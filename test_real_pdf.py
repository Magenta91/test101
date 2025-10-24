#!/usr/bin/env python3
"""
Test the real PDF file that produced the original vs current outputs
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from textract_processor import extract_structured_data_from_pdf_bytes
from structured_llm_processor import process_structured_data_with_llm_unified
from app import convert_unified_to_standard_format

def test_real_pdf():
    """Test with the actual AUB PDF file"""
    
    pdf_path = "AUB_1H23_Results_-_Performance_Overview.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None, None
    
    print("Testing Real PDF File...")
    print("=" * 60)
    print(f"Processing: {pdf_path}")
    
    try:
        # Extract structured data from PDF using Textract
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print("Extracting structured data with Textract...")
        structured_data = extract_structured_data_from_pdf_bytes(pdf_bytes)
        
        # Show what we extracted from Textract
        print(f"Textract extraction results:")
        print(f"  Document text lines: {len(structured_data.get('document_text', []))}")
        print(f"  Tables: {len(structured_data.get('tables', []))}")
        print(f"  Key-value pairs: {len(structured_data.get('key_values', []))}")
        
        # Show sample content
        doc_text = structured_data.get('document_text', [])
        if doc_text:
            print(f"\nSample document text (first 5 lines):")
            for i, line in enumerate(doc_text[:5]):
                print(f"  {i+1}. {line[:80]}...")
        
        tables = structured_data.get('tables', [])
        if tables:
            print(f"\nSample table data:")
            for i, table in enumerate(tables[:2]):
                print(f"  Table {i+1} (Page {table.get('page', 'N/A')}): {len(table.get('rows', []))} rows")
                if table.get('rows'):
                    print(f"    First row: {table['rows'][0]}")
        
        key_values = structured_data.get('key_values', [])
        if key_values:
            print(f"\nSample key-value pairs:")
            for i, kv in enumerate(key_values[:5]):
                print(f"  {i+1}. {kv.get('key', 'N/A')}: {kv.get('value', 'N/A')}")
        
        # Process with unified extraction
        print(f"\nProcessing with unified extraction...")
        unified_result = process_structured_data_with_llm_unified(structured_data)
        
        fields = unified_result.get("fields", {})
        print(f"Unified extraction: {len(fields)} fields extracted")
        
        # Convert to standard format
        standard_format = convert_unified_to_standard_format(unified_result, structured_data)
        
        # Analyze results
        enhanced_data = standard_format.get("enhanced_data_with_context", [])
        print(f"Standard format: {len(enhanced_data)} fields")
        
        # Show field breakdown
        fields_with_context = [item for item in enhanced_data if item.get('has_context', False)]
        print(f"Fields with context: {len(fields_with_context)}")
        
        # Compare with expected results
        print(f"\nComparison with previous results:")
        print(f"Original output: 73 fields")
        print(f"Current output: {len(enhanced_data)} fields")
        print(f"Difference: {73 - len(enhanced_data)} fewer fields")
        
        if len(enhanced_data) >= 60:
            print("✅ GOOD: Achieved reasonable field count")
        elif len(enhanced_data) >= 40:
            print("⚠️  MODERATE: Decent field count but could be better")
        else:
            print("❌ LOW: Significantly fewer fields than expected")
        
        # Display sample results
        print(f"\nSample extracted fields:")
        for i, item in enumerate(enhanced_data[:20]):
            field = item.get('field', 'N/A')[:35]
            value = str(item.get('value', 'N/A'))[:15]
            context = str(item.get('context', ''))[:50]
            print(f"{i+1:2d}. {field:35} | {value:15} | {context}...")
        
        # Show cost
        cost_summary = standard_format.get('cost_summary', {})
        if cost_summary:
            total_cost = cost_summary.get('total_cost_usd', 0)
            print(f"\nProcessing cost: ${total_cost:.6f}")
        
        return unified_result, standard_format
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("Real PDF Test")
    print("=" * 60)
    
    unified_result, standard_format = test_real_pdf()
    
    if unified_result and standard_format:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed!")