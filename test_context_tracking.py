#!/usr/bin/env python3
"""
Test script for the enhanced context tracking functionality.
Demonstrates comprehensive context extraction with fuzzy matching and relevance scoring.
"""

import json
from context_tracker import integrate_context_tracking, generate_context_for_field, extract_sentences_from_text

def test_enhanced_context_tracking():
    """Test the enhanced context tracking functionality with comprehensive examples"""
    
    print("=== Testing Enhanced Context Tracking System ===\n")
    
    # Realistic financial document text
    sample_document_text = [
        "Life360, Inc. (NASDAQ: LIF) is the world's largest family safety platform.",
        "The company serves families through location sharing, driving safety, and digital tools.",
        "Financial Performance: Life360 reported record quarterly revenue of $115.5 million for Q4 2024.",
        "This represents a 33% increase compared to the same period last year.",
        "The strong performance was driven by user growth and increased engagement.",
        "John Smith, Chief Executive Officer, commented on the results:",
        "'We are pleased with our continued growth trajectory and market leadership.'",
        "Our platform now serves over 65.8 million monthly active users globally.",
        "Life360 has captured approximately 12% market share in family safety applications.",
        "The company's stock (LIF) has performed well, gaining 25% year-to-date.",
        "John Smith emphasized Life360's commitment to innovation and expansion.",
        "The company plans to introduce new features in 2025.",
        "Life360's revenue growth outpaced industry averages by significant margins.",
        "Monthly active users increased by 18% compared to the previous quarter.",
        "The NASDAQ-listed company continues to strengthen its market position."
    ]
    
    # Sample structured data
    sample_structured_data = {
        'document_text': sample_document_text,
        'tables': [],
        'key_values': []
    }
    
    # Sample processed result with various data types
    sample_processed_result = {
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
                    'Stock_Performance': '25% year-to-date'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {
                'Platform_Type': 'Family safety platform',
                'Market_Position': 'World\'s largest',
                'User_Growth': '18%',
                'Business_Focus': 'Location sharing and safety'
            }
        },
        'processed_document_text': [
            {
                'extracted_facts': {
                    'Financial_Performance': 'Record quarterly revenue',
                    'Growth_Driver': 'User growth and engagement',
                    'Future_Plans': 'New features in 2025',
                    'Industry_Comparison': 'Outpaced industry averages'
                }
            }
        ]
    }
    
    # Test the enhanced integration
    enhanced_result = integrate_context_tracking(sample_structured_data, sample_processed_result)
    
    print("Enhanced Context Tracking Summary:")
    summary = enhanced_result.get('context_tracking_summary', {})
    print(json.dumps(summary, indent=2))
    print()
    
    print("Enhanced Data with Comprehensive Context:")
    print("=" * 100)
    
    for i, row in enumerate(enhanced_result.get('enhanced_data_with_context', []), 1):
        print(f"\nRow {i}: {row['field']}")
        print(f"  Value: {row['value']}")
        print(f"  Source: {row['source']}")
        print(f"  Has Context: {row['has_context']}")
        
        if row['context']:
            # Show context with line breaks for readability
            context = row['context']
            print(f"  Context: {context}")
        else:
            print(f"  Context: (no relevant context found)")
        print("-" * 80)
    
    return enhanced_result

def test_context_generation_directly():
    """Test the context generation function directly with various scenarios"""
    
    print("\n=== Testing Context Generation Function Directly ===\n")
    
    # Sample document text
    full_text = """
    Apple Inc. is a multinational technology company headquartered in Cupertino, California.
    The company designs, develops, and sells consumer electronics, computer software, and online services.
    Apple's stock symbol is AAPL and it trades on the NASDAQ exchange.
    In Q4 2024, Apple reported revenue of $89.5 billion, representing a 6% increase year-over-year.
    Tim Cook, the Chief Executive Officer, praised the team's exceptional performance.
    AAPL shares rose 5% following the strong earnings announcement.
    The iPhone remains Apple's flagship product, generating significant revenue.
    Apple Inc. continues to innovate in consumer electronics and services.
    Tim Cook emphasized the company's commitment to environmental sustainability.
    The company's market capitalization exceeded $3 trillion in 2024.
    """
    
    # Test cases with different field/value combinations
    test_cases = [
        ("Company_Name", "Apple Inc."),
        ("Stock_Symbol", "AAPL"),
        ("CEO_Name", "Tim Cook"),
        ("Q4_Revenue", "$89.5 billion"),
        ("Exchange", "NASDAQ"),
        ("Product", "iPhone"),
        ("Market_Cap", "$3 trillion"),
        ("Growth_Rate", "6%"),
        ("Headquarters", "Cupertino")
    ]
    
    print("Context Generation Test Results:")
    print("-" * 60)
    
    for field, value in test_cases:
        context = generate_context_for_field(field, value, full_text)
        print(f"\nField: {field}")
        print(f"Value: {value}")
        print(f"Context Found: {'Yes' if context else 'No'}")
        if context:
            # Truncate for display
            display_context = context[:200] + "..." if len(context) > 200 else context
            print(f"Context: {display_context}")
        print("-" * 40)

def test_sentence_extraction():
    """Test the sentence extraction functionality"""
    
    print("\n=== Testing Sentence Extraction ===\n")
    
    sample_text = """
    Life360, Inc. is a family safety platform. The company reported $115.5 million in revenue.
    This represents strong growth! John Smith, CEO, was pleased with results.
    What does the future hold? The company plans expansion.
    """
    
    sentences = extract_sentences_from_text(sample_text)
    
    print("Extracted Sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")
    
    print(f"\nTotal sentences extracted: {len(sentences)}")

if __name__ == "__main__":
    # Run comprehensive tests
    test_enhanced_context_tracking()
    test_context_generation_directly()
    test_sentence_extraction()