#!/usr/bin/env python3
"""
Debug script to simulate real application scenario
"""

import json
from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_empty_or_minimal_data():
    """Test what happens with empty or minimal data like might come from real app"""
    
    print("Testing various data scenarios that might cause only 2 rows...")
    
    # Test 1: Empty data
    print("\n1. Testing empty data:")
    empty_data = {}
    result = process_structured_data_with_llm_unified(empty_data)
    print(f"Empty data result: {result}")
    
    # Test 2: Data with empty arrays
    print("\n2. Testing data with empty arrays:")
    empty_arrays_data = {
        "document_text": [],
        "tables": [],
        "key_values": []
    }
    result = process_structured_data_with_llm_unified(empty_arrays_data)
    print(f"Empty arrays result: {result}")
    
    # Test 3: Data with only document text but no meaningful content
    print("\n3. Testing minimal document text:")
    minimal_data = {
        "document_text": ["Document Title", "Page 1"],
        "tables": [],
        "key_values": []
    }
    result = process_structured_data_with_llm_unified(minimal_data)
    converted = convert_unified_to_standard_format(result, minimal_data)
    print(f"Minimal data fields: {len(converted.get('enhanced_data_with_context', []))}")
    
    # Test 4: Data that might cause LLM to fail
    print("\n4. Testing data that might cause LLM issues:")
    problematic_data = {
        "document_text": ["???", "###", ""],
        "tables": [{"page": 1, "rows": []}],
        "key_values": []
    }
    result = process_structured_data_with_llm_unified(problematic_data)
    converted = convert_unified_to_standard_format(result, problematic_data)
    print(f"Problematic data fields: {len(converted.get('enhanced_data_with_context', []))}")
    
    # Test 5: Check what happens when LLM returns unexpected format
    print("\n5. Testing conversion with no fields:")
    no_fields_result = {"fields": {}}
    converted = convert_unified_to_standard_format(no_fields_result, {})
    print(f"No fields conversion result: {converted}")
    print(f"Enhanced data length: {len(converted.get('enhanced_data_with_context', []))}")

def test_streaming_scenario():
    """Test the streaming scenario that might be causing the issue"""
    
    print("\n6. Testing streaming scenario:")
    
    # Simulate what happens in process_stream
    data = {
        "document_text": ["Test document"],
        "tables": [],
        "key_values": []
    }
    
    # Simulate the unified extraction
    unified_result = process_structured_data_with_llm_unified(data)
    result = convert_unified_to_standard_format(unified_result, data)
    
    print(f"Streaming test - Enhanced data: {len(result.get('enhanced_data_with_context', []))}")
    
    # Check if enhanced_data_with_context exists and has content
    if 'enhanced_data_with_context' in result and result['enhanced_data_with_context']:
        print("✅ Enhanced data exists and has content")
        for i, row in enumerate(result['enhanced_data_with_context'][:3]):
            print(f"  Row {i+1}: {row['field']} = {row['value']}")
    else:
        print("❌ No enhanced data - this would cause fallback to legacy processing")
        print(f"Result keys: {list(result.keys())}")
        
        # This is what would happen in the streaming code
        print("Would fall back to legacy processing, but in unified mode this fails")

if __name__ == "__main__":
    test_empty_or_minimal_data()
    test_streaming_scenario()