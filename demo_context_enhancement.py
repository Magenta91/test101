#!/usr/bin/env python3
"""
Demonstration script showing the enhancement from basic extraction to context-enriched extraction.
This shows the before/after comparison of the Context column population with the new fuzzy matching system.
"""

import json
from context_tracker import integrate_context_tracking

def demo_context_enhancement():
    """Demonstrate the enhanced context tracking with comprehensive fuzzy matching"""
    
    print("=" * 90)
    print("ENHANCED CONTEXT TRACKING DEMONSTRATION")
    print("Fuzzy Matching + Relevance Scoring + Original Wording Preservation")
    print("=" * 90)
    print()
    
    # Realistic financial document text with varied terminology
    document_text = [
        "Life360, Inc. (NASDAQ: LIF) is the world's largest family safety platform.",
        "The company serves families through location sharing, driving safety, and digital tools.",
        "Financial Performance: Life360 reported record quarterly revenue of $115.5 million for Q4 2024.",
        "This represents a 33% increase compared to the same period last year.",
        "The strong performance was driven by user growth and increased engagement.",
        "John Smith, Chief Executive Officer, commented on the exceptional results:",
        "'We are pleased with our continued growth trajectory and market leadership.'",
        "Our platform now serves over 65.8 million monthly active users globally.",
        "Life360 has captured approximately 12% market share in family safety applications.",
        "The company's stock (LIF) has performed well, gaining 25% year-to-date.",
        "John Smith emphasized Life360's commitment to innovation and expansion.",
        "The company plans to introduce new features and expand into additional markets.",
        "Life360's revenue growth outpaced industry averages by significant margins.",
        "Monthly active users increased by 18% compared to the previous quarter.",
        "The NASDAQ-listed company continues to strengthen its market position.",
        "Family safety remains the core focus of Life360's business strategy.",
        "The platform's user engagement metrics exceeded management expectations."
    ]
    
    # Simulated extraction results
    structured_data = {
        'document_text': document_text,
        'tables': [],
        'key_values': []
    }
    
    processed_result = {
        'processed_tables': [
            {
                'page': 1,
                'structured_table': {
                    'Company_Name': 'Life360, Inc.',
                    'Stock_Symbol': 'LIF',
                    'Exchange': 'NASDAQ',
                    'Q4_2024_Revenue': '$115.5 million',
                    'Revenue_Growth': '33%',
                    'CEO_Name': 'John Smith',
                    'Monthly_Active_Users': '65.8 million',
                    'Market_Share': '12%',
                    'Stock_Performance': '25% year-to-date',
                    'User_Growth': '18%'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {
                'Platform_Type': 'Family safety platform',
                'Market_Position': 'World\'s largest',
                'Business_Strategy': 'Family safety focus',
                'Performance_Metric': 'User engagement'
            }
        },
        'processed_document_text': []
    }
    
    print("BEFORE: Basic Extraction (empty context column)")
    print("-" * 70)
    print(f"{'Field':<25} {'Value':<25} {'Context':<15}")
    print("-" * 70)
    
    # Show original data without context
    table_data = processed_result['processed_tables'][0]['structured_table']
    for field, value in list(table_data.items())[:5]:  # Show first 5 for brevity
        print(f"{field:<25} {str(value):<25} {'(empty)':<15}")
    print("... (and 9 more fields with empty context)")
    
    print()
    print("AFTER: Enhanced Extraction (with comprehensive context)")
    print("-" * 70)
    
    # Apply enhanced context tracking
    enhanced_result = integrate_context_tracking(structured_data, processed_result)
    
    print("Context Tracking Performance:")
    summary = enhanced_result.get('context_tracking_summary', {})
    print(f"  ✓ Context Coverage: {summary.get('context_coverage_percentage', 0)}% ({summary.get('fields_with_context', 0)}/{summary.get('total_fields', 0)} fields)")
    print(f"  ✓ Average Context Length: {summary.get('average_context_length', 0)} characters")
    print(f"  ✓ Total Context Extracted: {summary.get('total_context_characters', 0)} characters")
    print(f"  ✓ Document Processing: {summary.get('document_text_lines', 0)} lines analyzed")
    print()
    
    # Show enhanced data with context (first 8 examples)
    enhanced_data = enhanced_result.get('enhanced_data_with_context', [])
    print("Sample Enhanced Results (showing first 8 fields):")
    print("=" * 90)
    
    for i, row in enumerate(enhanced_data[:8], 1):
        print(f"\n{i}. Field: {row['field']}")
        print(f"   Value: {row['value']}")
        print(f"   Has Context: {'✓ YES' if row['has_context'] else '✗ NO'}")
        
        if row['context']:
            # Show context with smart truncation
            context = row['context']
            if len(context) > 150:
                # Find a good breaking point
                truncated = context[:140]
                last_space = truncated.rfind(' ')
                if last_space > 100:
                    context = truncated[:last_space] + "..."
                else:
                    context = truncated + "..."
            print(f"   Context: {context}")
        else:
            print(f"   Context: (no relevant context found)")
        print("-" * 70)
    
    print(f"\n... and {len(enhanced_data) - 8} more fields with context")
    
    print("\n" + "=" * 90)
    print("KEY ENHANCEMENTS DEMONSTRATED:")
    print("=" * 90)
    print("🎯 FUZZY MATCHING: Finds context even with slight variations in terminology")
    print("📊 RELEVANCE SCORING: Prioritizes most relevant sentences (25+ point threshold)")
    print("🔤 ORIGINAL WORDING: Preserves exact language from source document")
    print("🚫 DEDUPLICATION: Eliminates duplicate sentences while preserving unique mentions")
    print("📈 HIGH COVERAGE: Achieved {}% context coverage across all fields".format(summary.get('context_coverage_percentage', 0)))
    print("⚡ PERFORMANCE: Processes documents efficiently with smart sentence extraction")
    print()
    print("TECHNICAL FEATURES:")
    print("• Partial ratio matching with 75+ similarity threshold")
    print("• Multi-term value extraction (numbers, words, phrases)")
    print("• Field name component matching with word boundaries")
    print("• Context length optimization (max 800 chars with sentence boundaries)")
    print("• Company/financial term recognition for enhanced matching")
    print()
    print("This enhancement transforms basic data extraction into comprehensive")
    print("document analysis, providing users with the full context needed for")
    print("informed decision-making and data validation.")
    print()

if __name__ == "__main__":
    demo_context_enhancement()