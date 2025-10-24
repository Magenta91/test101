#!/usr/bin/env python3
"""
Test comprehensive extraction with realistic financial document data
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_comprehensive_extraction():
    """Test with comprehensive financial document data similar to what produced 73 fields"""
    
    # Create comprehensive test data based on the original 73-field extraction
    comprehensive_data = {
        "document_text": [
            "AUB Group Limited Half Year Financial Results 1HFY23",
            "CEO Mike Emmett announces strong performance for the period ended 31 December 2022",
            "Underlying NPAT of AUD 46.7mn (1HFY22: AUD 30.6mn) represents 53% growth",
            "Underlying earnings per share of 48.18 cents per share (1HFY22: 40.30 cents)",
            "Reported Net Profit After Tax of AUD 0.4mn (1HFY22: AUD 29.7mn) was impacted by acquisition costs",
            "Fully franked interim dividend of 17.0 cents per share maintained (1HFY22: 17.0 cents per share)",
            "Record date: 3 March 2023, Payment date: 17 March 2023",
            "Dividend Reinvestment Plan remains suspended",
            "Tysers acquisition completed on 1 October 2022 for GBP 102.5 million",
            "Tysers contributed 3 months profit and revenue exceeded expectations",
            "Australian Broking underlying pre-tax profit increased 30.3% to AUD 49.9mn (1HFY22: AUD 38.3mn)",
            "Australian Broking EBIT Margin of 35.2% up 410bps from 1HFY22",
            "Agencies underlying pre-tax profit increased 38.4% to AUD 12.3mn (1HFY22: AUD 8.9mn)",
            "Agencies EBIT margin of 31.6%. Excluding profit commission, EBIT margin was 30.3%",
            "BizCover underlying pre-tax profit increased 15.2% to AUD 4.8mn (1HFY22: AUD 4.2mn)",
            "New Zealand underlying pre-tax profit of AUD 2.1mn (1HFY22: AUD 1.8mn)",
            "Technology investment of AUD 3.2mn in New Zealand operations",
            "FY23 Underlying NPAT guidance upgraded to AUD 112.9mn to AUD 118.4mn (previously AUD 105mn to AUD 115mn)",
            "Strong performance driven by growth in BizCover and successful Tysers integration",
            "Cash and undrawn debt facilities of AUD 89.2mn at 31 December 2022",
            "Net debt to EBITDA leverage ratio of 1.8x at 31 December 2022",
            "Capital management leverage ratio target of 1.5x to 2.5x maintained",
            "The Board anticipates that the FY23 dividend payout ratio will be within 50% to 70% of Underlying NPAT",
            "Strata Unit Underwriters business continues to perform well",
            "Mike Emmett, CEO: 'We are pleased with the strong performance across all business segments'",
            "The acquisition of Tysers has strengthened our UK presence significantly",
            "Integration of Tysers proceeding ahead of schedule with identified synergies being realized",
            "Market conditions remain favorable for continued growth",
            "Regulatory environment stable with no significant changes expected",
            "Employee headcount increased to 2,847 following Tysers acquisition",
            "Office locations expanded to 95 locations globally including UK operations"
        ],
        "tables": [
            {
                "page": 1,
                "rows": [
                    ["Metric", "1HFY23", "1HFY22", "Change"],
                    ["Underlying NPAT", "AUD 46.7mn", "AUD 30.6mn", "53%"],
                    ["Underlying EPS", "48.18 cents", "40.30 cents", "19.5%"],
                    ["Reported NPAT", "AUD 0.4mn", "AUD 29.7mn", "-98.7%"],
                    ["Interim Dividend", "17.0 cents", "17.0 cents", "0%"],
                    ["Australian Broking Profit", "AUD 49.9mn", "AUD 38.3mn", "30.3%"],
                    ["Australian Broking EBIT Margin", "35.2%", "31.1%", "410bps"],
                    ["Agencies Profit", "AUD 12.3mn", "AUD 8.9mn", "38.4%"],
                    ["Agencies EBIT Margin", "31.6%", "28.2%", "340bps"],
                    ["BizCover Profit", "AUD 4.8mn", "AUD 4.2mn", "15.2%"],
                    ["New Zealand Profit", "AUD 2.1mn", "AUD 1.8mn", "16.7%"]
                ]
            },
            {
                "page": 2,
                "rows": [
                    ["Business Segment", "Revenue 1HFY23", "Revenue 1HFY22", "Growth"],
                    ["Australian Broking", "AUD 141.8mn", "AUD 123.2mn", "15.1%"],
                    ["Agencies", "AUD 38.9mn", "AUD 31.6mn", "23.1%"],
                    ["BizCover", "AUD 31.2mn", "AUD 27.1mn", "15.1%"],
                    ["New Zealand", "AUD 13.4mn", "AUD 10.8mn", "24.1%"],
                    ["Tysers (3 months)", "AUD 28.5mn", "N/A", "N/A"]
                ]
            },
            {
                "page": 3,
                "rows": [
                    ["Capital Management", "31 Dec 2022", "30 Jun 2022", "Change"],
                    ["Cash and Undrawn Facilities", "AUD 89.2mn", "AUD 95.4mn", "-6.5%"],
                    ["Net Debt", "AUD 156.8mn", "AUD 45.2mn", "247%"],
                    ["Net Debt to EBITDA", "1.8x", "0.5x", "1.3x"],
                    ["Leverage Ratio Target", "1.5x to 2.5x", "1.5x to 2.5x", "Unchanged"]
                ]
            }
        ],
        "key_values": [
            {"key": "Company Name", "value": "AUB Group Limited"},
            {"key": "Period", "value": "1HFY23"},
            {"key": "CEO", "value": "Mike Emmett"},
            {"key": "Report Date", "value": "February 2023"},
            {"key": "ASX Code", "value": "AUB"},
            {"key": "Headquarters", "value": "Sydney, Australia"},
            {"key": "Acquisition Date", "value": "1 October 2022"},
            {"key": "Acquisition Entity", "value": "Tysers"},
            {"key": "Acquisition Price", "value": "GBP 102.5 million"},
            {"key": "Dividend Record Date", "value": "3 March 2023"},
            {"key": "Dividend Payment Date", "value": "17 March 2023"},
            {"key": "Employee Count", "value": "2,847"},
            {"key": "Office Locations", "value": "95 locations"},
            {"key": "FY23 Guidance Lower", "value": "AUD 112.9mn"},
            {"key": "FY23 Guidance Upper", "value": "AUD 118.4mn"},
            {"key": "Previous Guidance Lower", "value": "AUD 105mn"},
            {"key": "Previous Guidance Upper", "value": "AUD 115mn"},
            {"key": "Dividend Payout Ratio Target", "value": "50% to 70%"},
            {"key": "DRP Status", "value": "Suspended"},
            {"key": "Leverage Target Lower", "value": "1.5x"},
            {"key": "Leverage Target Upper", "value": "2.5x"}
        ]
    }
    
    print("Testing Comprehensive Extraction (targeting 70+ fields)...")
    print("=" * 60)
    
    # Test unified extraction
    unified_result = process_structured_data_with_llm_unified(comprehensive_data)
    
    print("Raw unified result:")
    fields = unified_result.get("fields", {})
    print(f"Extracted {len(fields)} fields")
    
    # Convert to standard format
    standard_format = convert_unified_to_standard_format(unified_result, comprehensive_data)
    
    # Analyze results
    enhanced_data = standard_format.get("enhanced_data_with_context", [])
    print(f"\nConverted to standard format: {len(enhanced_data)} fields")
    
    # Show field breakdown
    fields_with_context = [item for item in enhanced_data if item.get('has_context', False)]
    print(f"Fields with context: {len(fields_with_context)}")
    
    # Display sample results
    print("\nSample extracted fields:")
    for i, item in enumerate(enhanced_data[:15]):
        field = item.get('field', 'N/A')[:40]
        value = str(item.get('value', 'N/A'))[:20]
        context = str(item.get('context', ''))[:60]
        print(f"{i+1:2d}. {field:40} | {value:20} | {context}...")
    
    # Compare with target
    target_fields = 70
    actual_fields = len(enhanced_data)
    print(f"\nComparison:")
    print(f"Target fields: {target_fields}")
    print(f"Actual fields: {actual_fields}")
    print(f"Achievement: {actual_fields/target_fields*100:.1f}%")
    
    if actual_fields >= target_fields:
        print("✅ SUCCESS: Achieved target field count!")
    else:
        print(f"❌ SHORTFALL: Missing {target_fields - actual_fields} fields")
    
    return unified_result, standard_format

if __name__ == "__main__":
    print("Comprehensive Extraction Test")
    print("=" * 60)
    
    try:
        unified_result, standard_format = test_comprehensive_extraction()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()