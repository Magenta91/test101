#!/usr/bin/env python3
"""
Test context quality for specific fields
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from textract_processor import extract_structured_data_from_pdf_bytes
from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_context_quality():
    """Test context quality for the AUB PDF"""
    
    pdf_path = "AUB_1H23_Results_-_Performance_Overview.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("Testing Context Quality...")
    print("=" * 60)
    
    try:
        # Extract and process
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        structured_data = extract_structured_data_from_pdf_bytes(pdf_bytes)
        unified_result = process_structured_data_with_llm_unified(structured_data)
        standard_format = convert_unified_to_standard_format(unified_result, structured_data)
        
        enhanced_data = standard_format.get("enhanced_data_with_context", [])
        
        print(f"Extracted {len(enhanced_data)} fields")
        print("\nContext Quality Analysis:")
        print("=" * 60)
        
        # Focus on the problematic fields mentioned
        target_fields = ["Reported_NPAT_1HFY23", "Reported_NPAT_1HFY22"]
        
        for item in enhanced_data:
            field = item.get('field', '')
            value = item.get('value', '')
            context = item.get('context', '')
            
            # Show all fields for analysis, but highlight target fields
            is_target = any(target in field for target in target_fields)
            marker = "🎯" if is_target else "  "
            
            print(f"{marker} {field[:40]:40} | {str(value)[:15]:15} | {context[:80]}...")
            
            # Detailed analysis for target fields
            if is_target:
                print(f"     VALUE: {value}")
                print(f"     CONTEXT: {context}")
                
                # Check if context properly relates to value
                value_clean = str(value).replace("AUD ", "").replace("mn", "").strip()
                if value_clean in context:
                    print(f"     ✅ Context contains value: {value_clean}")
                else:
                    print(f"     ❌ Context missing value: {value_clean}")
                print()
        
        # Summary
        fields_with_good_context = 0
        fields_with_poor_context = 0
        
        for item in enhanced_data:
            context = item.get('context', '')
            value = str(item.get('value', ''))
            
            # Simple quality check
            if len(context) > 20 and (value.replace("AUD ", "").replace("mn", "").replace("cents", "").strip() in context or 
                                     "LINE" in context or "Table" in context or "Field" in context):
                fields_with_good_context += 1
            else:
                fields_with_poor_context += 1
        
        print(f"\nContext Quality Summary:")
        print(f"Fields with good context: {fields_with_good_context}")
        print(f"Fields with poor context: {fields_with_poor_context}")
        print(f"Context quality: {fields_with_good_context/(fields_with_good_context+fields_with_poor_context)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_quality()