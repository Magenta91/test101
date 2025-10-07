"""
Enhanced Context Tracker Module for Document Processing

This module implements comprehensive context tracking that extracts all relevant
narrative or descriptive text from the original document about each field/value,
preserving the original wording from the source PDF.
"""

import re
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict
import json
from fuzzywuzzy import fuzz


def extract_sentences_from_text(full_text: str) -> List[str]:
    """
    Extract sentences from full text, preserving original structure and wording.
    
    Args:
        full_text: Complete document text as a single string
        
    Returns:
        List of sentences with original wording preserved
    """
    if not full_text:
        return []
    
    # Split on sentence boundaries while preserving the sentences
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    
    # Clean and filter sentences
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        # Keep substantial sentences (more than 15 characters)
        if sentence and len(sentence) > 15:
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences


def generate_context_for_field(field: str, value: str, full_text: str, similarity_threshold: int = 75) -> str:
    """
    Generate context for a specific field/value by finding all relevant sentences
    from the document that mention the field or value.
    
    Args:
        field: The field name (e.g., "Company_Name", "Revenue")
        value: The field value (e.g., "Life360", "$115.5 million")
        full_text: Complete document text
        similarity_threshold: Minimum similarity score for fuzzy matching (0-100)
        
    Returns:
        Context string with all relevant sentences, preserving original wording
    """
    if not full_text or not value:
        return ""
    
    sentences = extract_sentences_from_text(full_text)
    if not sentences:
        return ""
    
    matching_sentences = []
    field_lower = field.lower() if field else ""
    value_lower = str(value).lower()
    
    # Clean field name for better matching
    field_clean = re.sub(r'[_-]', ' ', field_lower)
    field_words = [word for word in field_clean.split() if len(word) > 2]
    
    # Clean value for better matching
    value_clean = str(value).strip()
    
    # Extract key terms from value for matching
    value_terms = []
    
    # For numeric values, extract the number
    numeric_matches = re.findall(r'\d+\.?\d*', value_clean)
    value_terms.extend(numeric_matches)
    
    # For text values, extract significant words
    text_words = re.findall(r'\b[A-Za-z]{3,}\b', value_clean)
    value_terms.extend(text_words)
    
    # Add the full value
    if len(value_clean) > 2:
        value_terms.append(value_clean)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        match_score = 0
        reasons = []
        
        # Check for exact value match (highest priority)
        if value_clean.lower() in sentence_lower:
            match_score += 50
            reasons.append("exact_value")
        
        # Check for fuzzy value match
        elif value_clean and len(value_clean) > 3:
            fuzzy_score = fuzz.partial_ratio(value_lower, sentence_lower)
            if fuzzy_score >= similarity_threshold:
                match_score += fuzzy_score // 2
                reasons.append(f"fuzzy_value_{fuzzy_score}")
        
        # Check for field name components
        field_matches = 0
        for field_word in field_words:
            if field_word in sentence_lower:
                field_matches += 1
                match_score += 10
        
        if field_matches > 0:
            reasons.append(f"field_words_{field_matches}")
        
        # Check for value terms
        term_matches = 0
        for term in value_terms:
            if len(term) > 2 and term.lower() in sentence_lower:
                term_matches += 1
                match_score += 15
        
        if term_matches > 0:
            reasons.append(f"value_terms_{term_matches}")
        
        # Special handling for company names, symbols, and financial terms
        if any(indicator in field_lower for indicator in ['company', 'name', 'symbol', 'ticker']):
            # Look for company-related context
            company_indicators = ['inc', 'corp', 'ltd', 'llc', 'company', 'corporation']
            for indicator in company_indicators:
                if indicator in sentence_lower:
                    match_score += 5
                    reasons.append("company_context")
                    break
        
        # Include sentence if it meets the threshold
        if match_score >= 25:  # Minimum score to include
            matching_sentences.append({
                'sentence': sentence,
                'score': match_score,
                'reasons': reasons
            })
    
    # Sort by relevance score and remove duplicates
    matching_sentences.sort(key=lambda x: x['score'], reverse=True)
    
    # Remove duplicate sentences while preserving order
    seen_sentences = set()
    unique_sentences = []
    
    for match in matching_sentences:
        sentence_key = match['sentence'].lower().strip()
        if sentence_key not in seen_sentences:
            unique_sentences.append(match['sentence'])
            seen_sentences.add(sentence_key)
    
    # Join sentences preserving original order and language
    if unique_sentences:
        context = ' '.join(unique_sentences)
        
        # Limit context length while preserving complete sentences
        if len(context) > 800:
            # Find a good breaking point
            truncated = context[:750]
            last_period = truncated.rfind('.')
            if last_period > 400:  # Ensure substantial content
                context = truncated[:last_period + 1]
            else:
                context = truncated + '...'
        
        return context
    
    return ""


def integrate_context_tracking(structured_data: Dict[str, Any], processed_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced context tracking integration that extracts comprehensive context
    for each field/value from the original document text.
    
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
    
    # Create enhanced data with context
    enhanced_data = []
    context_stats = {
        'total_fields': 0,
        'fields_with_context': 0,
        'total_context_length': 0
    }
    
    # Process tables with enhanced context
    if 'processed_tables' in processed_result:
        for table_idx, table in enumerate(processed_result['processed_tables']):
            if table.get('structured_table') and not table['structured_table'].get('error'):
                table_data = table['structured_table']
                page = table.get('page', 'N/A')
                
                for field_name, field_value in table_data.items():
                    if field_name != 'error' and field_value:
                        context_stats['total_fields'] += 1
                        
                        # Generate comprehensive context
                        context = generate_context_for_field(field_name, field_value, full_text)
                        
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
                            'has_context': bool(context)
                        })
    
    # Process key-value pairs with enhanced context
    if 'processed_key_values' in processed_result:
        kv_data = processed_result['processed_key_values'].get('structured_key_values', {})
        if kv_data and not kv_data.get('error'):
            for field_name, field_value in kv_data.items():
                if field_name != 'error' and field_value:
                    context_stats['total_fields'] += 1
                    
                    # Generate comprehensive context
                    context = generate_context_for_field(field_name, field_value, full_text)
                    
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
                        
                        # Generate comprehensive context
                        context = generate_context_for_field(field_name, field_value, full_text)
                        
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