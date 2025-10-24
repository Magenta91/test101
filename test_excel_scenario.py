#!/usr/bin/env python3
"""
Test to reproduce the exact scenario that created the Excel file with "Value found in document" context
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_excel_scenario():
    """Test with data that matches the Excel file values"""
    
    # Create test data based on the Excel file values
    test_data = {
        "document_text": [
            "Life360 Inc. Financial Results",
            "Revenue of AUD 46.7mn for the period.",
            "Underlying earnings per share of 48.18 cents.",
            "Operating expenses of AUD 0.4mn.",
            "Dividend of 17.0 cents per share declared.",
            "Growth rate of 12% achieved.",
            "EBIT of AUD 18.0mn recorded.",
            "Total revenue of AUD 49.9mn.",
            "EBIT Margin of 35.2% up 410bps.",
            "Net profit of AUD 12.3mn.",
            "EBIT margin of 31.6%.",
            "Underlying pre-tax profit increased by 34.6% to AUD 4.8mn.",
            "Strata Unit Underwriters business unit.",
            "Performance metrics at 38.4%.",
            "Efficiency ratio at 15.2%.",
            "Market share at 38.0%.",
            "Operating margin at 30.3%."
        ],
        "tables": [],
        "key_values": []
    }
    
    print("Testing Excel scenario...")
    print("=" * 50)
    
    # Test unified extraction
    unified_result = process_structured_data_with_llm_unified(test_data)
    
    print("Raw unified result (first 3 fields):")
    fields = unified_result.get("fields", {})
    for i, (field_name, field_data) in enumerate(list(fields.items())[:3]):
        print(f"  {field_name}: {field_data}")
    
    # Convert to standard format
    standard_format = convert_unified_to_standard_format(unified_result, test_data)
    
    # Check for the problematic context
    enhanced_data = standard_format.get("enhanced_data_with_context", [])
    print(f"\nFound {len(enhanced_data)} fields")
    
    problematic_count = 0
    good_context_count = 0
    
    for item in enhanced_data:
        context = item.get('context', '')
        if "Value found in document" in context:
            problematic_count += 1
            print(f"❌ PROBLEMATIC: {item.get('field', 'N/A')} -> {context}")
        elif context and len(context) > 10:
            good_context_count += 1
    
    print(f"\nSummary:")
    print(f"  Good context: {good_context_count}")
    print(f"  Problematic context: {problematic_count}")
    print(f"  Empty context: {len(enhanced_data) - good_context_count - problematic_count}")
    
    if problematic_count == 0:
        print("✅ No 'Value found in document' context found - issue might be elsewhere")
    else:
        print("❌ Found the problematic context pattern")
    
    return unified_result, standard_format

if __name__ == "__main__":
    print("Testing Excel Scenario")
    print("=" * 60)
    
    try:
        unified_result, standard_format = test_excel_scenario()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()