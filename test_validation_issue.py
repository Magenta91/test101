#!/usr/bin/env python3
"""
Test to check if the validation function is causing context to be cleared
"""

import json
from structured_llm_processor import validate_context_against_document

def test_validation_function():
    """Test the validation function with various scenarios"""
    
    # Test data with context that might fail validation
    test_extraction = {
        "fields": {
            "Revenue": {
                "value": "AUD 46.7mn",
                "context": "Revenue of AUD 46.7mn represents strong growth in the quarter."
            },
            "EPS": {
                "value": "48.18 cents",
                "context": "Underlying earnings per share of 48.18 cents shows improvement."
            },
            "Test_Field": {
                "value": "12%",
                "context": "This is a made-up context that won't be in the document."
            }
        }
    }
    
    # Document text that should match some contexts
    document_text = """
    Life360 Inc. Financial Results for Q4 2023
    Revenue of AUD 46.7mn represents strong growth in the quarter.
    Underlying earnings per share of 48.18 cents shows improvement.
    Operating expenses were AUD 0.4mn for the period.
    """
    
    print("Testing validation function...")
    print("=" * 50)
    
    print("Original extraction:")
    for field, data in test_extraction["fields"].items():
        print(f"  {field}: {data['value']} -> {data['context']}")
    
    # Test validation
    validated_result = validate_context_against_document(test_extraction, document_text)
    
    print("\nAfter validation:")
    for field, data in validated_result["fields"].items():
        context = data['context']
        if context:
            print(f"  ✅ {field}: {data['value']} -> {context}")
        else:
            print(f"  ❌ {field}: {data['value']} -> [CONTEXT CLEARED]")
    
    # Check if any context was cleared
    cleared_count = 0
    for field, data in validated_result["fields"].items():
        if not data['context']:
            cleared_count += 1
    
    print(f"\nSummary: {cleared_count} contexts were cleared by validation")
    
    return validated_result

if __name__ == "__main__":
    print("Testing Validation Function")
    print("=" * 60)
    
    try:
        result = test_validation_function()
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()