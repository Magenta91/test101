#!/usr/bin/env python3
"""
Debug script to identify why context is showing "Value found in document" instead of meaningful context
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_with_real_data():
    """Test with data that might cause the context issue"""
    
    # Create test data that might trigger the issue
    test_data = {
        "document_text": [
            "Life360 Inc. Financial Results for Q4 2023",
            "Revenue of AUD 46.7mn represents strong growth in the quarter.",
            "Underlying earnings per share of 48.18 cents shows improvement.",
            "Operating expenses were AUD 0.4mn for the period.",
            "Dividend declared at 17.0 cents per share for shareholders.",
            "Growth rate of 12% exceeded expectations for the year.",
            "EBIT of AUD 18.0mn demonstrates operational efficiency.",
            "Total revenue reached AUD 49.9mn for the full year.",
            "EBIT Margin of 35.2% up 410bps from 1HFY22.",
            "Net profit of AUD 12.3mn shows strong performance.",
            "EBIT margin of 31.6%. Excluding profit commission."
        ],
        "tables": [
            {
                "page": 1,
                "rows": [
                    ["Metric", "Q4 2023", "Q4 2022", "Change"],
                    ["Revenue", "AUD 46.7mn", "AUD 42.1mn", "11%"],
                    ["EPS", "48.18 cents", "41.2 cents", "17%"],
                    ["EBIT", "AUD 18.0mn", "AUD 15.2mn", "18%"]
                ]
            }
        ],
        "key_values": [
            {"key": "Company", "value": "Life360 Inc."},
            {"key": "Period", "value": "Q4 2023"},
            {"key": "Currency", "value": "AUD"}
        ]
    }
    
    print("Testing unified extraction with real-like data...")
    print("=" * 60)
    
    # Test unified extraction
    unified_result = process_structured_data_with_llm_unified(test_data)
    
    print("Raw unified result:")
    print(json.dumps(unified_result, indent=2))
    
    # Convert to standard format
    standard_format = convert_unified_to_standard_format(unified_result, test_data)
    
    print("\nConverted to standard format:")
    print(json.dumps(standard_format, indent=2))
    
    # Check for the problematic context
    enhanced_data = standard_format.get("enhanced_data_with_context", [])
    print(f"\nFound {len(enhanced_data)} fields")
    
    for i, item in enumerate(enhanced_data[:5]):
        context = item.get('context', '')
        print(f"\nField {i+1}: {item.get('field', 'N/A')}")
        print(f"  Value: {item.get('value', 'N/A')}")
        print(f"  Context: {context}")
        
        if "Value found in document" in context:
            print("  ❌ FOUND THE ISSUE: Context contains 'Value found in document'")
        elif context and len(context) > 10:
            print("  ✅ Context looks good")
        else:
            print("  ⚠️  Context is empty or too short")
    
    return unified_result, standard_format

if __name__ == "__main__":
    print("Debugging Context Issue")
    print("=" * 60)
    
    try:
        unified_result, standard_format = test_with_real_data()
        
        print("\n" + "=" * 60)
        print("Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()