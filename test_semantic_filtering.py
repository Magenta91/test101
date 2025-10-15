#!/usr/bin/env python3
"""
Test script for semantic filtering in context tracking.
Demonstrates how semantic similarity prevents irrelevant context inclusion.
"""

import json
from context_tracker import generate_context_for_field, integrate_context_tracking

def test_semantic_filtering_examples():
    """Test semantic filtering with problematic examples that should be filtered out"""
    
    print("=" * 80)
    print("SEMANTIC FILTERING TEST - PREVENTING IRRELEVANT CONTEXT")
    print("=" * 80)
    print()
    
    # Document with mixed content that could cause false matches
    problematic_document = """
    Lokesh Kumar was born on March 15, 1989, making him 35 years old.
    His blood group is O+ which is noted for emergency contact purposes.
    As an Indian national, his citizenship status is important for visa processing.
    Lokesh has extensive cloud platform expertise and technical leadership skills.
    The company's age in the market is 15 years, showing strong stability.
    Revenue growth has been consistent at 25% year-over-year.
    The platform serves users across different age demographics.
    Blood group compatibility is crucial for medical procedures.
    Citizenship requirements vary by country and regulation.
    Age verification is mandatory for certain financial services.
    His technical expertise spans cloud platforms, AI, and data analytics.
    The average age of our user base is 28 years old.
    """
    
    # Test cases that should demonstrate semantic filtering
    test_cases = [
        {
            "field": "Age",
            "value": "35 years old",
            "expected_relevant": [
                "Lokesh Kumar was born on March 15, 1989, making him 35 years old.",
                "The average age of our user base is 28 years old.",
                "Age verification is mandatory for certain financial services."
            ],
            "expected_filtered_out": [
                "The company's age in the market is 15 years, showing strong stability.",
                "The platform serves users across different age demographics."
            ]
        },
        {
            "field": "Blood_Group", 
            "value": "O+",
            "expected_relevant": [
                "His blood group is O+ which is noted for emergency contact purposes.",
                "Blood group compatibility is crucial for medical procedures."
            ],
            "expected_filtered_out": [
                "Lokesh has extensive cloud platform expertise and technical leadership skills.",
                "Revenue growth has been consistent at 25% year-over-year."
            ]
        },
        {
            "field": "Citizenship",
            "value": "Indian national", 
            "expected_relevant": [
                "As an Indian national, his citizenship status is important for visa processing.",
                "Citizenship requirements vary by country and regulation."
            ],
            "expected_filtered_out": [
                "His blood group is O+ which is noted for emergency contact purposes.",
                "His technical expertise spans cloud platforms, AI, and data analytics."
            ]
        },
        {
            "field": "Technical_Expertise",
            "value": "Cloud platform expertise",
            "expected_relevant": [
                "Lokesh has extensive cloud platform expertise and technical leadership skills.",
                "His technical expertise spans cloud platforms, AI, and data analytics."
            ],
            "expected_filtered_out": [
                "His blood group is O+ which is noted for emergency contact purposes.",
                "As an Indian national, his citizenship status is important for visa processing."
            ]
        }
    ]
    
    print("Testing Semantic Filtering Results:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        print("-" * 40)
        
        # Generate context with semantic filtering
        context = generate_context_for_field(field, value, problematic_document)
        
        print(f"Generated Context:")
        if context:
            print(f"  {context}")
        else:
            print("  (no relevant context found)")
        
        # Analyze what was included vs filtered out
        if context:
            context_sentences = [s.strip() for s in context.split('.') if s.strip()]
            
            print(f"\nSemantic Analysis:")
            print(f"  ✓ Sentences included: {len(context_sentences)}")
            
            # Check if expected relevant sentences are included
            relevant_found = 0
            for expected in test_case["expected_relevant"]:
                if any(expected.lower() in sent.lower() for sent in context_sentences):
                    relevant_found += 1
            
            # Check if irrelevant sentences were filtered out
            irrelevant_filtered = 0
            for irrelevant in test_case["expected_filtered_out"]:
                if not any(irrelevant.lower() in context.lower() for _ in [1]):
                    irrelevant_filtered += 1
            
            print(f"  ✓ Relevant content found: {relevant_found}/{len(test_case['expected_relevant'])}")
            print(f"  ✓ Irrelevant content filtered: {irrelevant_filtered}/{len(test_case['expected_filtered_out'])}")
            
            # Calculate semantic filtering effectiveness
            total_expected = len(test_case["expected_relevant"]) + len(test_case["expected_filtered_out"])
            correct_decisions = relevant_found + irrelevant_filtered
            effectiveness = (correct_decisions / total_expected) * 100 if total_expected > 0 else 0
            
            print(f"  📊 Filtering Effectiveness: {effectiveness:.1f}%")
        
        print()

def test_semantic_vs_lexical_comparison():
    """Compare results with and without semantic filtering"""
    
    print("=" * 80)
    print("SEMANTIC vs LEXICAL FILTERING COMPARISON")
    print("=" * 80)
    print()
    
    # Document with potential false positives
    mixed_content = """
    Apple Inc. is a technology company based in Cupertino, California.
    The apple orchard produces fresh fruit for local markets.
    Apple's stock symbol is AAPL and trades on NASDAQ.
    She ate an apple for lunch as part of her healthy diet.
    Apple reported quarterly revenue of $89.5 billion in Q4 2024.
    The apple tree in the garden needs pruning this season.
    Tim Cook is the CEO of Apple Inc. and leads the company.
    Apple juice is a popular beverage choice for children.
    """
    
    test_field = "Company_Name"
    test_value = "Apple Inc."
    
    print(f"Field: {test_field}")
    print(f"Value: {test_value}")
    print()
    
    # Generate context with semantic filtering (current implementation)
    semantic_context = generate_context_for_field(test_field, test_value, mixed_content)
    
    print("WITH Semantic Filtering:")
    print("-" * 30)
    if semantic_context:
        for i, sentence in enumerate(semantic_context.split('.'), 1):
            sentence = sentence.strip()
            if sentence:
                print(f"{i}. {sentence}")
    else:
        print("(no context found)")
    
    print()
    print("Expected Behavior:")
    print("✓ Should include: Company-related sentences about Apple Inc.")
    print("✗ Should exclude: Sentences about fruit, orchards, juice, etc.")
    print()
    
    # Analyze the results
    company_terms = ['technology', 'stock', 'nasdaq', 'revenue', 'ceo', 'company']
    fruit_terms = ['orchard', 'fruit', 'lunch', 'diet', 'tree', 'juice', 'beverage']
    
    if semantic_context:
        context_lower = semantic_context.lower()
        company_mentions = sum(1 for term in company_terms if term in context_lower)
        fruit_mentions = sum(1 for term in fruit_terms if term in context_lower)
        
        print(f"Analysis Results:")
        print(f"  Company-related terms found: {company_mentions}/{len(company_terms)}")
        print(f"  Fruit-related terms found: {fruit_mentions}/{len(fruit_terms)}")
        
        if company_mentions > 0 and fruit_mentions == 0:
            print("  🎯 EXCELLENT: Semantic filtering working correctly!")
        elif company_mentions > fruit_mentions:
            print("  ✅ GOOD: More relevant than irrelevant content")
        else:
            print("  ⚠️  NEEDS IMPROVEMENT: Too much irrelevant content")

def test_integration_with_semantic_filtering():
    """Test the full integration with semantic filtering"""
    
    print("\n" + "=" * 80)
    print("FULL INTEGRATION TEST WITH SEMANTIC FILTERING")
    print("=" * 80)
    print()
    
    # Realistic document with mixed content
    document_text = [
        "John Smith, age 45, is the Chief Executive Officer of TechCorp Inc.",
        "The company's age in the market spans over 20 years of innovation.",
        "His blood type is A+ as recorded in the medical files.",
        "TechCorp's revenue blood flow has been strong this quarter.",
        "As a US citizen, John Smith leads the company's strategic initiatives.",
        "The citizenship program for employees offers various benefits.",
        "TechCorp Inc. specializes in cloud platform development.",
        "The platform age demographics show diverse user adoption.",
        "John Smith has extensive leadership experience in technology.",
        "Age verification systems are crucial for platform security."
    ]
    
    # Structured data that could cause false matches
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
                    'CEO_Name': 'John Smith',
                    'Age': '45',
                    'Blood_Type': 'A+',
                    'Citizenship': 'US citizen',
                    'Company_Name': 'TechCorp Inc.'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {}
        },
        'processed_document_text': []
    }
    
    print("Testing full pipeline with semantic filtering...")
    enhanced_result = integrate_context_tracking(structured_data, processed_result)
    
    print("\nResults with Semantic Filtering:")
    print("-" * 50)
    
    for i, row in enumerate(enhanced_result.get('enhanced_data_with_context', []), 1):
        print(f"\n{i}. Field: {row['field']}")
        print(f"   Value: {row['value']}")
        print(f"   Has Context: {'✓' if row['has_context'] else '✗'}")
        
        if row['context']:
            print(f"   Context: {row['context']}")
            
            # Quick relevance check
            field_lower = row['field'].lower()
            context_lower = row['context'].lower()
            
            if 'age' in field_lower:
                if 'john smith, age 45' in context_lower and 'company\'s age' not in context_lower:
                    print("   🎯 EXCELLENT: Only person's age, not company age")
                elif 'company\'s age' in context_lower:
                    print("   ⚠️  WARNING: Includes company age (should be filtered)")
            
            elif 'blood' in field_lower:
                if 'blood type is a+' in context_lower and 'revenue blood flow' not in context_lower:
                    print("   🎯 EXCELLENT: Only medical blood type, not metaphorical usage")
                elif 'revenue blood flow' in context_lower:
                    print("   ⚠️  WARNING: Includes metaphorical blood reference")
        else:
            print("   Context: (no relevant context found)")
    
    # Summary
    summary = enhanced_result.get('context_tracking_summary', {})
    print(f"\nSemantic Filtering Summary:")
    print(f"  Total fields: {summary.get('total_fields', 0)}")
    print(f"  Fields with context: {summary.get('fields_with_context', 0)}")
    print(f"  Context coverage: {summary.get('context_coverage_percentage', 0)}%")

if __name__ == "__main__":
    test_semantic_filtering_examples()
    test_semantic_vs_lexical_comparison()
    test_integration_with_semantic_filtering()