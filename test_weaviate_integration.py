#!/usr/bin/env python3
"""
Test script for Weaviate + LLM context enhancement integration
"""

import json
import time
from weaviate_context_processor import WeaviateContextProcessor, test_weaviate_setup
from structured_llm_processor import process_structured_data_with_llm

def test_full_integration():
    """Test the complete integration with sample data"""
    
    print("=" * 60)
    print("TESTING WEAVIATE + LLM CONTEXT ENHANCEMENT INTEGRATION")
    print("=" * 60)
    
    # Step 1: Test Weaviate setup
    print("\n1. Testing Weaviate Setup...")
    if not test_weaviate_setup():
        print("X Weaviate setup failed. Make sure Docker is running and Weaviate is accessible.")
        return False
    print("OK Weaviate setup successful")
    
    # Step 2: Create sample structured data (simulating Textract output)
    print("\n2. Creating sample structured data...")
    
    sample_structured_data = {
        "document_text": [
            "Life360 Inc. Financial Results for Q4 2023",
            "Revenue Performance: Total revenue grew by 33% year-on-year reaching USD 115.5 million for Q4 2023.",
            "The strong revenue growth was driven by increased Monthly Active Users (MAU) reaching 65.8 million globally.",
            "Net profit after tax increased significantly to USD 12.3 million compared to USD 8.1 million in Q4 2022.",
            "Operating expenses were well controlled at USD 89.2 million, representing an improvement in operational efficiency.",
            "The company's gross margin improved to 78% from 74% in the previous year.",
            "Cash and cash equivalents at the end of Q4 2023 were USD 45.7 million.",
            "Monthly Active Users (MAU) growth of 15% demonstrates strong user engagement and platform adoption.",
            "The company expects continued growth momentum into 2024 with projected revenue growth of 25-30%.",
            "Life360's family safety platform continues to gain market share in the competitive location services market."
        ],
        "tables": [
            {
                "page": 1,
                "rows": [
                    ["Metric", "Q4 2023", "Q4 2022", "Growth"],
                    ["Revenue (USD M)", "115.5", "86.8", "33%"],
                    ["MAU (Millions)", "65.8", "57.2", "15%"],
                    ["Net Profit (USD M)", "12.3", "8.1", "52%"],
                    ["Gross Margin", "78%", "74%", "4pp"]
                ]
            }
        ],
        "key_values": [
            {"key": "Company", "value": "Life360 Inc.", "page": 1},
            {"key": "Period", "value": "Q4 2023", "page": 1},
            {"key": "Cash Position", "value": "USD 45.7M", "page": 1}
        ]
    }
    
    print("OK Sample data created")
    
    # Step 3: Process with the enhanced pipeline
    print("\n3. Processing with enhanced pipeline (LLM + Weaviate)...")
    start_time = time.time()
    
    try:
        results = process_structured_data_with_llm(sample_structured_data)
        processing_time = time.time() - start_time
        
        print(f"OK Processing completed in {processing_time:.2f} seconds")
        
        # Step 4: Display results
        print("\n4. Results Analysis:")
        print("-" * 40)
        
        # Check if Weaviate enhancement was successful
        weaviate_status = results.get("weaviate_enhancement", {})
        if weaviate_status.get("enhancement_completed"):
            print(f"OK Weaviate Enhancement: SUCCESS")
            print(f"   Document ID: {weaviate_status.get('document_id')}")
            print(f"   Chunks Stored: {weaviate_status.get('chunks_stored')}")
        else:
            print(f"X Weaviate Enhancement: FAILED")
            print(f"   Error: {weaviate_status.get('error', 'Unknown error')}")
            return False
        
        # Display enhanced table results
        print("\nTable Results:")
        for i, table in enumerate(results.get("processed_tables", [])):
            print(f"\nTable {i+1}:")
            
            # Original extracted fields
            structured_table = table.get("structured_table", {})
            print("  Extracted Fields:")
            for field, value in structured_table.items():
                if field != "error":
                    print(f"    {field}: {value}")
            
            # Polished contexts
            polished_contexts = table.get("polished_context", {})
            if polished_contexts:
                print("  Polished Contexts:")
                for field, context in polished_contexts.items():
                    print(f"    {field}: {context}")
            else:
                print("  Warning: No polished contexts generated")
        
        # Display enhanced key-value results
        print("\nKey-Value Results:")
        kv_results = results.get("processed_key_values", {})
        if kv_results:
            structured_kvs = kv_results.get("structured_key_values", {})
            polished_contexts = kv_results.get("polished_context", {})
            
            print("  Extracted Fields:")
            for field, value in structured_kvs.items():
                if field != "error":
                    print(f"    {field}: {value}")
            
            if polished_contexts:
                print("  Polished Contexts:")
                for field, context in polished_contexts.items():
                    print(f"    {field}: {context}")
        
        print("\n" + "=" * 60)
        print("OK INTEGRATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"X Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Weaviate + LLM Context Enhancement Tests...")
    
    # Test integration
    success = test_full_integration()
    
    if success:
        print("\nAll tests passed! The Weaviate + LLM enhancement is working correctly.")
        print("\nNext steps:")
        print("1. Use your existing document processing code")
        print("2. Results will now include 'polished_context' fields")
        print("3. Check the enhancement status in results['weaviate_enhancement']")
    else:
        print("\nTests failed. Please check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Ensure Docker is running")
        print("2. Start Weaviate: docker-compose up -d")
        print("3. Check your OpenAI API key in .env file")
        print("4. Verify network connectivity to Weaviate (localhost:8080)")