#!/usr/bin/env python3
"""
Test script to compare different context enhancement modes for speed
"""

import time
import os
from structured_llm_processor import process_structured_data_with_llm
from context_config import set_context_mode, MODE_DESCRIPTIONS

def create_sample_data():
    """Create sample data for testing"""
    return {
        "document_text": [
            "Life360 Inc. Financial Results for Q4 2023",
            "Revenue Performance: Total revenue grew by 33% year-on-year reaching USD 115.5 million for Q4 2023.",
            "The strong revenue growth was driven by increased Monthly Active Users (MAU) reaching 65.8 million globally.",
            "Net profit after tax increased significantly to USD 12.3 million compared to USD 8.1 million in Q4 2022.",
            "Operating expenses were well controlled at USD 89.2 million, representing an improvement in operational efficiency.",
            "The company's gross margin improved to 78% from 74% in the previous year.",
            "Cash and cash equivalents at the end of Q4 2023 were USD 45.7 million."
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

def test_mode(mode_name: str, sample_data: dict):
    """Test a specific mode and return timing results"""
    print(f"\n{'='*50}")
    print(f"TESTING MODE: {mode_name.upper()}")
    print(f"Description: {MODE_DESCRIPTIONS[mode_name]}")
    print(f"{'='*50}")
    
    # Set the mode
    set_context_mode(mode_name)
    
    # Run the test
    start_time = time.time()
    
    try:
        results = process_structured_data_with_llm(sample_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Check results
        enhancement_status = results.get("weaviate_enhancement", {})
        enhancement_completed = enhancement_status.get("enhancement_completed", False)
        
        # Count polished contexts
        polished_count = 0
        tables = results.get("processed_tables", [])
        if tables and "polished_context" in tables[0]:
            polished_count += len(tables[0]["polished_context"])
        
        kv_results = results.get("processed_key_values", {})
        if "polished_context" in kv_results:
            polished_count += len(kv_results["polished_context"])
        
        print(f"✅ SUCCESS")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Enhancement Completed: {enhancement_completed}")
        print(f"   Polished Contexts: {polished_count}")
        print(f"   Mode: {enhancement_status.get('mode', 'unknown')}")
        
        if polished_count > 0:
            print(f"   Sample Context: {list(tables[0]['polished_context'].values())[0][:100]}...")
        
        return {
            "mode": mode_name,
            "success": True,
            "time": processing_time,
            "enhancement_completed": enhancement_completed,
            "polished_count": polished_count
        }
        
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"❌ FAILED")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Error: {e}")
        
        return {
            "mode": mode_name,
            "success": False,
            "time": processing_time,
            "error": str(e)
        }

def main():
    """Run speed comparison tests"""
    print("🚀 CONTEXT ENHANCEMENT SPEED COMPARISON")
    print("=" * 60)
    
    # Create sample data
    sample_data = create_sample_data()
    
    # Test modes in order of speed (fastest first)
    modes_to_test = ["off", "fast", "optimized"]
    
    results = []
    
    for mode in modes_to_test:
        result = test_mode(mode, sample_data)
        results.append(result)
        
        # Small delay between tests
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SPEED COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    print(f"{'Mode':<12} {'Time':<8} {'Status':<8} {'Contexts':<10} {'Description'}")
    print("-" * 60)
    
    for result in results:
        mode = result["mode"]
        time_str = f"{result['time']:.1f}s"
        status = "✅" if result["success"] else "❌"
        contexts = result.get("polished_count", 0) if result["success"] else "N/A"
        description = MODE_DESCRIPTIONS[mode].split(" - ")[0][:25]
        
        print(f"{mode:<12} {time_str:<8} {status:<8} {contexts:<10} {description}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("- Use 'fast' mode for quick processing (3-5 important fields)")
    print("- Use 'optimized' mode for balanced speed/quality")
    print("- Use 'off' mode when you don't need context enhancement")
    print("\n🔧 TO SET MODE:")
    print("- Environment variable: export CONTEXT_MODE=fast")
    print("- Or in code: from context_config import set_context_mode; set_context_mode('fast')")

if __name__ == "__main__":
    main()