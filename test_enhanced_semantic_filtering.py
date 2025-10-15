#!/usr/bin/env python3
"""
Test script for enhanced semantic filtering with confidence scoring and multi-domain detection.
Demonstrates precision improvements and cross-field association elimination.
"""

import json
from context_tracker import (
    integrate_context_tracking, 
    generate_context_for_field, 
    is_sentence_relevant_to_field,
    detect_multi_domain_sentence,
    calculate_keyword_proximity
)

def test_enhanced_precision():
    """Test enhanced semantic precision with confidence scoring"""
    
    print("=" * 90)
    print("ENHANCED SEMANTIC FILTERING - PRECISION & CONFIDENCE SCORING")
    print("=" * 90)
    print()
    
    # Complex document with potential cross-field associations
    complex_document = """
    Lokesh Kumar was born on March 15, 1989, in Jaipur, Rajasthan, making him 35 years old as of 2024.
    His O+ blood group is noted for emergency contact purposes in his medical records.
    As an Indian national, his citizenship status is important for understanding his work authorization and visa requirements.
    Lokesh has extensive cloud platform expertise and technical leadership skills spanning over 10 years.
    Born in Jaipur and has O+ blood group, he completed his engineering degree from IIT Delhi.
    The company's age in the market is 15 years, showing strong stability and growth.
    His technical expertise spans cloud platforms, AI, and data analytics with proven results.
    Blood flow in the financial markets has been strong this quarter with increased investments.
    The average age of our user base is 28 years old, indicating a young demographic.
    Citizenship requirements vary by country and regulation, affecting global expansion plans.
    Age verification is mandatory for certain financial services and compliance requirements.
    His blood type is A+ as recorded in the medical files for emergency procedures.
    """
    
    # Test cases with expected precision improvements
    test_cases = [
        {
            "field": "Age",
            "value": "35 years old",
            "expected_context": "Lokesh Kumar was born on March 15, 1989, in Jaipur, Rajasthan, making him 35 years old as of 2024.",
            "should_exclude": ["company's age", "average age of user base", "age verification"]
        },
        {
            "field": "Blood_Group", 
            "value": "O+",
            "expected_context": "His O+ blood group is noted for emergency contact purposes in his medical records.",
            "should_exclude": ["blood flow in financial markets", "Born in Jaipur and has O+ blood group"]
        },
        {
            "field": "Citizenship",
            "value": "Indian national",
            "expected_context": "As an Indian national, his citizenship status is important for understanding his work authorization and visa requirements.",
            "should_exclude": ["citizenship requirements vary by country"]
        },
        {
            "field": "Technical_Expertise",
            "value": "Cloud platform expertise",
            "expected_context": "Lokesh has extensive cloud platform expertise and technical leadership skills spanning over 10 years.",
            "should_exclude": ["Born in Jaipur and has O+ blood group"]
        }
    ]
    
    print("Enhanced Precision Test Results:")
    print("-" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        print("-" * 50)
        
        # Generate context with enhanced filtering and confidence
        context, confidence = generate_context_for_field(field, value, complex_document)
        
        print(f"Generated Context (Confidence: {confidence:.3f}):")
        if context:
            print(f"  {context}")
        else:
            print("  (no relevant context found)")
        
        # Analyze precision
        if context:
            context_lower = context.lower()
            
            # Check if expected content is included
            expected_found = any(exp.lower() in context_lower for exp in [test_case["expected_context"]])
            
            # Check if unwanted content is excluded
            unwanted_found = any(unwanted.lower() in context_lower for unwanted in test_case["should_exclude"])
            
            print(f"\nPrecision Analysis:")
            print(f"  ✓ Expected content found: {'Yes' if expected_found else 'No'}")
            print(f"  ✓ Unwanted content excluded: {'Yes' if not unwanted_found else 'No'}")
            print(f"  📊 Confidence Score: {confidence:.3f}")
            
            # Overall precision assessment
            if expected_found and not unwanted_found and confidence >= 0.7:
                print(f"  🎯 EXCELLENT: High precision with good confidence")
            elif expected_found and not unwanted_found:
                print(f"  ✅ GOOD: Correct content but lower confidence")
            elif expected_found:
                print(f"  ⚠️  PARTIAL: Expected content found but includes unwanted")
            else:
                print(f"  ❌ POOR: Missing expected content")
        
        print()

def test_multi_domain_detection():
    """Test multi-domain sentence detection"""
    
    print("=" * 90)
    print("MULTI-DOMAIN SENTENCE DETECTION")
    print("=" * 90)
    print()
    
    # Test sentences with varying domain complexity
    test_sentences = [
        {
            "sentence": "Lokesh Kumar was born on March 15, 1989, making him 35 years old.",
            "expected_domains": ["name", "age"],
            "is_multi_domain": False
        },
        {
            "sentence": "Born in Jaipur and has O+ blood group, he completed his engineering degree.",
            "expected_domains": ["age", "blood", "education", "location"],
            "is_multi_domain": True
        },
        {
            "sentence": "His O+ blood group is noted for emergency contact purposes.",
            "expected_domains": ["blood", "medical"],
            "is_multi_domain": False
        },
        {
            "sentence": "As an Indian national with technical expertise in cloud platforms, he leads the team.",
            "expected_domains": ["citizenship", "technical", "job"],
            "is_multi_domain": True
        },
        {
            "sentence": "The company reported quarterly revenue of $115.5 million.",
            "expected_domains": ["company", "revenue"],
            "is_multi_domain": False
        }
    ]
    
    # Semantic groups for testing
    semantic_groups = {
        'name': ['name', 'called', 'known', 'person'],
        'age': ['age', 'years', 'old', 'born', 'birth'],
        'blood': ['blood', 'type', 'group', 'medical'],
        'education': ['education', 'degree', 'university', 'studied'],
        'location': ['location', 'born', 'city', 'place'],
        'citizenship': ['citizen', 'national', 'nationality'],
        'technical': ['technical', 'expertise', 'skills', 'cloud'],
        'job': ['job', 'leads', 'team', 'work'],
        'company': ['company', 'reported', 'business'],
        'revenue': ['revenue', 'million', 'financial']
    }
    
    print("Multi-Domain Detection Results:")
    print("-" * 50)
    
    for i, test in enumerate(test_sentences, 1):
        sentence = test["sentence"]
        is_multi, detected_domains = detect_multi_domain_sentence(sentence, semantic_groups)
        
        print(f"\nTest {i}:")
        print(f"  Sentence: {sentence}")
        print(f"  Detected domains: {detected_domains}")
        print(f"  Is multi-domain: {is_multi}")
        print(f"  Expected multi-domain: {test['is_multi_domain']}")
        
        # Accuracy check
        if is_multi == test['is_multi_domain']:
            print(f"  ✅ CORRECT: Detection matches expectation")
        else:
            print(f"  ❌ INCORRECT: Detection mismatch")

def test_keyword_proximity():
    """Test keyword proximity scoring"""
    
    print("\n" + "=" * 90)
    print("KEYWORD PROXIMITY SCORING")
    print("=" * 90)
    print()
    
    # Test sentences with varying keyword distances
    test_cases = [
        {
            "sentence": "Lokesh Kumar, age 35, is the CEO",
            "field_words": ["age"],
            "value_terms": ["35"],
            "expected_proximity": "high"
        },
        {
            "sentence": "Born in 1989, making him 35 years old",
            "field_words": ["age"],
            "value_terms": ["35"],
            "expected_proximity": "medium"
        },
        {
            "sentence": "The company has been in business for 35 years and focuses on age demographics",
            "field_words": ["age"],
            "value_terms": ["35"],
            "expected_proximity": "low"
        },
        {
            "sentence": "His O+ blood group is noted",
            "field_words": ["blood", "group"],
            "value_terms": ["O+"],
            "expected_proximity": "high"
        }
    ]
    
    print("Proximity Scoring Results:")
    print("-" * 40)
    
    for i, test in enumerate(test_cases, 1):
        sentence = test["sentence"]
        field_words = test["field_words"]
        value_terms = test["value_terms"]
        
        proximity_score = calculate_keyword_proximity(field_words, value_terms, sentence)
        
        print(f"\nTest {i}:")
        print(f"  Sentence: {sentence}")
        print(f"  Field words: {field_words}")
        print(f"  Value terms: {value_terms}")
        print(f"  Proximity score: {proximity_score:.3f}")
        print(f"  Expected: {test['expected_proximity']}")
        
        # Categorize score
        if proximity_score >= 0.8:
            actual_category = "high"
        elif proximity_score >= 0.4:
            actual_category = "medium"
        else:
            actual_category = "low"
        
        if actual_category == test['expected_proximity']:
            print(f"  ✅ CORRECT: {actual_category} proximity as expected")
        else:
            print(f"  ⚠️  MISMATCH: Got {actual_category}, expected {test['expected_proximity']}")

def test_full_integration_with_confidence():
    """Test full integration with confidence scoring"""
    
    print("\n" + "=" * 90)
    print("FULL INTEGRATION TEST WITH CONFIDENCE SCORING")
    print("=" * 90)
    print()
    
    # Realistic document with mixed content
    document_text = [
        "Lokesh Kumar was born on March 15, 1989, in Jaipur, Rajasthan, making him 35 years old as of 2024.",
        "His O+ blood group is noted for emergency contact purposes in his medical records.",
        "As an Indian national, his citizenship status is important for work authorization.",
        "Lokesh has extensive cloud platform expertise and technical leadership skills.",
        "The company's age in the market is 15 years, showing strong stability.",
        "Blood flow in the financial markets has been strong this quarter.",
        "Born in Jaipur and has O+ blood group, he completed his engineering degree.",
        "Age verification is mandatory for certain financial services.",
        "His technical expertise spans cloud platforms, AI, and data analytics.",
        "Citizenship requirements vary by country and regulation."
    ]
    
    # Structured data
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
                    'Name': 'Lokesh Kumar',
                    'Age': '35 years old',
                    'Blood_Group': 'O+',
                    'Citizenship': 'Indian national',
                    'Technical_Expertise': 'Cloud platform expertise'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {}
        },
        'processed_document_text': []
    }
    
    print("Testing enhanced integration with confidence scoring...")
    enhanced_result = integrate_context_tracking(structured_data, processed_result)
    
    print("\nResults with Enhanced Semantic Filtering:")
    print("-" * 60)
    
    for i, row in enumerate(enhanced_result.get('enhanced_data_with_context', []), 1):
        print(f"\n{i}. Field: {row['field']}")
        print(f"   Value: {row['value']}")
        print(f"   Has Context: {'✓' if row['has_context'] else '✗'}")
        print(f"   Confidence: {row.get('context_confidence', 0.0):.3f}")
        
        if row['context']:
            print(f"   Context: {row['context']}")
            
            # Quality assessment based on confidence
            confidence = row.get('context_confidence', 0.0)
            if confidence >= 0.8:
                print("   🎯 EXCELLENT: High confidence context")
            elif confidence >= 0.6:
                print("   ✅ GOOD: Moderate confidence context")
            elif confidence >= 0.4:
                print("   ⚠️  FAIR: Lower confidence context")
            else:
                print("   ❌ POOR: Very low confidence context")
        else:
            print("   Context: (no relevant context found)")
    
    # Summary
    summary = enhanced_result.get('context_tracking_summary', {})
    print(f"\nEnhanced Filtering Summary:")
    print(f"  Total fields: {summary.get('total_fields', 0)}")
    print(f"  Fields with context: {summary.get('fields_with_context', 0)}")
    print(f"  Context coverage: {summary.get('context_coverage_percentage', 0)}%")
    
    # Calculate average confidence
    contexts_with_confidence = [row for row in enhanced_result.get('enhanced_data_with_context', []) 
                               if row.get('context_confidence', 0) > 0]
    if contexts_with_confidence:
        avg_confidence = sum(row['context_confidence'] for row in contexts_with_confidence) / len(contexts_with_confidence)
        print(f"  Average confidence: {avg_confidence:.3f}")

if __name__ == "__main__":
    test_enhanced_precision()
    test_multi_domain_detection()
    test_keyword_proximity()
    test_full_integration_with_confidence()