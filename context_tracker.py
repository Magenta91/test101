"""
Enhanced Context Tracker Module for Document Processing

This module implements comprehensive context tracking with semantic filtering
that extracts only semantically relevant narrative or descriptive text from 
the original document about each field/value, preserving the original wording.

Key Features:
- Clause-level trimming for minimal relevant phrases
- Enhanced numeric handling with financial comparatives
- Stricter filtering with financial-specific anti-patterns
- Better document structure handling for bullet points
- Field normalization for improved matching
- Controlled recovery mechanisms to avoid noise
"""

import re
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict
import json
from fuzzywuzzy import fuzz

# Semantic similarity imports
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SEMANTIC_AVAILABLE = True
    print("Semantic filtering enabled with sentence-transformers")
except (ImportError, ModuleNotFoundError) as e:
    SEMANTIC_AVAILABLE = False
    print(f"Using enhanced fallback semantic filtering (sentence-transformers unavailable: {type(e).__name__})")

# Global model instance and caching for efficiency
_semantic_model = None
_embedding_cache = {}  # Cache for field embeddings
_sentence_cache = {}   # Cache for sentence embeddings (limited size)


def get_semantic_model():
    """Get or initialize the semantic similarity model"""
    global _semantic_model, SEMANTIC_AVAILABLE
    if _semantic_model is None and SEMANTIC_AVAILABLE:
        try:
            _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Loaded semantic model: all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Failed to load semantic model: {e}")
            SEMANTIC_AVAILABLE = False
    return _semantic_model


def extract_sentences_from_text(full_text: str) -> List[Tuple[str, int]]:
    """
    Extract discrete sentences with enhanced bullet handling and improved phrase preservation.
    
    Args:
        full_text: Complete document text as a single string
        
    Returns:
        List of tuples (sentence, original_index) with cleaned, original wording preserved
    """
    if not full_text:
        return []
    
    # Clean OCR artifacts first
    cleaned_text = clean_ocr_artifacts(full_text)
    
    # Enhanced bullet pattern to handle PDF special characters and headers
    bullet_pattern = r'(?:\s*[•†‡]\s*|\s*••\s*|\n{2,}|\n\s*(?:[•\-\*\+]|\d+[\.\)])\s+)'
    
    # Also split on section headers (all caps followed by newline)
    header_pattern = r'\n([A-Z\s]{3,}:?)\n'
    
    # First split on headers to isolate sections
    header_segments = re.split(header_pattern, cleaned_text)
    
    all_sentences = []
    segment_idx = 0
    
    for header_segment in header_segments:
        if not header_segment.strip():
            continue
            
        # Skip pure header text (all caps)
        if header_segment.isupper() and len(header_segment.split()) <= 5:
            continue
            
        # Split each header segment on bullet patterns
        bullet_segments = re.split(bullet_pattern, header_segment)
        
        for segment in bullet_segments:
            if not segment.strip():
                continue
                
            # Clean segment of artifacts
            segment = clean_segment_artifacts(segment)
            
            # Enhanced sentence splitting with fallback for phrases without punctuation
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', segment)
            
            # If no sentence breaks found within 50 chars, treat as single phrase
            if len(sentences) == 1 and len(segment) > 50:
                # Check if we can split on other delimiters while preserving phrases like "YoY"
                alt_sentences = re.split(r'(?<=[.!?;])\s+', segment)
                if len(alt_sentences) > 1:
                    sentences = alt_sentences
                else:
                    # Fallback: join lines to preserve full phrases
                    lines = segment.split('\n')
                    if len(lines) > 1:
                        # Join lines but preserve meaningful breaks
                        joined_lines = []
                        current_line = ""
                        for line in lines:
                            line = line.strip()
                            if line:
                                if current_line and not current_line.endswith(('.', '!', '?', ':')):
                                    current_line += " " + line
                                else:
                                    if current_line:
                                        joined_lines.append(current_line)
                                    current_line = line
                        if current_line:
                            joined_lines.append(current_line)
                        sentences = joined_lines
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # Clean up common artifacts and formatting
                sentence = re.sub(r'\s+', ' ', sentence)  # Normalize whitespace
                sentence = re.sub(r'^[•\-\*\+†‡]\s*', '', sentence)  # Remove leading bullets
                sentence = re.sub(r'^\d+[\.\)]\s*', '', sentence)  # Remove leading numbers
                sentence = re.sub(r'\s*\+\s*$', '', sentence)  # Remove trailing "+"
                sentence = re.sub(r'^\+\s*', '', sentence)  # Remove leading "+"
                
                # Preserve important abbreviations like "YoY" (don't let them become "Yo Y..")
                sentence = re.sub(r'\bYo\s+Y\b', 'YoY', sentence)
                sentence = re.sub(r'\bQ\s+o\s+Q\b', 'QoQ', sentence)
                sentence = re.sub(r'\bM\s+o\s+M\b', 'MoM', sentence)
                
                # Keep substantial sentences but allow shorter ones for bullet points
                if sentence and 10 <= len(sentence) <= 500:  # Increased max length
                    all_sentences.append((sentence, segment_idx))
                    segment_idx += 1
    
    return all_sentences


def clean_ocr_artifacts(text: str) -> str:
    """
    Clean common OCR artifacts from extracted PDF text with enhanced patterns.
    
    Args:
        text: Raw text from PDF extraction
        
    Returns:
        Cleaned text with artifacts removed
    """
    if not text:
        return text
    
    # Enhanced OCR artifacts and their replacements
    artifact_replacements = [
        (r'\?(?=\s|$)', ''),  # Remove standalone question marks (OCR errors)
        (r'([A-Za-z])\?([A-Za-z])', r'\1\2'),  # Remove ? between letters
        (r'([0-9])\?([0-9])', r'\1\2'),  # Remove ? between numbers
        (r'NPAT\?', 'NPAT'),  # Specific fix for "NPAT?"
        (r'EPS\?', 'EPS'),    # Specific fix for "EPS?"
        (r'([A-Z]+)\?(\s+of\s+)', r'\1\2'),  # Fix "METRIC? of VALUE"
        (r'per share\?\s+of', 'per share of'),  # Fix "per share? of"
        (r'(\w+)\?\s+(\w+)', r'\1 \2'),  # Remove ? between words
        (r'(\s+)\?(\s+of\s+)', r'\1\2'),  # Fix spacing with "of"
        (r'Tax\?\s+of', 'Tax of'),  # Fix "Tax? of"
        (r'profit\?\s+of', 'profit of'),  # Fix "profit? of"
        (r'[†‡]', '•'),  # Normalize special bullet characters to standard
        (r'••', '•'),     # Normalize double bullets
        (r'–', '-'),  # Normalize dashes
        (r'—', '-'),  # Normalize em-dashes
        (r'\s+', ' '),  # Normalize multiple spaces
    ]
    
    cleaned_text = text
    for pattern, replacement in artifact_replacements:
        cleaned_text = re.sub(pattern, replacement, cleaned_text)
    
    return cleaned_text


def clean_segment_artifacts(segment: str) -> str:
    """
    Clean artifacts specific to individual segments/bullets.
    
    Args:
        segment: Text segment to clean
        
    Returns:
        Cleaned segment
    """
    if not segment:
        return segment
    
    # Remove common segment artifacts
    segment = re.sub(r'\s*\+\s*(?=[A-Z])', '. ', segment)  # Replace " + " with ". " between sentences
    segment = re.sub(r'\s*\+\s*$', '', segment)  # Remove trailing "+"
    segment = re.sub(r'^\+\s*', '', segment)  # Remove leading "+"
    
    # Fix common OCR spacing issues
    segment = re.sub(r'([a-z])([A-Z])', r'\1 \2', segment)  # Add space between lowercase and uppercase
    segment = re.sub(r'(\d)([A-Z])', r'\1 \2', segment)  # Add space between digit and uppercase
    
    return segment.strip()


def get_enhanced_semantic_groups() -> Dict[str, List[str]]:
    """
    Get comprehensive semantic groups for field classification.
    
    Returns:
        Dictionary mapping semantic domains to related keywords
    """
    return {
        # Financial Performance
        'profit': ['profit', 'margin', 'earnings', 'net', 'income', 'profitability', 'surplus', 'gain', 'ebitda', 'operating'],
        'revenue': ['revenue', 'sales', 'turnover', 'income', 'receipts', 'collections', 'premium', 'billing', 'invoicing'],
        'growth': ['growth', 'increase', 'expansion', 'rise', 'improvement', 'gain', 'boost', 'surge', 'uptick'],
        'financial': ['financial', 'fiscal', 'monetary', 'economic', 'budget', 'cost', 'expense', 'capital', 'investment'],
        'performance': ['performance', 'results', 'outcome', 'achievement', 'success', 'metrics', 'indicators'],
        
        # Personal Information
        'age': ['age', 'born', 'years', 'birthday', 'birth', 'old', 'young', 'elderly', 'senior'],
        'name': ['name', 'called', 'known', 'person', 'individual', 'mr', 'ms', 'dr', 'sir', 'madam'],
        'citizenship': ['citizen', 'national', 'visa', 'status', 'nationality', 'passport', 'immigration', 'resident'],
        'blood': ['blood', 'group', 'type', 'medical', 'donor', 'health', 'emergency', 'transfusion', 'compatibility'],
        'address': ['address', 'location', 'residence', 'home', 'street', 'city', 'state', 'postal', 'zip'],
        'contact': ['contact', 'phone', 'email', 'telephone', 'mobile', 'communication', 'reach'],
        
        # Professional Information
        'company': ['company', 'corporation', 'firm', 'business', 'organization', 'enterprise', 'entity', 'establishment'],
        'job': ['job', 'position', 'role', 'work', 'employment', 'career', 'profession', 'occupation', 'title'],
        'technical': ['technical', 'technology', 'expertise', 'skills', 'engineering', 'development', 'programming', 'software'],
        'education': ['education', 'degree', 'university', 'college', 'school', 'qualification', 'certification', 'training'],
        'experience': ['experience', 'background', 'history', 'tenure', 'service', 'expertise', 'knowledge'],
        
        # Market and Business
        'market': ['market', 'industry', 'sector', 'segment', 'competition', 'share', 'position', 'landscape'],
        'operations': ['operations', 'operational', 'business', 'activities', 'processes', 'workflow', 'management'],
        'strategy': ['strategy', 'strategic', 'plan', 'planning', 'vision', 'mission', 'objectives', 'goals'],
        
        # CEO and Management Statements
        'statement': ['said', 'commented', 'stated', 'announced', 'declared', 'quote', 'ceo', 'managing director', 'chairman', 'executive']
    }


def is_relevant_sentence(field: str, sentence: str, value: str = "", 
                        semantic_groups: Dict[str, List[str]] = None,
                        anti_patterns: Dict[str, List[str]] = None,
                        model = None, threshold: float = 0.55, 
                        is_numeric_field: bool = False) -> Tuple[bool, float]:
    """
    Determine if a sentence is relevant to a field using comprehensive filtering with enhanced precision.
    
    Args:
        field: The field name
        sentence: The sentence to evaluate
        value: The field value (optional)
        semantic_groups: Dictionary of semantic keyword groups
        anti_patterns: Dictionary of anti-patterns to avoid
        model: Semantic similarity model (optional)
        threshold: Minimum semantic similarity threshold
        
    Returns:
        Tuple of (is_relevant, confidence_score)
    """
    if not sentence or not field:
        return False, 0.0
    
    sentence_lower = sentence.lower()
    field_lower = field.lower()
    
    # Initialize groups if not provided
    if semantic_groups is None:
        semantic_groups = get_enhanced_semantic_groups()
    if anti_patterns is None:
        anti_patterns = get_enhanced_anti_patterns()
    
    # STEP 1: Enhanced anti-pattern checking (immediate rejection)
    all_anti_patterns = []
    for pattern_category, patterns in anti_patterns.items():
        all_anti_patterns.extend(patterns)
    
    # Add field-specific anti-patterns
    field_anti_patterns = anti_patterns.get(field_lower, [])
    all_anti_patterns.extend(field_anti_patterns)
    
    # Check for anti-patterns
    for pattern in all_anti_patterns:
        if pattern in sentence_lower:
            return False, 0.0
    
    # STEP 2: Enhanced value matching with stricter requirements for text/alphanumeric values
    value_clean = str(value).strip().lower() if value else ""
    is_text_alphanum = bool(re.search(r'[A-Za-z]', value_clean))
    
    # For text/alphanumeric values like "1HFY23", "Life360, Inc.", require exact match or very high fuzzy
    if is_text_alphanum and value_clean:
        if value_clean in sentence_lower:
            # Exact match found - good
            pass
        else:
            # Check fuzzy match with very high threshold for text/alphanum
            fuzzy_ratio = fuzz.partial_ratio(value_clean, sentence_lower)
            if fuzzy_ratio < 90:  # Much stricter for text/alphanum values
                return False, 0.0
    
    # STEP 3: Disable recovery for problematic fields
    problematic_fields = ['period', 'company', 'name', 'technology_impact', 'performance_outcome']
    is_problematic_field = any(prob_field in field_lower for prob_field in problematic_fields)
    
    # STEP 4: Adjust threshold based on field type
    adjusted_threshold = threshold
    if not is_numeric_field or is_problematic_field:
        adjusted_threshold = 0.6  # Higher threshold for non-numeric and problematic fields
    
    # STEP 5: Length filter (reject overly long sentences)
    word_count = len(sentence.split())
    if word_count > 50:
        return False, 0.0
    
    # STEP 6: Detect unrelated domains (cross-domain filtering)
    matched_domains = []
    for domain, keywords in semantic_groups.items():
        if any(keyword in sentence_lower for keyword in keywords):
            matched_domains.append(domain)
    
    # Reject if sentence mentions multiple unrelated domains
    if len(matched_domains) > 1 and not is_numeric_field:
        field_related_domains = [domain for domain in matched_domains 
                               if field_lower in domain or domain in field_lower]
        if not field_related_domains:
            return False, 0.0
    elif len(matched_domains) > 2 and is_numeric_field:
        field_related_domains = [domain for domain in matched_domains 
                               if field_lower in domain or domain in field_lower]
        if not field_related_domains:
            return False, 0.0
    
    # STEP 7: Calculate relevance score
    relevance_score = 0.0
    
    # Direct value match (highest priority)
    if value_clean:
        if value_clean in sentence_lower:
            relevance_score += 0.4
        else:
            # For non-text/alphanum values, allow fuzzy matching
            if not is_text_alphanum:
                fuzzy_ratio = fuzz.partial_ratio(value_clean, sentence_lower)
                if fuzzy_ratio > 80:
                    relevance_score += (fuzzy_ratio / 100) * 0.3
    
    # Field name component matches
    field_clean = re.sub(r'[_-]', ' ', field_lower)
    field_words = [word for word in field_clean.split() if len(word) > 2]
    for field_word in field_words:
        if field_word in sentence_lower:
            relevance_score += 0.15
    
    # Semantic domain matches
    for domain in matched_domains:
        if field_lower in domain or domain in field_lower:
            relevance_score += 0.2
            break
    
    # STEP 8: Semantic similarity (if model available)
    semantic_score = 0.0
    if model is not None and SEMANTIC_AVAILABLE:
        try:
            # Use cached embeddings for efficiency
            field_key = field_lower
            if field_key not in _embedding_cache:
                _embedding_cache[field_key] = model.encode(field, convert_to_tensor=True)
            
            sentence_key = sentence[:100].lower()
            if sentence_key not in _sentence_cache:
                if len(_sentence_cache) > 1000:
                    oldest_key = next(iter(_sentence_cache))
                    del _sentence_cache[oldest_key]
                _sentence_cache[sentence_key] = model.encode(sentence, convert_to_tensor=True)
            
            field_emb = _embedding_cache[field_key]
            sent_emb = _sentence_cache[sentence_key]
            semantic_score = util.cos_sim(field_emb, sent_emb).item()
            
        except Exception as e:
            print(f"Semantic similarity computation failed: {e}")
            semantic_score = 0.0
    
    # STEP 9: Final relevance calculation with adjusted threshold
    final_score = relevance_score + (semantic_score * 0.3)
    
    # Apply adjusted threshold
    is_relevant = final_score >= adjusted_threshold or semantic_score >= adjusted_threshold
    
    return is_relevant, final_score


def get_enhanced_anti_patterns() -> Dict[str, List[str]]:
    """
    Get comprehensive anti-patterns to filter out irrelevant contexts.
    
    Returns:
        Dictionary mapping field types to phrases that should be excluded
    """
    return {
        # Financial anti-patterns
        'profit': ['profit-sharing scheme', 'profit pool notional', 'profit margin error', 'non-profit'],
        'revenue': ['revenue recognition policy', 'revenue accounting standard', 'revenue stream definition'],
        'growth': ['hair growth', 'plant growth', 'tumor growth', 'population growth', 'personal growth'],
        
        # Personal anti-patterns
        'blood': ['blood money', 'blood red', 'blood diamond', 'blood sport', 'blood relation', 'bloodline'],
        'age': ['company age', 'market age', 'system age', 'platform age', 'golden age', 'stone age'],
        'citizenship': ['citizenship ceremony', 'citizenship test', 'citizenship course'],
        
        # Professional anti-patterns
        'company': ['company policy', 'company handbook', 'company culture', 'company values'],
        'technical': ['technical difficulties', 'technical support', 'technical issues', 'technical manual'],
        'education': ['education system', 'education policy', 'education reform', 'education sector'],
        
        # Generic anti-patterns
        'generic': ['operates globally', 'industry standard', 'market conditions', 'economic environment']
    }


def get_enhanced_anti_patterns() -> Dict[str, List[str]]:
    """
    Get comprehensive anti-patterns to filter out irrelevant contexts, especially financial commentary.
    
    Returns:
        Dictionary mapping field types to phrases that should be excluded
    """
    return {
        # Financial false positives
        'profit': ['profit-sharing scheme', 'profit pool notional', 'profit center', 'profit motive'],
        'revenue': ['revenue recognition', 'revenue model', 'revenue stream'],
        'growth': ['hair growth', 'plant growth', 'tumor growth', 'population growth'],
        
        # Personal false positives
        'blood': ['blood money', 'blood red', 'blood relation', 'blood sport', 'blood flow'],
        'age': ['company age', 'market age', 'platform age', 'stone age', 'golden age'],
        'citizenship': ['citizenship ceremony', 'citizenship test', 'citizenship program'],
        
        # Professional false positives
        'company': ['company car', 'company policy', 'company culture'],
        'technical': ['technical difficulties', 'technical support', 'technical issues'],
        'market': ['farmers market', 'flea market', 'black market', 'stock market'],
        
        # Financial commentary anti-patterns (ENHANCED)
        'commentary': [
            'said', 'commented', 'noted', 'stated', 'announced', 'declared',
            'momentum continuing', 'performed strongly', 'upgraded the outlook',
            'outlook remains', 'expects to', 'anticipates', 'forecasts',
            'management believes', 'we are confident', 'looking forward',
            'continuing into', 'second half', 'full year', 'going forward',
            'pleased to announce', 'excited about', 'committed to',
            'driven by', 'these increases', 'continue to grow', 'healthy expansion',
            'increases were driven by', 'organic and bolt-on', 'acquisition growth',
            'capital management', 'leverage ratio of', 'at 31 december'
        ],
        
        # CEO and management quotes
        'quotes': [
            'ceo said', 'chief executive', 'managing director said',
            'chairman commented', 'according to', 'as stated by',
            'in his remarks', 'during the call', 'in the presentation'
        ],
        
        # Generic business language
        'business_generic': [
            'operates globally', 'maintains workforce', 'company overview',
            'general information', 'business strategy', 'strategic initiatives',
            'operational excellence', 'market leadership', 'industry trends',
            'competitive landscape', 'market conditions', 'economic environment'
        ],
        
        # Footnote and reference patterns
        'references': [
            'see footnote', 'refer to note', 'as detailed in',
            'further information', 'additional details', 'more information',
            'please refer', 'see appendix', 'see table', 'see chart'
        ]
    }





def determine_adaptive_threshold(field: str, value: str) -> float:
    """
    Determine adaptive confidence threshold based on field/value characteristics.
    
    Args:
        field: The field name
        value: The field value
        
    Returns:
        Adaptive threshold (0.35 for short/numeric, 0.6 for long text)
    """
    if not value:
        return 0.5  # Default threshold
    
    value_str = str(value).strip()
    
    # Check if value is numeric, short, or code-like
    is_numeric = bool(re.match(r'^[\d.,\s$%+-]+$', value_str))
    is_short = len(value_str) <= 10
    is_code_like = bool(re.match(r'^[A-Z0-9+\-]{1,5}$', value_str))  # Like "O+", "A1", "USD"
    is_date_like = bool(re.search(r'\d{4}|\d{1,2}/\d{1,2}', value_str))
    
    # Lower threshold for numeric, short, or code-like values
    if is_numeric or is_short or is_code_like or is_date_like:
        return 0.25  # More lenient for short/code values
    
    # Moderate threshold for long text values
    return 0.45  # More lenient for text values


def compute_semantic_similarity(field: str, sentence: str, similarity_threshold: float = 0.55) -> float:
    """
    Compute semantic similarity between field and sentence using embeddings.
    
    Args:
        field: The field name to compare
        sentence: The sentence to compare
        similarity_threshold: Minimum similarity threshold
        
    Returns:
        Similarity score (0.0 to 1.0), or 0.0 if semantic analysis unavailable
    """
    if not SEMANTIC_AVAILABLE or not field or not sentence:
        return 0.0
    
    try:
        model = get_semantic_model()
        if model is None:
            return 0.0
        
        # Use cache for field embeddings to improve performance
        field_key = field.lower().strip()
        if field_key not in _embedding_cache:
            _embedding_cache[field_key] = model.encode(field, convert_to_tensor=True)
        
        field_embedding = _embedding_cache[field_key]
        
        # Cache sentence embeddings with size limit
        sentence_key = sentence[:100].lower().strip()  # Use first 100 chars as key
        if sentence_key not in _sentence_cache:
            # Limit cache size to prevent memory issues
            if len(_sentence_cache) > 1000:
                # Remove oldest entries (simple FIFO)
                oldest_key = next(iter(_sentence_cache))
                del _sentence_cache[oldest_key]
            _sentence_cache[sentence_key] = model.encode(sentence, convert_to_tensor=True)
        
        sentence_embedding = _sentence_cache[sentence_key]
        
        # Compute cosine similarity
        similarity = util.cos_sim(field_embedding, sentence_embedding).item()
        return similarity
        
    except Exception as e:
        print(f"Semantic similarity computation failed: {e}")
        return 0.0


def calculate_keyword_proximity(field_words: List[str], value_terms: List[str], sentence: str) -> float:
    """
    Calculate proximity score based on how close field keywords and value terms appear in the sentence.
    
    Args:
        field_words: List of field-related keywords
        value_terms: List of value-related terms
        sentence: The sentence to analyze
        
    Returns:
        Proximity score (0.0 to 1.0), higher means closer proximity
    """
    if not field_words or not value_terms or not sentence:
        return 0.0
    
    sentence_lower = sentence.lower()
    words = sentence_lower.split()
    
    # Find positions of field words and value terms
    field_positions = []
    value_positions = []
    
    for i, word in enumerate(words):
        for field_word in field_words:
            if field_word in word:
                field_positions.append(i)
        for value_term in value_terms:
            if value_term.lower() in word:
                value_positions.append(i)
    
    if not field_positions or not value_positions:
        return 0.0
    
    # Calculate minimum distance between any field word and any value term
    min_distance = float('inf')
    for field_pos in field_positions:
        for value_pos in value_positions:
            distance = abs(field_pos - value_pos)
            min_distance = min(min_distance, distance)
    
    # Convert distance to proximity score (closer = higher score)
    if min_distance == 0:
        return 1.0  # Same word contains both field and value
    elif min_distance <= 3:
        return 0.8  # Very close
    elif min_distance <= 6:
        return 0.6  # Moderately close
    elif min_distance <= 10:
        return 0.4  # Somewhat close
    else:
        return 0.2  # Far apart


def detect_multi_domain_sentence(sentence: str, semantic_groups: Dict[str, List[str]]) -> Tuple[int, List[str]]:
    """
    Detect how many semantic domains a sentence mentions.
    
    Args:
        sentence: The sentence to analyze
        semantic_groups: Dictionary of semantic keyword groups
        
    Returns:
        Tuple of (num_domains, list_of_detected_domains)
    """
    sentence_lower = sentence.lower()
    detected_domains = []
    
    # Check each semantic group
    for domain, keywords in semantic_groups.items():
        domain_matches = 0
        for keyword in keywords:
            if keyword in sentence_lower:
                domain_matches += 1
        
        # If domain has keyword matches, consider it present
        if domain_matches >= 1:
            detected_domains.append(domain)
    
    return len(detected_domains), detected_domains


def is_sentence_relevant_to_field(field: str, sentence: str, value: str = "", 
                                 semantic_groups: Dict[str, List[str]] = None,
                                 anti_patterns: Dict[str, List[str]] = None,
                                 threshold: float = 0.55,
                                 use_adaptive_threshold: bool = True) -> Tuple[bool, float]:
    """
    Enhanced function to determine if a sentence is semantically relevant to a specific field.
    
    Args:
        field: The field name
        sentence: The sentence to evaluate
        value: The field value (optional)
        semantic_groups: Dictionary of semantic keyword groups
        anti_patterns: Dictionary of anti-patterns to avoid
        threshold: Minimum relevance threshold
        use_adaptive_threshold: Whether to use adaptive thresholds based on value type
        
    Returns:
        Tuple of (is_relevant, confidence_score)
    """
    if not field or not sentence:
        return False, 0.0
    
    # Initialize default groups if not provided
    if semantic_groups is None:
        semantic_groups = {}
    if anti_patterns is None:
        anti_patterns = {}
    
    field_lower = field.lower()
    sentence_lower = sentence.lower()
    
    # Clean field name for keyword extraction
    field_clean = re.sub(r'[_-]', ' ', field_lower)
    field_words = [word for word in field_clean.split() if len(word) > 2]
    
    # Extract value terms
    value_terms = []
    if value:
        value_clean = str(value).strip()
        # For numeric values, extract the number
        numeric_matches = re.findall(r'\d+\.?\d*', value_clean)
        value_terms.extend(numeric_matches)
        # For text values, extract significant words
        text_words = re.findall(r'\b[A-Za-z]{3,}\b', value_clean)
        value_terms.extend(text_words)
        if len(value_clean) > 2:
            value_terms.append(value_clean)
    
    # STEP 1: Check anti-patterns (immediate rejection)
    for pattern_type, patterns in anti_patterns.items():
        if any(fw in pattern_type for fw in field_words):
            for pattern in patterns:
                if pattern in sentence_lower:
                    return False, 0.0  # Immediate rejection
    
    # STEP 2: Detect multi-domain sentences and apply proportional confidence reduction
    num_domains, detected_domains = detect_multi_domain_sentence(sentence, semantic_groups)
    if num_domains > 1:
        # Apply proportional confidence reduction instead of penalty
        domain_reduction_factor = 1.0 / num_domains
    else:
        domain_reduction_factor = 1.0
    
    # STEP 3: Check sentence length (reject overly long sentences)
    word_count = len(sentence.split())
    if word_count > 40:
        return False, 0.0  # Too long, likely not focused
    elif word_count < 5:
        return False, 0.0  # Too short, likely not informative
    
    # STEP 4: Calculate relevance score
    relevance_score = 0.0
    
    # Direct field word matches (high weight)
    direct_matches = 0
    for field_word in field_words:
        if field_word in sentence_lower:
            relevance_score += 0.25
            direct_matches += 1
    
    # Value term matches (high weight)
    value_matches = 0
    for term in value_terms:
        if len(term) > 2 and term.lower() in sentence_lower:
            relevance_score += 0.2
            value_matches += 1
    
    # Semantic group matches (medium weight)
    matched_groups = []
    for group_key, keywords in semantic_groups.items():
        field_relates_to_group = any(fw in group_key or group_key in fw for fw in field_words)
        
        if field_relates_to_group:
            group_matches = 0
            for keyword in keywords:
                if keyword in sentence_lower:
                    group_matches += 1
            
            if group_matches > 0:
                group_score = min(0.3, group_matches * 0.1)
                relevance_score += group_score
                matched_groups.append(group_key)
    
    # STEP 5: Proximity scoring (bonus for close keywords)
    if field_words and value_terms:
        proximity_score = calculate_keyword_proximity(field_words, value_terms, sentence)
        relevance_score += proximity_score * 0.2  # Up to 0.2 bonus
    
    # STEP 6: Semantic similarity (if available)
    if SEMANTIC_AVAILABLE:
        semantic_score = compute_semantic_similarity(field, sentence, threshold)
        relevance_score += semantic_score * 0.3  # Up to 0.3 from embeddings
    
    # STEP 7: Apply domain reduction factor
    relevance_score *= domain_reduction_factor
    
    # STEP 8: Bonus for high-confidence matches
    if direct_matches > 0 and value_matches > 0:
        relevance_score += 0.1  # Bonus for both field and value matches
    
    # Normalize score to 0-1 range
    final_score = min(1.0, max(0.0, relevance_score))
    
    # STEP 9: Apply adaptive threshold
    if use_adaptive_threshold:
        adaptive_threshold = determine_adaptive_threshold(field, value)
    else:
        adaptive_threshold = threshold
    
    # Apply threshold
    is_relevant = final_score >= adaptive_threshold
    
    return is_relevant, final_score


def weak_context_recovery(field: str, value: str, sentences_with_indices: List[Tuple[str, int]], 
                         max_sentences: int = 2) -> List[Tuple[str, int, float]]:
    """
    Stricter context recovery for fields with empty context - only exact value matches.
    
    Args:
        field: The field name
        value: The field value
        sentences_with_indices: List of (sentence, index) tuples
        max_sentences: Maximum number of sentences to recover (reduced to 2)
        
    Returns:
        List of (sentence, index, confidence) tuples for recovered context
    """
    if not value or not sentences_with_indices:
        return []
    
    value_clean = str(value).strip().lower()
    
    # Only proceed if value is substantial enough
    if len(value_clean) < 3:
        return []
    
    recovery_candidates = []
    
    for sentence, idx in sentences_with_indices:
        sentence_lower = sentence.lower()
        recovery_score = 0.0
        
        # STRICT: Only recover if exact value match is found
        if value_clean in sentence_lower:
            recovery_score = 0.5  # Base score for exact match
            
            # Bonus for shorter sentences (prefer focused content)
            if len(sentence) < 100:
                recovery_score += 0.2
            
            # Bonus for numeric patterns in financial contexts
            if re.search(r'[\d,\.]+\s*(?:mn|bn|%|million|billion)', sentence_lower):
                recovery_score += 0.1
            
            recovery_candidates.append((sentence, idx, recovery_score))
    
    # Sort by score and return top candidates, preferring shorter sentences
    recovery_candidates.sort(key=lambda x: (x[2], -len(x[0])), reverse=True)
    return recovery_candidates[:max_sentences]


def fallback_semantic_filter(field: str, sentence: str, similarity_threshold: float = 0.55) -> bool:
    """
    Enhanced fallback semantic filtering using keyword proximity and context analysis.
    Used when sentence-transformers is not available.
    
    Args:
        field: The field name
        sentence: The sentence to evaluate
        similarity_threshold: Threshold (converted to keyword-based scoring)
        
    Returns:
        True if sentence is semantically relevant to field
    """
    if not field or not sentence:
        return False
    
    field_lower = field.lower()
    sentence_lower = sentence.lower()
    
    # Clean field name for keyword extraction
    field_clean = re.sub(r'[_-]', ' ', field_lower)
    field_words = [word for word in field_clean.split() if len(word) > 2]
    
    # Comprehensive semantic keyword groups with domain-specific coverage
    semantic_groups = {
        # Personal Information
        'name': ['name', 'called', 'known', 'person', 'individual', 'mr', 'ms', 'dr', 'sir', 'madam', 'titled', 'named'],
        'age': ['age', 'years', 'old', 'born', 'birth', 'date', 'birthday', 'anniversary', 'young', 'elder', 'senior'],
        'gender': ['gender', 'male', 'female', 'man', 'woman', 'he', 'she', 'his', 'her', 'him'],
        'address': ['address', 'residence', 'home', 'street', 'city', 'state', 'country', 'postal', 'zip', 'location', 'based', 'located'],
        'phone': ['phone', 'mobile', 'telephone', 'contact', 'number', 'call', 'reach', 'dial'],
        'email': ['email', 'mail', 'contact', 'address', 'communication', 'correspondence'],
        
        # Medical Information  
        'blood': ['blood', 'type', 'group', 'medical', 'health', 'emergency', 'contact', 'recorded', 'files', 'donor', 'recipient'],
        'medical': ['medical', 'health', 'condition', 'diagnosis', 'treatment', 'doctor', 'hospital', 'clinic', 'patient'],
        'allergy': ['allergy', 'allergic', 'reaction', 'sensitive', 'intolerant', 'adverse'],
        
        # Legal/Citizenship
        'citizenship': ['citizen', 'national', 'nationality', 'country', 'passport', 'visa', 'immigration', 'status', 'resident', 'naturalized'],
        'legal': ['legal', 'law', 'court', 'judge', 'attorney', 'lawyer', 'case', 'litigation', 'contract'],
        'id': ['id', 'identification', 'license', 'card', 'document', 'certificate', 'permit'],
        
        # Professional Information
        'company': ['company', 'corporation', 'firm', 'business', 'organization', 'inc', 'corp', 'ltd', 'llc', 'enterprise', 'technology', 'based', 'headquarters', 'founded'],
        'job': ['job', 'position', 'role', 'title', 'work', 'employment', 'career', 'profession', 'occupation'],
        'ceo': ['ceo', 'chief', 'executive', 'officer', 'president', 'director', 'leader', 'head', 'chairman', 'founder'],
        'salary': ['salary', 'wage', 'compensation', 'pay', 'income', 'earnings', 'remuneration'],
        'experience': ['experience', 'years', 'worked', 'employed', 'served', 'tenure', 'background'],
        
        # Financial Information
        'revenue': ['revenue', 'income', 'earnings', 'sales', 'financial', 'money', 'million', 'billion', 'profit', 'quarterly', 'reported'],
        'growth': ['growth', 'increase', 'rise', 'gain', 'improvement', 'expansion', 'percent', '%', 'rate'],
        'market': ['market', 'share', 'position', 'segment', 'industry', 'sector', 'competition', 'capitalization'],
        'stock': ['stock', 'share', 'symbol', 'ticker', 'nasdaq', 'nyse', 'exchange', 'trading', 'listed', 'trades', 'price'],
        'investment': ['investment', 'investor', 'funding', 'capital', 'equity', 'debt', 'financing'],
        
        # Technical Information
        'technical': ['technical', 'technology', 'expertise', 'skills', 'experience', 'development', 'engineering', 'analytics', 'programming'],
        'expertise': ['expertise', 'experience', 'skills', 'knowledge', 'specialization', 'proficiency', 'competency', 'qualified'],
        'platform': ['platform', 'service', 'system', 'application', 'software', 'technology', 'digital', 'cloud', 'infrastructure'],
        'user': ['user', 'customer', 'client', 'subscriber', 'member', 'active', 'base', 'demographics', 'audience'],
        
        # Educational Information
        'education': ['education', 'school', 'university', 'college', 'degree', 'diploma', 'certificate', 'graduated', 'studied'],
        'qualification': ['qualification', 'certified', 'licensed', 'accredited', 'trained', 'skilled'],
        
        # Geographic Information
        'location': ['location', 'place', 'region', 'area', 'zone', 'territory', 'geographic', 'situated'],
        'country': ['country', 'nation', 'state', 'province', 'territory', 'region', 'jurisdiction']
    }
    
    # Calculate relevance score with improved logic
    relevance_score = 0.0
    matched_groups = []
    
    # Direct field word matches (high weight)
    direct_matches = 0
    for field_word in field_words:
        if field_word in sentence_lower:
            relevance_score += 0.25
            direct_matches += 1
    
    # Semantic group matches (medium weight) - more sophisticated matching
    for group_key, keywords in semantic_groups.items():
        # Check if field relates to this semantic group
        field_relates_to_group = any(fw in group_key or group_key in fw for fw in field_words)
        
        if field_relates_to_group:
            group_matches = 0
            for keyword in keywords:
                if keyword in sentence_lower:
                    group_matches += 1
            
            if group_matches > 0:
                # Weight by number of matches and group relevance
                group_score = min(0.3, group_matches * 0.1)
                relevance_score += group_score
                matched_groups.append(group_key)
    
    # Context structure analysis (medium weight)
    structure_indicators = [
        ('is', 0.1), ('was', 0.1), ('has', 0.1), ('have', 0.1),
        ('reported', 0.15), ('announced', 0.15), ('stated', 0.15),
        ('mentioned', 0.1), ('noted', 0.1), ('recorded', 0.1)
    ]
    
    for indicator, weight in structure_indicators:
        if indicator in sentence_lower:
            relevance_score += weight
            break
    
    # Comprehensive anti-patterns to filter out metaphorical, idiomatic, or irrelevant contexts
    anti_patterns = {
        # Age-related false positives
        'age': ['company\'s age', 'market age', 'platform age', 'system age', 'age of technology', 'golden age', 'stone age', 'ice age', 'age group', 'average age'],
        
        # Blood-related false positives  
        'blood': ['blood flow', 'blood money', 'blood red', 'blood sport', 'blood pressure', 'bloodline', 'blood relation', 'blood diamond', 'blood orange', 'bad blood', 'blood bank', 'blood test'],
        
        # Platform-related false positives
        'platform': ['oil platform', 'train platform', 'political platform', 'drilling platform', 'station platform'],
        
        # Company name false positives
        'apple': ['apple orchard', 'apple fruit', 'apple juice', 'apple tree', 'ate an apple', 'fresh apple', 'apple pie', 'apple sauce'],
        'amazon': ['amazon river', 'amazon rainforest', 'amazon jungle', 'amazon basin'],
        'oracle': ['oracle database', 'ancient oracle', 'oracle bones'],
        
        # Technical false positives
        'technical': ['technical difficulties', 'technical support', 'technical issues'],
        'experience': ['experience shows', 'experience suggests', 'bad experience', 'user experience'],
        
        # Financial false positives
        'growth': ['hair growth', 'plant growth', 'tumor growth', 'population growth'],
        'market': ['stock market', 'farmers market', 'flea market', 'black market'],
        'capital': ['capital city', 'capital letter', 'capital punishment'],
        
        # Personal info false positives
        'address': ['address the issue', 'address the problem', 'keynote address', 'public address'],
        'contact': ['eye contact', 'physical contact', 'contact sport', 'contact lens'],
        'position': ['sitting position', 'geographic position', 'yoga position'],
        
        # Medical false positives
        'medical': ['medical drama', 'medical show', 'medical emergency'],
        'health': ['health insurance', 'public health', 'health department'],
        
        # Legal false positives
        'legal': ['legal age', 'legal document', 'legal system', 'legal advice'],
        'case': ['brief case', 'suit case', 'phone case', 'worst case'],
        
        # Multi-domain sentences (containing multiple semantic fields)
        'multi_domain': ['born in', 'blood group', 'citizenship status', 'technical expertise', 'medical condition', 'legal status']
    }
    
    for field_type, patterns in anti_patterns.items():
        if any(ft in field_type for ft in field_words):
            for pattern in patterns:
                if pattern in sentence_lower:
                    relevance_score -= 0.3  # Significant penalty
                    break
    
    # Boost score for high-confidence matches
    if direct_matches > 0 and len(matched_groups) > 0:
        relevance_score += 0.1  # Bonus for both direct and semantic matches
    
    # Convert threshold to keyword-based scoring
    # More lenient than pure embedding similarity but still filtered
    keyword_threshold = similarity_threshold * 0.7  # 0.55 -> ~0.385
    
    # Debug information
    if relevance_score > 0:
        print(f"    Fallback semantic: field='{field}', score={relevance_score:.3f}, threshold={keyword_threshold:.3f}, groups={matched_groups}")
    
    return relevance_score >= keyword_threshold


def is_numeric_value(value: str) -> bool:
    """
    Detect if a value is predominantly numeric or currency-like.
    
    Args:
        value: The field value to check
        
    Returns:
        True if the value is numeric/currency, False otherwise
    """
    if not value:
        return False
    
    value_str = str(value).strip()
    
    # Enhanced regex patterns for numeric detection
    patterns = [
        r'[\d,\.]+\s*(?:mn|bn|m|b|%|million|billion|cents|dollars?)',  # Numbers with units
        r'(?:aud|usd|gbp|eur|\$)\s*[\d,\.]+',  # Currency prefixed numbers
        r'[\d,\.]+\s*(?:increase|decrease|up|down)',  # Numbers with change indicators
        r'^\d+\.?\d*$',  # Pure numbers
        r'[\d,\.]+\s*to\s*[\d,\.]+',  # Ranges
        r'[\d,\.]+\s*(?:basis\s*points|bps)',  # Basis points
    ]
    
    value_lower = value_str.lower()
    
    # Check if any pattern matches
    for pattern in patterns:
        if re.search(pattern, value_lower):
            return True
    
    # Fallback: check if significant portion is numeric
    numeric_chars = len(re.findall(r'[\d,\.]', value_str))
    total_chars = len(value_str.replace(' ', ''))
    
    return numeric_chars / total_chars > 0.4 if total_chars > 0 else False


def extract_numeric_context_window(value: str, full_text: str, window_size: int = 30) -> List[Tuple[str, float]]:
    """
    Extract local text windows around numeric values in the document.
    
    Args:
        value: The numeric value to find
        full_text: Complete document text
        window_size: Characters to extract on each side of the match
        
    Returns:
        List of (context_text, confidence_score) tuples
    """
    contexts = []
    
    # Normalize the value for matching
    normalized_value = str(value).strip()
    
    # Create multiple search patterns for the numeric value
    patterns = []
    
    # Extract core numeric part
    numeric_match = re.search(r'[\d,\.]+', normalized_value)
    if numeric_match:
        core_number = numeric_match.group()
        
        # Pattern 1: Exact match with units
        patterns.append(re.escape(normalized_value))
        
        # Pattern 2: Core number with flexible units
        unit_pattern = r'[\s]*(?:mn|bn|m|b|%|million|billion|cents|dollars?|aud|usd|gbp|eur)?'
        patterns.append(re.escape(core_number) + unit_pattern)
        
        # Pattern 3: Number with currency prefix
        patterns.append(r'(?:aud|usd|gbp|eur)?\s*' + re.escape(core_number) + unit_pattern)
    
    # Search for each pattern in the text
    for pattern in patterns:
        for match in re.finditer(pattern, full_text, re.IGNORECASE):
            start_pos = max(0, match.start() - window_size)
            end_pos = min(len(full_text), match.end() + window_size)
            
            # Expand to sentence boundaries
            context_window = full_text[start_pos:end_pos]
            
            # Find better boundaries (punctuation or newlines)
            # Expand left to find sentence start
            left_boundary = start_pos
            for i in range(start_pos, max(0, start_pos - 50), -1):
                if full_text[i] in '.;,\n':
                    left_boundary = i + 1
                    break
            
            # Expand right to find sentence end
            right_boundary = end_pos
            for i in range(end_pos, min(len(full_text), end_pos + 50)):
                if full_text[i] in '.;,\n':
                    right_boundary = i
                    break
            
            # Extract the final context
            final_context = full_text[left_boundary:right_boundary].strip()
            
            if final_context and len(final_context) > 10:
                # Calculate confidence based on match precision
                confidence = 0.8 if pattern == re.escape(normalized_value) else 0.6
                contexts.append((final_context, confidence))
    
    # Remove duplicates and sort by confidence
    unique_contexts = []
    seen_contexts = set()
    
    for context, conf in sorted(contexts, key=lambda x: x[1], reverse=True):
        context_key = context.lower().strip()
        if context_key not in seen_contexts:
            seen_contexts.add(context_key)
            unique_contexts.append((context, conf))
    
    return unique_contexts[:3]  # Return top 3 matches


def normalize_field_name(field: str) -> str:
    """
    Normalize field names for better matching by removing underscores, periods, etc.
    
    Args:
        field: Original field name
        
    Returns:
        Normalized field name
    """
    if not field:
        return ""
    
    # Remove underscores, periods, and convert to lowercase
    normalized = re.sub(r'[_\.\-]', ' ', field.lower())
    
    # Remove common suffixes that don't add semantic value
    normalized = re.sub(r'\s+(1hfy23|1hfy22|fy23|fy22|current|previous|amount|percentage)$', '', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def split_into_clauses(sentence: str) -> List[str]:
    """
    Split a sentence into clauses while preserving financial comparative units.
    
    Args:
        sentence: The sentence to split
        
    Returns:
        List of clauses with parentheticals preserved as atomic units
    """
    if not sentence:
        return []
    
    # First, protect parenthetical expressions by replacing them with placeholders
    parenthetical_map = {}
    placeholder_counter = 0
    
    # Find and replace parentheticals with placeholders
    def replace_parenthetical(match):
        nonlocal placeholder_counter
        placeholder = f"__PAREN_{placeholder_counter}__"
        parenthetical_map[placeholder] = match.group(0)
        placeholder_counter += 1
        return placeholder
    
    # Protect parentheticals (especially financial comparatives)
    protected_sentence = re.sub(r'\([^)]*\)', replace_parenthetical, sentence)
    
    # Split on clause separators, but be more conservative
    clause_patterns = [
        r';\s+',        # Semicolon - strong separator
        r'\s+(?:while|whereas|however|although|though)\s+',  # Strong conjunctions only
        r',\s+(?=(?:and|but|or)\s)',  # Comma before coordinating conjunctions
    ]
    
    clauses = [protected_sentence]
    
    # Apply patterns more conservatively
    for pattern in clause_patterns:
        new_clauses = []
        for clause in clauses:
            if len(clause.strip()) > 20:  # Only split longer clauses
                parts = re.split(pattern, clause)
                new_clauses.extend([part.strip() for part in parts if part.strip()])
            else:
                new_clauses.append(clause)
        clauses = new_clauses
    
    # Restore parentheticals
    final_clauses = []
    for clause in clauses:
        for placeholder, original in parenthetical_map.items():
            clause = clause.replace(placeholder, original)
        if len(clause.strip()) > 10:  # Minimum meaningful length
            final_clauses.append(clause.strip())
    
    return final_clauses if final_clauses else [sentence]


def find_minimal_relevant_clause(clauses: List[str], field: str, value: str) -> Tuple[str, float]:
    """
    Find the minimal clause with enhanced metric phrase extraction and expansion.
    
    Args:
        clauses: List of clauses to evaluate
        field: Field name
        value: Field value
        
    Returns:
        Tuple of (best_clause, confidence_score)
    """
    if not clauses or not value:
        return "", 0.0
    
    normalized_field = normalize_field_name(field)
    value_clean = str(value).strip().lower()
    
    # Extract core numeric value for pattern matching
    core_number = re.search(r'[\d,\.]+', value_clean)
    core_num = core_number.group() if core_number else ""
    
    # Enhanced regex patterns to capture complete financial statements
    enhanced_patterns = [
        # Full EPS patterns with comparatives
        rf'([\w\s]+earnings per share\s+of\s+{re.escape(core_num) if core_num else r"[\d,\.]+"}\s*cents?\s*per share\s*\([^)]+\))',
        rf'([\w\s]*earnings per share\s+{re.escape(core_num) if core_num else r"[\d,\.]+"}\s*cents?\s*\([^)]+\))',
        # NPAT patterns
        rf'([\w\s]+(?:npat|profit)\s+of\s+(?:aud|usd|\$)?\s*{re.escape(core_num) if core_num else r"[\d,\.]+"}\s*(?:mn|million)?\s*\([^)]+\))',
        # General metric patterns
        rf'([\w\s]+(?:margin|dividend|revenue)\s+of\s+{re.escape(core_num) if core_num else r"[\d,\.]+"}\s*[%]?\s*\([^)]+\))'
    ] if core_num else []
    
    clause_scores = []
    
    for i, clause in enumerate(clauses):
        clause_lower = clause.lower()
        score = 0.0
        
        # First, try to match enhanced financial patterns
        pattern_matched = False
        for pattern in enhanced_patterns:
            if re.search(pattern, clause_lower, re.IGNORECASE):
                score += 2.0  # Very high score for complete patterns
                pattern_matched = True
                break
        
        # CRITICAL: Must contain both field-related terms AND value
        has_field_match = False
        has_value_match = False
        
        # Check for field match with financial metrics
        financial_metrics = [
            'underlying earnings per share', 'reported earnings per share', 'basic earnings per share',
            'underlying npat', 'reported npat', 'npat', 'pre-tax profit', 'profit', 
            'earnings', 'revenue', 'ebit margin', 'margin', 'dividend', 'guidance'
        ]
        
        field_words = normalized_field.split()
        for field_word in field_words:
            if len(field_word) > 2 and field_word in clause_lower:
                has_field_match = True
                score += 0.3
        
        # Check for financial metric keywords
        for metric in financial_metrics:
            if metric in clause_lower:
                # Check if this metric relates to the field
                if any(fw in metric for fw in field_words) or any(mw in normalized_field for mw in metric.split()):
                    has_field_match = True
                    score += 0.5
                    break
        
        # Check for value match
        if value_clean in clause_lower:
            has_value_match = True
            score += 1.0
        elif core_num and core_num in clause_lower:
            has_value_match = True
            score += 0.8
        
        # Enhanced expansion logic: if value found but field missing, look for expansion
        expansion_text = ""
        if has_value_match and not has_field_match:
            # Look in preceding clauses for field terms (up to 10 words before)
            words_collected = 0
            
            for j in range(i - 1, -1, -1):
                if j < 0:
                    break
                prev_clause = clauses[j]
                prev_words = prev_clause.split()
                
                # Check if previous clause has field terms
                prev_has_field = any(fw in prev_clause.lower() for fw in field_words)
                if prev_has_field:
                    # Include up to 10 words from this clause
                    words_to_take = min(10 - words_collected, len(prev_words))
                    expansion_words = prev_words[-words_to_take:] if words_to_take < len(prev_words) else prev_words
                    expansion_text = " ".join(expansion_words) + " " + expansion_text
                    has_field_match = True
                    score += 0.4  # Bonus for successful expansion
                    break
                
                # Collect words for potential expansion
                expansion_text = prev_clause + " " + expansion_text
                words_collected += len(prev_words)
                
                if words_collected > 20:  # Don't look too far back
                    break
        
        # Only consider clauses that have BOTH field and value matches
        if not (has_field_match and has_value_match):
            continue
        
        # Bonus for complete financial statements (with comparatives)
        if re.search(r'\([^)]*(?:1hfy\d+|fy\d+|20\d+)[^)]*\)', clause_lower):
            score += 0.4
        
        # Bonus for currency patterns
        if re.search(r'\b(?:aud|usd|\$)\s*[\d,\.]+\s*(?:mn|bn|million|billion)', clause_lower):
            score += 0.3
        
        # Limit to 1 clause max for numerics unless adjacent clauses both contain field/value terms
        is_numeric = bool(re.search(r'\d', value_clean))
        if is_numeric and len(clause.split()) > 15:
            # Check if this is truly a multi-clause situation
            adjacent_relevant = False
            if i > 0:
                prev_clause = clauses[i-1].lower()
                if any(fw in prev_clause for fw in field_words) and (value_clean in prev_clause or (core_num and core_num in prev_clause)):
                    adjacent_relevant = True
            if i < len(clauses) - 1:
                next_clause = clauses[i+1].lower()
                if any(fw in next_clause for fw in field_words) and (value_clean in next_clause or (core_num and core_num in next_clause)):
                    adjacent_relevant = True
            
            if not adjacent_relevant:
                score *= 0.7  # Penalty for long single clauses without adjacent relevance
        
        # Prefer appropriately sized clauses
        if 20 <= len(clause) <= 100:
            score += 0.2
        elif len(clause) > 150:
            score *= 0.8
        
        # Store clause with expansion text if applicable
        final_clause = expansion_text + clause if expansion_text else clause
        clause_scores.append((final_clause.strip(), score))
    
    if not clause_scores:
        return "", 0.0
    
    # Sort by score, then by completeness
    clause_scores.sort(key=lambda x: x[1], reverse=True)
    best_clause, best_score = clause_scores[0]
    
    # Post-process: Expand clause if it's fragmented
    best_clause = expand_clause_for_completeness(best_clause, field, value, clauses)
    
    return best_clause.strip(), min(1.0, best_score)


def expand_clause_for_completeness(clause: str, field: str, value: str, all_clauses: List[str] = None) -> str:
    """
    Expand clause to include complete financial metric context if fragmented.
    
    Args:
        clause: The selected clause
        field: Field name
        value: Field value
        all_clauses: All available clauses for context expansion
        
    Returns:
        Expanded clause with complete context
    """
    if not clause:
        return clause
    
    # Check if clause starts with a financial metric
    financial_starters = [
        'underlying', 'reported', 'npat', 'ebitda', 'ebit', 'profit', 'earnings',
        'revenue', 'margin', 'dividend', 'guidance', 'leverage', 'interim', 'pre-tax'
    ]
    
    clause_lower = clause.lower().strip()
    starts_with_metric = any(clause_lower.startswith(starter) for starter in financial_starters)
    
    if starts_with_metric:
        return clause
    
    # If clause starts with common fragments, try to find the complete context
    fragment_patterns = [
        r'^of\s+(?:aud|usd|\$)',  # Starts with "of AUD"
        r'^per\s+share',          # Starts with "per share"
        r'^ratio\s+of',           # Starts with "ratio of"
        r'^tax\s+',               # Starts with "tax" (missing "pre-")
    ]
    
    is_fragment = any(re.match(pattern, clause_lower) for pattern in fragment_patterns)
    
    if is_fragment and all_clauses:
        # Look for a preceding clause that might contain the metric
        normalized_field = normalize_field_name(field)
        field_words = normalized_field.split()
        
        for other_clause in all_clauses:
            if other_clause == clause:
                continue
                
            other_lower = other_clause.lower()
            
            # Check if this clause contains field-related terms
            has_field_terms = any(fw in other_lower for fw in field_words if len(fw) > 2)
            has_metric_terms = any(starter in other_lower for starter in financial_starters)
            
            if has_field_terms or has_metric_terms:
                # Try combining clauses if they seem related
                combined = f"{other_clause.strip()} {clause.strip()}"
                if len(combined) <= 150:  # Keep reasonable length
                    return combined
    
    # If no expansion possible, clean up the fragment
    if clause_lower.startswith('of '):
        # Try to infer the metric from the field name
        normalized_field = normalize_field_name(field)
        if 'npat' in normalized_field:
            return f"NPAT {clause}"
        elif 'profit' in normalized_field:
            return f"profit {clause}"
        elif 'earnings' in normalized_field:
            return f"earnings {clause}"
        elif 'revenue' in normalized_field:
            return f"revenue {clause}"
        elif 'margin' in normalized_field:
            return f"margin {clause}"
    
    return clause


def get_financial_metric_anchors() -> List[str]:
    """
    Get list of financial metric anchor terms for tight phrase extraction.
    
    Returns:
        List of metric anchor keywords
    """
    return [
        "npat", "npat1", "underlying npat", "underlying npat1", "reported npat",
        "ebitda", "ebit", "pbt", "pre-tax profit", "pretax profit",
        "revenue", "total revenue", "underlying revenue", 
        "earnings", "earnings per share", "eps", "underlying eps",
        "margin", "ebit margin", "profit margin", "net margin",
        "cost", "costs", "expenses", "investment costs",
        "net profit", "profit", "underlying profit", "reported profit",
        "income", "net income", "total income",
        "dividend", "interim dividend", "final dividend",
        "guidance", "npat guidance", "underlying guidance",
        "leverage ratio", "debt ratio", "cash", "facilities"
    ]


def extract_metric_phrase(text: str, value: str, anchors: List[str]) -> List[Tuple[str, float]]:
    """
    Extract tight metric phrases around numeric values using enhanced anchor detection and financial comparatives.
    
    Args:
        text: Full document text
        value: Numeric value to find
        anchors: List of financial metric anchor terms
        
    Returns:
        List of (phrase, confidence) tuples
    """
    phrases = []
    normalized_value = str(value).strip()
    
    # Extract core numeric part for flexible matching
    core_number = re.search(r'[\d,\.]+', normalized_value)
    if not core_number:
        return phrases
    
    core_num = core_number.group()
    
    # Enhanced search patterns for financial comparatives
    search_patterns = [
        re.escape(normalized_value),  # Exact match
        re.escape(core_num) + r'\s*(?:mn|bn|m|b|%|million|billion|cents)',  # Core + units
        r'(?:aud|usd|gbp|eur|\$)\s*' + re.escape(core_num),  # Currency prefix
    ]
    
    # Enhanced regex patterns for complete financial statements with comparatives
    enhanced_patterns = [
        # Full EPS patterns with comparatives
        rf'([\w\s]+earnings per share\s+of\s+{re.escape(core_num)}\s*cents?\s*per share\s*\([^)]+\))',
        rf'([\w\s]*earnings per share\s+{re.escape(core_num)}\s*cents?\s*\([^)]+\))',
        # NPAT patterns
        rf'([\w\s]+(?:npat|profit)\s+of\s+(?:aud|usd|\$)?\s*{re.escape(core_num)}\s*(?:mn|million)?\s*\([^)]+\))',
        # General metric patterns
        rf'([\w\s]+(?:margin|dividend|revenue|guidance)\s+of\s+{re.escape(core_num)}\s*[%]?\s*\([^)]+\))',
        # Legacy pattern for backward compatibility
        rf'([A-Za-z\s]+(?:npat|profit|earnings|revenue|margin|dividend|guidance)\s+of\s+(?:aud|usd|\$)?\s*{re.escape(core_num)}[^(]*\([^)]*(?:aud|usd|\$)?\s*[\d,\.]+[^)]*\)(?:[^.]*(?:up|down|increase|decrease)\s+[\d,\.]+%)?)'
    ]
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        line_clean = line.strip()
        
        # First, try to match enhanced financial patterns
        pattern_matched = False
        for pattern in enhanced_patterns:
            comparative_match = re.search(pattern, line_clean, re.IGNORECASE)
            if comparative_match:
                phrase = comparative_match.group(1).strip()
                if phrase and len(phrase) > 10:
                    confidence = 1.0  # Highest confidence for complete patterns
                    phrases.append((phrase, confidence))
                    pattern_matched = True
                    break
        
        if pattern_matched:
            continue
        
        # Check if line contains our target value
        value_found = False
        value_match = None
        for pattern in search_patterns:
            match = re.search(pattern, line_clean, re.IGNORECASE)
            if match:
                value_found = True
                value_match = match
                break
        
        if not value_found:
            continue
        
        # Look for metric anchors in the same line
        line_lower = line_clean.lower()
        best_anchor = None
        anchor_pos = -1
        
        for anchor in anchors:
            anchor_pattern = r'\b' + re.escape(anchor.lower()) + r'\b'
            anchor_match = re.search(anchor_pattern, line_lower)
            if anchor_match and (anchor_pos == -1 or anchor_match.start() > anchor_pos):
                best_anchor = anchor
                anchor_pos = anchor_match.start()
        
        if best_anchor:
            # Extract phrase from anchor to end of metric statement
            anchor_start = line_lower.find(best_anchor.lower())
            value_end = value_match.end()
            
            # Extend to include comparative values in brackets - treat as single unit
            extended_end = value_end
            remaining_text = line_clean[value_end:]
            
            # Look for bracketed comparisons like (1HFY22: AUD 30.6mn) - capture as complete unit
            bracket_match = re.search(r'\s*\([^)]*(?:1hfy\d+|fy\d+|20\d+)[^)]*\)', remaining_text, re.IGNORECASE)
            if bracket_match:
                extended_end = value_end + bracket_match.end()
            
            # Look for percentage changes like ", up 52.6%" but stop at sentence boundaries
            change_match = re.search(r'\s*,?\s*(?:up|down|increase|decrease)\s+[\d,\.]+%(?=\s|$|\.)', remaining_text, re.IGNORECASE)
            if change_match:
                extended_end = value_end + change_match.end()
            
            # Extract the tight phrase and clean it
            phrase = line_clean[anchor_start:extended_end].strip()
            
            # Remove any trailing punctuation that might cause issues
            phrase = re.sub(r'[,;]\s*$', '', phrase)
            
            if phrase and len(phrase) > 10:  # Ensure meaningful content
                confidence = 1.0  # High confidence for anchor-based extraction
                phrases.append((phrase, confidence))
        
        else:
            # Fallback: extract window around value with connector words
            value_start = value_match.start()
            
            # Look backward for connector words or start of meaningful phrase
            window_start = max(0, value_start - 30)  # Reduced window for tighter extraction
            prefix_text = line_clean[window_start:value_start]
            
            # Find last occurrence of connector words
            connectors = ['of', 'for', 'at', 'was', 'is', 'to', 'from', 'with']
            best_connector_pos = -1
            
            for connector in connectors:
                connector_pattern = r'\b' + re.escape(connector) + r'\s*$'
                match = re.search(connector_pattern, prefix_text, re.IGNORECASE)
                if match:
                    best_connector_pos = window_start + match.start()
                    break
            
            if best_connector_pos != -1:
                # Extract from connector to end of value (with extensions)
                value_end = value_match.end()
                extended_end = value_end
                
                # Include bracketed comparisons as complete units
                remaining_text = line_clean[value_end:]
                bracket_match = re.search(r'\s*\([^)]*(?:1hfy\d+|fy\d+|20\d+)[^)]*\)', remaining_text, re.IGNORECASE)
                if bracket_match:
                    extended_end = value_end + bracket_match.end()
                
                phrase = line_clean[best_connector_pos:extended_end].strip()
                phrase = re.sub(r'[,;]\s*$', '', phrase)  # Clean trailing punctuation
                
                if phrase and len(phrase) > 5:
                    confidence = 0.8  # Good confidence for connector-based extraction
                    phrases.append((phrase, confidence))
    
    # Remove duplicates and sort by confidence, preferring shorter phrases
    unique_phrases = []
    seen_phrases = set()
    
    for phrase, conf in sorted(phrases, key=lambda x: (x[1], -len(x[0])), reverse=True):
        phrase_key = phrase.lower().strip()
        if phrase_key not in seen_phrases:
            seen_phrases.add(phrase_key)
            unique_phrases.append((phrase, conf))
    
    return unique_phrases[:2]  # Return top 2 matches


def extract_numeric_pair_context(value: str, full_text: str) -> List[Tuple[str, float]]:
    """
    Extract context for numeric values that appear in comparative pairs, treating parentheticals as units.
    
    Args:
        value: The numeric value to find
        full_text: Complete document text
        
    Returns:
        List of (context_text, confidence_score) tuples containing comparative context
    """
    contexts = []
    normalized_value = str(value).strip()
    
    # Extract core numeric part for more flexible matching
    core_number = re.search(r'[\d,\.]+', normalized_value)
    if not core_number:
        return contexts
    
    core_num = core_number.group()
    
    # Create search patterns
    search_patterns = [
        re.escape(normalized_value),  # Exact match
        re.escape(core_num) + r'\s*(?:mn|bn|m|b|%|million|billion|cents)',  # Core number with units
        r'(?:aud|usd|gbp|eur)\s*' + re.escape(core_num),  # Currency prefix
    ]
    
    # Enhanced pattern for complete comparative statements
    comparative_pattern = rf'[^.!?]*(?:aud|usd|\$)?\s*{re.escape(core_num)}[^.!?]*\([^)]*(?:aud|usd|\$)?\s*[\d,\.]+[^)]*\)[^.!?]*'
    
    # Find lines containing the target value
    lines = full_text.split('\n')
    
    for line_idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # First, try to match complete comparative patterns
        comparative_match = re.search(comparative_pattern, line_clean, re.IGNORECASE)
        if comparative_match:
            comparative_text = comparative_match.group().strip()
            # Clean up the extracted text
            comparative_text = re.sub(r'^[•\-\*\+]\s*', '', comparative_text)  # Remove bullet points
            comparative_text = re.sub(r'^\d+[\.\)]\s*', '', comparative_text)  # Remove numbering
            
            if comparative_text and len(comparative_text) > 15:
                confidence = 1.0  # High confidence for complete comparative patterns
                contexts.append((comparative_text, confidence))
                continue
        
        # Check if this line contains our target value using any pattern
        value_found = False
        for pattern in search_patterns:
            if re.search(pattern, line_clean, re.IGNORECASE):
                value_found = True
                break
        
        if not value_found:
            continue
        
        # Count numeric values in this line to identify comparative contexts
        numeric_pattern = r'[\d,\.]+(mn|bn|m|b|%|million|billion|cents|dollars?|aud|usd|gbp|eur)?'
        numeric_matches = re.findall(numeric_pattern, line_clean.lower())
        
        if len(numeric_matches) >= 2:
            # This line contains multiple numeric values - likely comparative
            # Clean the line for better presentation
            cleaned_line = re.sub(r'^[•\-\*\+]\s*', '', line_clean)  # Remove bullet points
            cleaned_line = re.sub(r'^\d+[\.\)]\s*', '', cleaned_line)  # Remove numbering
            
            confidence = 0.9
            contexts.append((cleaned_line, confidence))
    
    # Remove duplicates and prioritize shorter, more focused contexts
    unique_contexts = []
    seen_contexts = set()
    
    for context, conf in sorted(contexts, key=lambda x: (x[1], -len(x[0])), reverse=True):
        context_key = context.lower().strip()
        if context_key not in seen_contexts and 15 <= len(context) <= 200:  # Prefer focused contexts
            # Boost confidence if exact value is found
            for pattern in search_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    conf = min(1.0, conf + 0.1)  # Small boost
                    break
            
            seen_contexts.add(context_key)
            unique_contexts.append((context, conf))
    
    return unique_contexts[:2]  # Return top 2 matches


def generate_context_for_field(field: str, value: str, full_text: str, 
                              similarity_threshold: int = 75, 
                              semantic_threshold: float = 0.55,
                              enable_recovery: bool = True) -> Tuple[str, float]:
    """
    Generate refined context with clause-level trimming and enhanced numeric handling.
    Prioritizes minimal relevant phrases over verbose sentences.
    
    Args:
        field: The field name (e.g., "Net_Profit", "Revenue")
        value: The field value (e.g., "$115.5 million", "15% growth")
        full_text: Complete document text
        similarity_threshold: Minimum similarity score for fuzzy matching (0-100)
        semantic_threshold: Minimum semantic similarity score (0.0-1.0)
        enable_recovery: Whether to enable strict context recovery for empty results
        
    Returns:
        Tuple of (context_string, max_confidence_score) with minimal relevant phrases
    """
    if not full_text or not value:
        return "", 0.0
    
    print(f"Processing field '{field}' with value '{value}' using refined context generation")
    
    # NUMERIC-AWARE PROCESSING: Check if this is a numeric/currency value
    is_numeric = is_numeric_value(value)
    
    # Enhanced field-value mismatch prevention for problematic fields
    problematic_fields = ['period', 'company', 'name', 'technology_impact', 'performance_outcome']
    field_lower = field.lower()
    is_problematic_field = any(prob_field in field_lower for prob_field in problematic_fields)
    
    if is_numeric and not is_problematic_field:
        print(f"  Detected numeric value, applying specialized tight phrase extraction")
        
        # Get financial metric anchors
        anchors = get_financial_metric_anchors()
        
        # Try tight metric phrase extraction first (highest precision)
        metric_phrases = extract_metric_phrase(full_text, value, anchors)
        if metric_phrases:
            best_context, best_confidence = metric_phrases[0]
            # Quality check for artifacts
            if '+' in best_context or '?' in best_context:
                print(f"  Rejecting metric phrase with artifacts: {best_context}")
            else:
                print(f"  Found tight metric phrase with confidence: {best_confidence:.3f}")
                return best_context, round(best_confidence, 3)
        
        # Fallback to numeric pair context (for comparative values)
        pair_contexts = extract_numeric_pair_context(value, full_text)
        if pair_contexts:
            best_context, best_confidence = pair_contexts[0]
            # Quality check for artifacts
            if '+' in best_context or '?' in best_context:
                print(f"  Rejecting pair context with artifacts: {best_context}")
            else:
                print(f"  Found numeric pair context with confidence: {best_confidence:.3f}")
                return best_context, round(best_confidence, 3)
        
        # Last resort: numeric window extraction (keep flexible window_size)
        window_contexts = extract_numeric_context_window(value, full_text)
        if window_contexts:
            best_context, best_confidence = window_contexts[0]
            # Quality check for artifacts
            if '+' in best_context or '?' in best_context:
                print(f"  Rejecting window context with artifacts: {best_context}")
            else:
                print(f"  Found numeric window context with confidence: {best_confidence:.3f}")
                return best_context, round(best_confidence, 3)
        
        print("  No numeric context found, falling back to semantic processing")
    elif is_problematic_field:
        print(f"  Problematic field detected, skipping numeric extraction to prevent mismatches")
    
    # Extract discrete sentences preserving punctuation and order
    sentences_with_indices = extract_sentences_from_text(full_text)
    if not sentences_with_indices:
        return "", 0.0
    
    print(f"  Analyzing {len(sentences_with_indices)} sentences from document")
    
    # Get semantic model for similarity computation
    model = get_semantic_model() if SEMANTIC_AVAILABLE else None
    
    # Get enhanced semantic groups and anti-patterns
    semantic_groups = get_enhanced_semantic_groups()
    anti_patterns = get_enhanced_anti_patterns()
    
    # PHASE 1: Sentence-level relevance filtering with normalized field names
    normalized_field = normalize_field_name(field)
    relevant_sentences = []  # List of (sentence, index, confidence)
    
    for sentence, idx in sentences_with_indices:
        is_relevant, confidence = is_relevant_sentence(
            normalized_field, sentence, value, semantic_groups, anti_patterns, model, semantic_threshold, is_numeric
        )
        
        if is_relevant:
            relevant_sentences.append((sentence, idx, confidence))
    
    print(f"  Found {len(relevant_sentences)} relevant sentences")
    
    # PHASE 2: Clause-level trimming for minimal relevant phrases
    if relevant_sentences:
        print("  Applying clause-level trimming for minimal phrases")
        
        clause_candidates = []
        
        for sentence, idx, confidence in relevant_sentences:
            # Split sentence into clauses
            clauses = split_into_clauses(sentence)
            
            # Find the most relevant clause
            best_clause, clause_confidence = find_minimal_relevant_clause(clauses, field, value)
            
            if best_clause:
                # Combine sentence confidence with clause confidence
                combined_confidence = (confidence + clause_confidence) / 2
                clause_candidates.append((best_clause, idx, combined_confidence))
        
        if clause_candidates:
            # Sort by confidence, then by fuzzy match to field+value
            clause_candidates.sort(key=lambda x: x[2], reverse=True)
            
            # Enhanced CEO/Commentary handling with regex quote extraction
            if 'ceo' in normalized_field.lower() or 'statement' in normalized_field.lower() or 'comment' in normalized_field.lower():
                print("  Processing CEO/statement field with quote extraction")
                
                # Use regex to capture full quotes
                quote_pattern = r'said:\s*"([^"]+)"'
                for sentence, idx, confidence in relevant_sentences:
                    quote_match = re.search(quote_pattern, sentence, re.IGNORECASE)
                    if quote_match:
                        full_quote = quote_match.group(0)  # Include 'said: "..."'
                        print(f"  Found CEO quote with regex, confidence: {confidence:.3f}")
                        return full_quote, round(confidence, 3)
                
                # Fallback: look for quote indicators in clauses
                quote_clauses = []
                for clause, idx, conf in clause_candidates:
                    if any(indicator in clause.lower() for indicator in ['said:', 'commented:', 'stated:']):
                        quote_clauses.append((clause, idx, conf))
                
                if quote_clauses:
                    best_quote, _, quote_conf = quote_clauses[0]
                    print(f"  Generated quote context, confidence: {quote_conf:.3f}")
                    return best_quote, round(quote_conf, 3)
                else:
                    # Route to "Overall Document Commentary" if no quote found
                    print("  No quote found, routing to Overall Document Commentary")
                    return "", 0.0
            
            # For numeric fields: Limit to 1 clause max unless adjacent clauses both contain field/value terms
            elif is_numeric:
                best_clause, best_idx, best_conf = clause_candidates[0]
                
                # Check for specific field patterns that need exact bullet matching
                if 'tysers' in normalized_field.lower() and 'months' in str(value).lower():
                    print("  Special handling for Tysers contribution field")
                    # Look for exact bullet containing both field and value
                    for sentence, idx, confidence in relevant_sentences:
                        sentence_lower = sentence.lower()
                        if 'tysers' in sentence_lower and 'months' in sentence_lower and 'profit' in sentence_lower:
                            if '3 months' in sentence_lower or 'three months' in sentence_lower:
                                print(f"  Found exact Tysers bullet, confidence: {confidence:.3f}")
                                return sentence, round(confidence, 3)
                
                # Standard numeric processing with clause joining limits
                if len(clause_candidates) > 1:
                    # Check if adjacent clauses both contain field/value terms with high fuzzy match
                    should_join = False
                    for i in range(len(clause_candidates) - 1):
                        clause1, _, conf1 = clause_candidates[i]
                        clause2, _, conf2 = clause_candidates[i + 1]
                        
                        # Check fuzzy match for both clauses
                        field_value_combo = f"{field} {value}".lower()
                        fuzzy1 = fuzz.partial_ratio(field_value_combo, clause1.lower())
                        fuzzy2 = fuzz.partial_ratio(field_value_combo, clause2.lower())
                        
                        if fuzzy1 > 90 and fuzzy2 > 90:
                            should_join = True
                            break
                    
                    if not should_join:
                        # Use only the single best clause
                        best_clause = clause_candidates[0][0]
                        best_conf = clause_candidates[0][2]
                
                # Final quality check - reject if contains artifacts
                if '+' in best_clause or '?' in best_clause:
                    print(f"  Rejecting clause with artifacts: {best_clause}")
                    return "", 0.0
                
                print(f"  Generated precise numeric clause, confidence: {best_conf:.3f}")
                return best_clause, round(best_conf, 3)
            
            # For other fields: Use single best clause with high threshold
            else:
                best_clause, best_idx, best_conf = clause_candidates[0]
                
                # Validate the best clause has high fuzzy match to field+value combination
                field_value_combo = f"{field} {value}".lower()
                clause_fuzzy = fuzz.partial_ratio(field_value_combo, best_clause.lower())
                
                if clause_fuzzy > 75:  # Higher threshold for precision
                    # Final quality check
                    if '+' in best_clause or '?' in best_clause:
                        print(f"  Rejecting clause with artifacts: {best_clause}")
                        return "", 0.0
                    
                    print(f"  Generated precise clause-level context, confidence: {best_conf:.3f}")
                    return best_clause, round(best_conf, 3)
    
    # PHASE 3: Stricter recovery - only if exact value match
    if not relevant_sentences and enable_recovery:
        print("  No relevant sentences found, attempting strict recovery (exact value match only)...")
        
        value_clean = str(value).strip().lower()
        recovery_candidates = []
        
        for sentence, idx in sentences_with_indices:
            sentence_lower = sentence.lower()
            
            # Only recover if exact value is found
            if value_clean in sentence_lower:
                # Apply clause trimming to recovery candidates too
                clauses = split_into_clauses(sentence)
                best_clause, clause_confidence = find_minimal_relevant_clause(clauses, field, value)
                
                if best_clause and clause_confidence > 0.3:  # Higher threshold for recovery
                    recovery_candidates.append((best_clause, clause_confidence))
        
        if recovery_candidates:
            # Sort by confidence and take the best
            recovery_candidates.sort(key=lambda x: x[1], reverse=True)
            best_recovery, recovery_confidence = recovery_candidates[0]
            
            print(f"  Strict recovery found context with confidence: {recovery_confidence:.3f}")
            return best_recovery, round(recovery_confidence, 3)
    
    # NUMERIC FALLBACK: If semantic processing failed but this is a numeric value (not for problematic fields)
    if is_numeric and enable_recovery and not is_problematic_field:
        print("  Semantic processing failed, trying numeric fallback with reduced confidence...")
        
        # Get financial metric anchors
        anchors = get_financial_metric_anchors()
        
        # Try tight metric phrase extraction with fallback confidence
        metric_phrases = extract_metric_phrase(full_text, value, anchors)
        if metric_phrases:
            best_context, best_confidence = metric_phrases[0]
            # Quality check for artifacts
            if '+' in best_context or '?' in best_context:
                print(f"  Rejecting fallback metric phrase with artifacts")
            else:
                # Reduce confidence since this is a fallback
                fallback_confidence = best_confidence * 0.7
                print(f"  Metric phrase fallback found context with confidence: {fallback_confidence:.3f}")
                return best_context, round(fallback_confidence, 3)
        
        # Try numeric pair context with reduced confidence
        pair_contexts = extract_numeric_pair_context(value, full_text)
        if pair_contexts:
            best_context, best_confidence = pair_contexts[0]
            # Quality check for artifacts
            if '+' in best_context or '?' in best_context:
                print(f"  Rejecting fallback pair context with artifacts")
            else:
                # Reduce confidence since this is a fallback
                fallback_confidence = best_confidence * 0.6
                print(f"  Numeric fallback found context with confidence: {fallback_confidence:.3f}")
                return best_context, round(fallback_confidence, 3)
    
    print("  No relevant context found")
    return "", 0.0


def handle_truncation_and_chopping(context: str, max_length: int = 2000) -> str:
    """
    Handle truncation with complete clause preservation to avoid word chopping.
    
    Args:
        context: The context string to potentially truncate
        max_length: Maximum allowed length (increased from 1000 to 2000)
        
    Returns:
        Properly truncated context ending with complete clause
    """
    if not context or len(context) <= max_length:
        return context
    
    # Truncate to max_length but ensure we end with a complete clause
    truncated = context[:max_length]
    
    # Find the last complete clause by looking for sentence endings
    clause_endings = ['.', '!', '?', ';']
    last_ending = -1
    
    for ending in clause_endings:
        pos = truncated.rfind(ending)
        if pos > last_ending:
            last_ending = pos
    
    # If we found a clause ending, truncate there
    if last_ending > max_length * 0.7:  # Only if we're not losing too much content
        return truncated[:last_ending + 1].strip()
    
    # Fallback: find last complete word to avoid chopping
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        return truncated[:last_space].strip() + '...'
    
    # Last resort: return as-is with ellipsis
    return truncated.strip() + '...'


def integrate_context_tracking(structured_data: Dict[str, Any], processed_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced context tracking integration with deduplication and quality control.
    
    Args:
        structured_data: Original structured data from document extraction
        processed_result: Result from LLM processing
        
    Returns:
        Enhanced result with comprehensive context information added
    """
    # Get the full document text
    document_text_lines = structured_data.get('document_text', [])
    if not document_text_lines:
        print("Warning: No document text available for context tracking")
        return processed_result
    
    # Join all document text into a single string for processing
    full_text = ' '.join(document_text_lines)
    
    print(f"Context tracking: Processing {len(document_text_lines)} lines of text ({len(full_text)} characters)")
    
    # Create enhanced data with context and deduplication
    enhanced_data = []
    context_stats = {
        'total_fields': 0,
        'fields_with_context': 0,
        'total_context_length': 0
    }
    
    # Context cache for deduplication
    context_cache = {}  # Key: field+value hash, Value: (context, confidence)
    
    # Process tables with enhanced context
    if 'processed_tables' in processed_result:
        for table_idx, table in enumerate(processed_result['processed_tables']):
            if table.get('structured_table') and not table['structured_table'].get('error'):
                table_data = table['structured_table']
                page = table.get('page', 'N/A')
                
                for field_name, field_value in table_data.items():
                    if field_name != 'error' and field_value:
                        context_stats['total_fields'] += 1
                        
                        # Check cache first for deduplication
                        cache_key = f"{field_name}:{field_value}".lower()
                        
                        if cache_key in context_cache:
                            context, confidence = context_cache[cache_key]
                        else:
                            # Generate comprehensive context with confidence
                            context, confidence = generate_context_for_field(field_name, field_value, full_text)
                            
                            # Enhanced CEO/Commentary routing
                            if not context and ('ceo' in field_name.lower() or 'statement' in field_name.lower() or 'comment' in field_name.lower()):
                                print(f"  Routing {field_name} to Overall Document Commentary")
                                # Add to overall commentary collection instead of individual field
                                context = ""  # Keep empty for individual field
                                confidence = 0.0
                            
                            # Apply enhanced truncation handling
                            if context:
                                context = handle_truncation_and_chopping(context, 2000)
                            
                            # Cache the result if it's good quality
                            if context and confidence > 0.5:
                                context_cache[cache_key] = (context, confidence)
                        
                        # Enhanced quality control - reject contexts with artifacts or low quality
                        if context:
                            # Reject if contains artifacts after cleaning
                            if '+' in context or '?' in context:
                                print(f"  Rejecting context with artifacts for {field_name}")
                                context = ""
                                confidence = 0.0
                            # Reject long contexts with low confidence
                            elif len(context) > 500 and confidence < 0.6:
                                print(f"  Rejecting long low-confidence context for {field_name}")
                                context = ""
                                confidence = 0.0
                            # Higher confidence threshold for general quality
                            elif confidence < 0.6:
                                print(f"  Rejecting low-confidence context for {field_name}")
                                context = ""
                                confidence = 0.0
                        
                        if context:
                            context_stats['fields_with_context'] += 1
                            context_stats['total_context_length'] += len(context)
                        
                        enhanced_data.append({
                            'source': f'Table {table_idx + 1}',
                            'type': 'Table Data',
                            'field': field_name,
                            'value': str(field_value),
                            'page': page,
                            'context': context,
                            'context_confidence': confidence,
                            'has_context': bool(context)
                        })
    
    # Process key-value pairs with enhanced context
    if 'processed_key_values' in processed_result:
        kv_data = processed_result['processed_key_values'].get('structured_key_values', {})
        if kv_data and not kv_data.get('error'):
            for field_name, field_value in kv_data.items():
                if field_name != 'error' and field_value:
                    context_stats['total_fields'] += 1
                    
                    # Check cache first for deduplication
                    cache_key = f"{field_name}:{field_value}".lower()
                    
                    if cache_key in context_cache:
                        context, confidence = context_cache[cache_key]
                    else:
                        # Generate comprehensive context with confidence
                        context, confidence = generate_context_for_field(field_name, field_value, full_text)
                        
                        # Cache the result if it's good quality
                        if context and confidence > 0.5:
                            context_cache[cache_key] = (context, confidence)
                    
                    # Enhanced quality control
                    if context:
                        if '+' in context or '?' in context:
                            context = ""
                            confidence = 0.0
                        elif len(context) > 500 and confidence < 0.6:
                            context = ""
                            confidence = 0.0
                        elif confidence < 0.6:
                            context = ""
                            confidence = 0.0
                    
                    if context:
                        context_stats['fields_with_context'] += 1
                        context_stats['total_context_length'] += len(context)
                    
                    enhanced_data.append({
                        'source': 'Key-Value Pairs',
                        'type': 'Structured Data',
                        'field': field_name,
                        'value': str(field_value),
                        'page': 'N/A',
                        'context': context,
                        'context_confidence': confidence,
                        'has_context': bool(context)
                    })
    
    # Process document text facts with enhanced context
    if 'processed_document_text' in processed_result:
        for chunk_idx, chunk in enumerate(processed_result['processed_document_text']):
            if 'extracted_facts' in chunk and not chunk['extracted_facts'].get('error'):
                facts = chunk['extracted_facts']
                for field_name, field_value in facts.items():
                    if field_name != 'error' and field_value:
                        context_stats['total_fields'] += 1
                        
                        # Check cache first for deduplication
                        cache_key = f"{field_name}:{field_value}".lower()
                        
                        if cache_key in context_cache:
                            context, confidence = context_cache[cache_key]
                        else:
                            # Generate comprehensive context with confidence
                            context, confidence = generate_context_for_field(field_name, field_value, full_text)
                            
                            # Cache the result if it's good quality
                            if context and confidence > 0.5:
                                context_cache[cache_key] = (context, confidence)
                        
                        # Enhanced quality control
                        if context:
                            if '+' in context or '?' in context:
                                context = ""
                                confidence = 0.0
                            elif len(context) > 500 and confidence < 0.6:
                                context = ""
                                confidence = 0.0
                            elif confidence < 0.6:
                                context = ""
                                confidence = 0.0
                        
                        if context:
                            context_stats['fields_with_context'] += 1
                            context_stats['total_context_length'] += len(context)
                        
                        # Determine data type
                        data_type = 'Footnote' if 'footnote' in field_name.lower() else 'Financial Data'
                        field_display = field_name.replace('_Footnote', ' (Footnote)').replace('Footnote_', 'Footnote: ')
                        
                        enhanced_data.append({
                            'source': f'Text Chunk {chunk_idx + 1}',
                            'type': data_type,
                            'field': field_display,
                            'value': str(field_value),
                            'page': 'N/A',
                            'context': context,
                            'context_confidence': confidence,
                            'has_context': bool(context)
                        })
    
    # Add enhanced context tracking summary
    processed_result['context_tracking_summary'] = {
        'total_fields': context_stats['total_fields'],
        'fields_with_context': context_stats['fields_with_context'],
        'context_coverage_percentage': round((context_stats['fields_with_context'] / max(context_stats['total_fields'], 1)) * 100, 1),
        'average_context_length': round(context_stats['total_context_length'] / max(context_stats['fields_with_context'], 1), 1) if context_stats['fields_with_context'] > 0 else 0,
        'total_context_characters': context_stats['total_context_length'],
        'document_text_lines': len(document_text_lines),
        'document_text_characters': len(full_text)
    }
    
    processed_result['enhanced_data_with_context'] = enhanced_data
    
    print(f"Context tracking completed: {context_stats['fields_with_context']}/{context_stats['total_fields']} fields have context ({processed_result['context_tracking_summary']['context_coverage_percentage']}%)")
    
    return processed_result


# Legacy compatibility functions
class EntityContextTracker:
    """Legacy compatibility class - use integrate_context_tracking() instead"""
    
    def __init__(self):
        print("Warning: EntityContextTracker is deprecated. Use integrate_context_tracking() function instead.")
        pass