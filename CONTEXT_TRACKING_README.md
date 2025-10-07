# Enhanced Context Tracking for Document Processing

This document describes the enhanced context tracking system that ensures comprehensive entity-based context aggregation in document processing workflows.

## Overview

The context tracking system addresses the requirement to populate the **Context column** in output tables with all descriptive sentences from source documents that relate to each extracted entity. The system maintains exact wording from the original document and prevents duplication while ensuring comprehensive coverage.

## Key Features

### 1. Entity Tracking Across Pages
- **Cross-page entity recognition**: Tracks entities mentioned across multiple pages/sections
- **Identifier variations**: Handles synonyms, abbreviations, and alternative names
- **Exact string matching**: Uses precise matching with word boundaries
- **Relationship mapping**: Links structured data fields to their contextual mentions

### 2. Context Aggregation
- **Comprehensive sentence extraction**: Captures all relevant descriptive sentences
- **Word-for-word accuracy**: Maintains original wording exactly as in document
- **Contextual boundaries**: Includes surrounding sentences for complete context
- **Deduplication**: Prevents duplicate sentences while preserving unique mentions

### 3. Language Integrity
- **No paraphrasing**: Preserves exact grammar, casing, and wording
- **Original language**: Maintains the same language used in source document
- **Complete sentences**: Ensures context contains complete, meaningful sentences
- **Proper concatenation**: Joins multiple mentions with appropriate separators

## Architecture

### Core Components

#### `EntityContextTracker` Class
The main class responsible for entity tracking and context aggregation.

```python
class EntityContextTracker:
    def __init__(self):
        self.entity_contexts: Dict[str, List[str]] = defaultdict(list)
        self.entity_identifiers: Dict[str, Set[str]] = defaultdict(set)
        self.processed_sentences: Set[str] = set()
        self.document_text: List[str] = []
```

**Key Methods:**
- `register_entity()`: Register entities with their identifiers
- `extract_entity_contexts()`: Extract all relevant contexts from document
- `get_entity_context()`: Retrieve aggregated context for specific entity
- `generate_entity_key()`: Create consistent entity identifiers

#### Integration Function
```python
def integrate_context_tracking(structured_data, processed_result) -> Dict[str, Any]:
    """Integrate context tracking into existing processing pipeline"""
```

### Processing Pipeline

1. **Entity Registration Phase**
   - Extract entities from tables, key-value pairs, and document facts
   - Generate consistent entity keys
   - Register entity variations and synonyms

2. **Context Extraction Phase**
   - Scan document text for entity mentions
   - Extract contextual sentences with boundaries
   - Ensure complete sentence integrity

3. **Context Aggregation Phase**
   - Combine contexts for each entity
   - Remove duplicates while preserving order
   - Format for output table integration

4. **Output Enhancement Phase**
   - Add context column to structured data
   - Maintain existing data structure
   - Provide context tracking statistics

## Usage Examples

### Basic Integration

```python
from context_tracker import integrate_context_tracking

# After LLM processing
enhanced_result = integrate_context_tracking(structured_data, processed_result)

# Access enhanced data with context
for row in enhanced_result['enhanced_data_with_context']:
    print(f"Field: {row['field']}")
    print(f"Value: {row['value']}")
    print(f"Context: {row['context']}")
```

### Direct Entity Tracking

```python
from context_tracker import EntityContextTracker

tracker = EntityContextTracker()
tracker.set_document_text(document_lines)

# Register entities
tracker.register_entity("company_abc", "Company_Name", "ABC Corporation")
tracker.register_entity("ceo_john", "CEO_Name", "John Smith")

# Extract contexts
tracker.extract_entity_contexts()

# Get results
context = tracker.get_entity_context("company_abc")
print(f"ABC Corporation context: {context}")
```

## Entity Matching Strategy

### Identifier Variations
The system automatically generates variations for better matching:

- **Names**: First name, last name, full name combinations
- **Companies**: Base name without suffixes (Inc., Corp., LLC), acronyms
- **Trading Symbols**: Upper/lowercase variations
- **Numeric Values**: Formatted and unformatted versions

### Matching Algorithm
1. **Exact word matching**: Uses word boundaries for precise matching
2. **Case-insensitive**: Handles different capitalizations
3. **Phrase matching**: Supports multi-word entity names
4. **Context validation**: Ensures matches are meaningful

## Context Extraction Rules

### Sentence Boundaries
- Extracts complete sentences only
- Includes 1-2 surrounding sentences for context
- Ensures sentences start with capital letters
- Maintains proper punctuation

### Quality Filters
- Minimum sentence length (15+ characters)
- Substantial content requirements
- Complete sentence validation
- Relevance scoring

### Deduplication
- Tracks processed sentences globally
- Prevents duplicate contexts per entity
- Maintains chronological order
- Preserves unique mentions

## Output Format

### Enhanced Data Structure
```python
{
    'source': 'Table 1',
    'type': 'Table Data', 
    'field': 'Company_Name',
    'value': 'ABC Corporation',
    'page': '1',
    'context': 'ABC Corporation is a leading technology company. The company reported strong growth in Q4 2024.',
    'has_context': True
}
```

### Context Tracking Summary
```python
{
    'total_entities': 15,
    'entities_with_context': 12,
    'total_context_sentences': 45,
    'unique_sentences_processed': 38
}
```

## Integration Points

### Existing Processors
The context tracking integrates seamlessly with:
- `structured_llm_processor.py`: Automatic integration in processing pipeline
- `app.py`: Enhanced streaming and export endpoints
- `textract_processor.py`: Document text extraction compatibility

### API Endpoints
- `/process_stream`: Includes context in streaming output
- `/process`: Enhanced data with context in response
- `/export_xlsx`: Context column in Excel exports

## Performance Considerations

### Optimization Features
- **Selective processing**: Limits context extraction for large documents
- **Relevance scoring**: Only includes high-confidence matches
- **Batch processing**: Efficient entity registration and extraction
- **Memory management**: Prevents excessive memory usage

### Scalability Limits
- Maximum 30 data points for context matching
- Document text limit of 150 lines for full processing
- Fallback to basic processing for large documents

## Testing

### Test Script
Run the comprehensive test suite:
```bash
python test_context_tracking.py
```

### Test Coverage
- Entity registration and variation generation
- Context extraction and aggregation
- Integration with existing pipeline
- Output format validation
- Performance with various document sizes

## Configuration

### Environment Variables
No additional environment variables required. The system uses existing OpenAI API configuration.

### Customization Options
- Adjust entity variation rules in `_add_entity_variations()`
- Modify context extraction boundaries in `_get_contextual_text()`
- Configure relevance scoring in `_find_entity_mentions()`

## Error Handling

### Graceful Degradation
- Falls back to original processing if context tracking fails
- Continues processing even with partial context extraction
- Logs errors without stopping the pipeline

### Error Recovery
- Handles malformed entity data
- Manages missing document text
- Recovers from context extraction failures

## Future Enhancements

### Planned Features
- Multi-language support with language detection
- Advanced entity relationship mapping
- Configurable context extraction rules
- Performance optimization for large documents

### Extension Points
- Custom entity type handlers
- Pluggable matching algorithms
- Configurable output formats
- Integration with additional processors

## Conclusion

The enhanced context tracking system provides comprehensive entity-based context aggregation while maintaining document integrity and processing efficiency. It seamlessly integrates with existing workflows and provides valuable contextual information for extracted structured data.

For questions or issues, refer to the test scripts and integration examples provided in this repository.