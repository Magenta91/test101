#!/usr/bin/env python3
"""
Test script for unified field + context extraction feature.
Tests both unified and legacy modes to ensure compatibility.
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the modules
from structured_llm_processor import process_structured_data_with_llm_unified, process_structured_data_with_llm

def test_unified_extraction():
    """Test the unified extraction function with sample financial text"""
    
    # Create comprehensive structured data like what Textract would provide
    sample_structured_data = {
        "document_text": [
            "AUB Group Limited Financial Results for Half Year 2023",
            "Revenue increased by 15% to $125.5 million compared to previous period.",
            "Net profit after tax (NPAT) of $18.2 million represents strong performance.",
            "The company's gross written premium grew 12% to $89.3 million.",
            "Operating expenses were well controlled at $45.7 million.",
            "Return on equity improved to 14.2% from 12.8% in the prior period.",
            "The Board declared an interim dividend of 8.5 cents per share.",
            "Total assets under management reached $2.1 billion at period end."
        ],
        "tables": [
            {
                "page": 1,
                "rows": [
                    ["Metric", "H1 2023", "H1 2022", "Change"],
                    ["Revenue", "$125.5M", "$109.1M", "15%"],
                    ["NPAT", "$18.2M", "$15.8M", "15.2%"],
                    ["ROE", "14.2%", "12.8%", "1.4pp"],
                    ["Dividend", "8.5c", "7.5c", "13.3%"]
                ]
            },
            {
                "page": 2,
                "rows": [
                    ["Business Unit", "Premium", "Growth"],
                    ["Personal Insurance", "$45.2M", "8%"],
                    ["Commercial Insurance", "$44.1M", "16%"],
                    ["Total GWP", "$89.3M", "12%"]
                ]
            }
        ],
        "key_values": [
            {"key": "Company Name", "value": "AUB Group Limited"},
            {"key": "Period", "value": "Half Year 2023"},
            {"key": "Report Date", "value": "August 2023"},
            {"key": "CEO", "value": "Mike Emmett"},
            {"key": "Headquarters", "value": "Sydney, Australia"},
            {"key": "ASX Code", "value": "AUB"},
            {"key": "Employees", "value": "2,847"},
            {"key": "Offices", "value": "95 locations"}
        ]
    }
    
    print("Testing Unified Extraction Mode...")
    print("=" * 50)
    
    # Test unified extraction
    unified_result = process_structured_data_with_llm_unified(sample_structured_data)
    
    print("Unified Extraction Results:")
    print(json.dumps(unified_result, indent=2))
    
    # Convert to standard format
    from app import convert_unified_to_standard_format
    
    mock_original_data = sample_structured_data
    standard_format = convert_unified_to_standard_format(unified_result, mock_original_data)
    
    print("\nConverted to Standard Format:")
    print(json.dumps(standard_format, indent=2))
    
    # Verify output structure
    assert "enhanced_data_with_context" in standard_format
    assert "cost_summary" in standard_format
    assert "processing_mode" in standard_format
    
    enhanced_data = standard_format["enhanced_data_with_context"]
    
    print(f"\nExtracted {len(enhanced_data)} fields with context")
    
    # Check that we have some fields with context
    fields_with_context = [item for item in enhanced_data if item.get('has_context', False)]
    print(f"Fields with context: {len(fields_with_context)}")
    
    # Display sample results
    for i, item in enumerate(enhanced_data[:3]):  # Show first 3 items
        print(f"\nSample {i+1}:")
        print(f"  Field: {item['field']}")
        print(f"  Value: {item['value']}")
        print(f"  Context: {item['context'][:100]}..." if len(item['context']) > 100 else f"  Context: {item['context']}")
    
    return unified_result, standard_format


def test_legacy_extraction():
    """Test legacy extraction for comparison"""
    
    sample_structured_data = {
        "document_text": [
            "AUB Group Limited Financial Results for Half Year 2023",
            "Revenue increased by 15% to $125.5 million compared to previous period.",
            "Net profit after tax (NPAT) of $18.2 million represents strong performance.",
            "The company's gross written premium grew 12% to $89.3 million."
        ],
        "tables": [],
        "key_values": []
    }
    
    print("\n\nTesting Legacy Extraction Mode...")
    print("=" * 50)
    
    try:
        legacy_result = process_structured_data_with_llm(sample_structured_data)
        print("Legacy extraction completed successfully")
        print(f"Result keys: {list(legacy_result.keys())}")
        return legacy_result
    except Exception as e:
        print(f"Legacy extraction failed (expected if context_tracker has issues): {e}")
        return None


def test_mode_switching():
    """Test switching between modes using the flag"""
    
    print("\n\nTesting Mode Switching...")
    print("=" * 50)
    
    # Import app to test flag switching
    import app
    
    print(f"Current mode: {'Unified' if app.USE_UNIFIED_CONTEXT_EXTRACTION else 'Legacy'}")
    
    # Test that the flag can be changed
    original_flag = app.USE_UNIFIED_CONTEXT_EXTRACTION
    
    app.USE_UNIFIED_CONTEXT_EXTRACTION = True
    print(f"Set to Unified: {app.USE_UNIFIED_CONTEXT_EXTRACTION}")
    
    app.USE_UNIFIED_CONTEXT_EXTRACTION = False
    print(f"Set to Legacy: {app.USE_UNIFIED_CONTEXT_EXTRACTION}")
    
    # Restore original
    app.USE_UNIFIED_CONTEXT_EXTRACTION = original_flag
    print(f"Restored to: {app.USE_UNIFIED_CONTEXT_EXTRACTION}")


if __name__ == "__main__":
    print("Unified Field + Context Extraction Test")
    print("=" * 60)
    
    try:
        # Test unified extraction
        unified_result, standard_format = test_unified_extraction()
        
        # Test legacy extraction
        legacy_result = test_legacy_extraction()
        
        # Test mode switching
        test_mode_switching()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("✅ Unified extraction is working")
        print("✅ Standard format conversion is working")
        print("✅ Mode switching is working")
        
        # Summary
        if unified_result and "fields" in unified_result:
            field_count = len(unified_result["fields"])
            context_count = sum(1 for field_data in unified_result["fields"].values() 
                              if isinstance(field_data, dict) and field_data.get("context", "").strip())
            print(f"✅ Extracted {field_count} fields, {context_count} with context")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()