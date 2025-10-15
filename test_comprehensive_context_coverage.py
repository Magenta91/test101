#!/usr/bin/env python3
"""
Test script for comprehensive context coverage with refined filtering.
Verifies that all fields receive relevant context while maintaining precision.
"""

import json
from context_tracker import (
    integrate_context_tracking, 
    generate_context_for_field,
    determine_adaptive_threshold,
    weak_context_recovery,
    extract_sentences_from_text
)

def test_comprehensive_coverage():
    """Test comprehensive context coverage with the refined system"""
    
    print("=" * 90)
    print("COMPREHENSIVE CONTEXT COVERAGE TEST")
    print("=" * 90)
    print()
    
    # Comprehensive document with various field types
    comprehensive_document = """
    Lokesh Kumar was born on March 15, 1989, in Jaipur, Rajasthan, making him 35 years old as of 2024.
    His O+ blood group is noted for emergency contact purposes in his medical records.
    As an Indian national, his citizenship status is important for understanding his work authorization and visa requirements.
    Lokesh has extensive cloud platform expertise and technical leadership skills spanning over 10 years.
    Born in Jaipur and has O+ blood group, he completed his engineering degree from IIT Delhi in 2011.
    He currently works as a Senior Software Engineer at TechCorp Inc., earning a salary of $95,000 annually.
    His contact information includes phone number +91-9876543210 and email lokesh.kumar@techcorp.com.
    The company's age in the market is 15 years, showing strong stability and growth.
    His technical expertise spans cloud platforms, AI, and data analytics with proven results.
    Blood flow in the financial markets has been strong this quarter with increased investments.
    The average age of our user base is 28 years old, indicating a young demographic.
    Citizenship requirements vary by country and regulation, affecting global expansion plans.
    Age verification is mandatory for certain financial services and compliance requirements.
    His blood type is A+ as recorded in the medical files for emergency procedures.
    Lokesh Kumar graduated with honors and received multiple certifications in cloud computing.
    The education system in India emphasizes technical skills and practical knowledge.
    His address is 123 Tech Street, Bangalore, Karnataka, India, 560001.
    """
    
    # Test cases covering various field types
    test_cases = [
        {"field": "Name", "value": "Lokesh Kumar", "type": "text"},
        {"field": "Age", "value": "35 years old", "type": "numeric"},
        {"field": "Blood_Group", "value": "O+", "type": "code"},
        {"field": "Citizenship", "value": "Indian national", "type": "text"},
        {"field": "Technical_Expertise", "value": "Cloud platform expertise", "type": "text"},
        {"field": "Education", "value": "Engineering degree", "type": "text"},
        {"field": "Salary", "value": "$95,000", "type": "numeric"},
        {"field": "Phone", "value": "+91-9876543210", "type": "code"},
        {"field": "Email", "value": "lokesh.kumar@techcorp.com", "type": "code"},
        {"field": "Address", "value": "123 Tech Street, Bangalore", "type": "text"},
        {"field": "Company", "value": "TechCorp Inc.", "type": "text"},
        {"field": "Graduation_Year", "value": "2011", "type": "numeric"}
    ]
    
    print("Comprehensive Coverage Test Results:")
    print("-" * 70)
    
    coverage_stats = {
        'total_fields': len(test_cases),
        'fields_with_context': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0,
        'recovered_contexts': 0
    }
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        field_type = test_case["type"]
        
        print(f"\nTest {i}: {field} = '{value}' ({field_type})")
        print("-" * 50)
        
        # Test adaptive threshold
        adaptive_threshold = determine_adaptive_threshold(field, value)
        print(f"  Adaptive threshold: {adaptive_threshold}")
        
        # Generate context with comprehensive coverage
        context, confidence = generate_context_for_field(field, value, comprehensive_document)
        
        print(f"  Generated Context (Confidence: {confidence:.3f}):")
        if context:
            coverage_stats['fields_with_context'] += 1
            
            # Categorize confidence
            if confidence >= 0.7:
                coverage_stats['high_confidence'] += 1
                confidence_category = "HIGH"
            elif confidence >= 0.4:
                coverage_stats['medium_confidence'] += 1
                confidence_category = "MEDIUM"
            else:
                coverage_stats['low_confidence'] += 1
                confidence_category = "LOW"
            
            # Check if this was likely recovered context (low confidence)
            if confidence < 0.5:
                coverage_stats['recovered_contexts'] += 1
            
            print(f"    {context}")
            print(f"  Confidence Category: {confidence_category}")
            
            # Analyze context quality
            context_lower = context.lower()
            value_lower = value.lower()
            
            # Check if value is mentioned
            value_mentioned = any(term.lower() in context_lower for term in value.split() if len(term) > 2)
            
            # Check for cross-field contamination
            contamination_indicators = []
            if field.lower() == 'age' and any(term in context_lower for term in ['company', 'market', 'platform']):
                contamination_indicators.append('company_age')
            if field.lower() == 'blood' and any(term in context_lower for term in ['flow', 'money', 'red']):
                contamination_indicators.append('blood_metaphor')
            
            print(f"  Quality Analysis:")
            print(f"    Value mentioned: {'Yes' if value_mentioned else 'No'}")
            print(f"    Cross-field contamination: {'Yes' if contamination_indicators else 'No'}")
            if contamination_indicators:
                print(f"    Contamination types: {contamination_indicators}")
        else:
            print("    (no relevant context found)")
            print(f"  Status: EMPTY - No context recovered")
        
        print()
    
    # Summary statistics
    print("=" * 70)
    print("COVERAGE SUMMARY")
    print("=" * 70)
    print(f"Total fields tested: {coverage_stats['total_fields']}")
    print(f"Fields with context: {coverage_stats['fields_with_context']}")
    print(f"Coverage percentage: {(coverage_stats['fields_with_context'] / coverage_stats['total_fields']) * 100:.1f}%")
    print()
    print(f"Confidence distribution:")
    print(f"  High confidence (≥0.7): {coverage_stats['high_confidence']}")
    print(f"  Medium confidence (0.4-0.7): {coverage_stats['medium_confidence']}")
    print(f"  Low confidence (<0.4): {coverage_stats['low_confidence']}")
    print(f"  Likely recovered contexts: {coverage_stats['recovered_contexts']}")
    print()
    
    # Overall assessment
    if coverage_stats['fields_with_context'] == coverage_stats['total_fields']:
        print("🎯 EXCELLENT: 100% context coverage achieved!")
    elif coverage_stats['fields_with_context'] >= coverage_stats['total_fields'] * 0.9:
        print("✅ VERY GOOD: >90% context coverage achieved")
    elif coverage_stats['fields_with_context'] >= coverage_stats['total_fields'] * 0.8:
        print("✅ GOOD: >80% context coverage achieved")
    else:
        print("⚠️  NEEDS IMPROVEMENT: <80% context coverage")

def test_multi_domain_handling():
    """Test handling of multi-domain sentences"""
    
    print("\n" + "=" * 90)
    print("MULTI-DOMAIN SENTENCE HANDLING TEST")
    print("=" * 90)
    print()
    
    # Document with multi-domain sentences
    multi_domain_document = """
    Born in Jaipur and has O+ blood group, Lokesh Kumar completed his engineering degree.
    As an Indian national with technical expertise in cloud platforms, he leads the development team.
    His contact details include phone +91-9876543210 and email lokesh@company.com for work purposes.
    The 35-year-old software engineer specializes in AI and machine learning technologies.
    """
    
    test_cases = [
        {"field": "Age", "value": "35", "expected_sentence": "The 35-year-old software engineer"},
        {"field": "Blood_Group", "value": "O+", "expected_sentence": "Born in Jaipur and has O+ blood group"},
        {"field": "Citizenship", "value": "Indian national", "expected_sentence": "As an Indian national with technical expertise"},
        {"field": "Technical_Expertise", "value": "Cloud platforms", "expected_sentence": "As an Indian national with technical expertise"}
    ]
    
    print("Multi-Domain Handling Results:")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        
        context, confidence = generate_context_for_field(field, value, multi_domain_document)
        
        print(f"  Context: {context}")
        print(f"  Confidence: {confidence:.3f}")
        
        # Check if multi-domain sentence was included (should be with reduced confidence)
        if context and test_case["expected_sentence"].lower() in context.lower():
            print(f"  ✅ Multi-domain sentence included with confidence reduction")
        elif context:
            print(f"  ⚠️  Different sentence selected")
        else:
            print(f"  ❌ No context found")

def test_weak_recovery():
    """Test weak context recovery for difficult cases"""
    
    print("\n" + "=" * 90)
    print("WEAK CONTEXT RECOVERY TEST")
    print("=" * 90)
    print()
    
    # Document with subtle references
    subtle_document = """
    The employee record shows various details for personnel management.
    Contact information is maintained for emergency purposes.
    Medical records include blood type information for safety protocols.
    Educational background verification is part of the hiring process.
    Salary information is confidential and stored securely.
    Geographic location data helps with regional assignments.
    """
    
    # Convert to sentences with indices
    sentences_with_indices = extract_sentences_from_text(subtle_document)
    
    test_cases = [
        {"field": "Blood_Group", "value": "O+"},
        {"field": "Education", "value": "Engineering degree"},
        {"field": "Salary", "value": "$95,000"},
        {"field": "Address", "value": "Bangalore"}
    ]
    
    print("Weak Recovery Test Results:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        
        # Test weak recovery directly
        recovery_results = weak_context_recovery(field, value, sentences_with_indices)
        
        print(f"  Recovery results: {len(recovery_results)} sentences")
        for j, (sentence, idx, score) in enumerate(recovery_results):
            print(f"    {j+1}. {sentence} (score: {score:.3f})")
        
        if recovery_results:
            print(f"  ✅ Recovery successful")
        else:
            print(f"  ❌ No recovery possible")

def test_full_integration():
    """Test full integration with comprehensive coverage"""
    
    print("\n" + "=" * 90)
    print("FULL INTEGRATION TEST - COMPREHENSIVE COVERAGE")
    print("=" * 90)
    print()
    
    # Realistic document
    document_text = [
        "Lokesh Kumar was born on March 15, 1989, in Jaipur, Rajasthan, making him 35 years old as of 2024.",
        "His O+ blood group is noted for emergency contact purposes in his medical records.",
        "As an Indian national, his citizenship status is important for work authorization.",
        "Lokesh has extensive cloud platform expertise and technical leadership skills.",
        "Born in Jaipur and has O+ blood group, he completed his engineering degree from IIT Delhi.",
        "He works as Senior Software Engineer at TechCorp Inc. with salary $95,000 annually.",
        "Contact: +91-9876543210, email: lokesh.kumar@techcorp.com, address: 123 Tech Street, Bangalore.",
        "The company's age in the market is 15 years, showing strong stability.",
        "His technical expertise spans cloud platforms, AI, and data analytics.",
        "Educational background includes multiple certifications in cloud computing."
    ]
    
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
                    'Technical_Expertise': 'Cloud platform expertise',
                    'Education': 'Engineering degree',
                    'Salary': '$95,000',
                    'Phone': '+91-9876543210',
                    'Email': 'lokesh.kumar@techcorp.com',
                    'Address': '123 Tech Street, Bangalore',
                    'Company': 'TechCorp Inc.'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {}
        },
        'processed_document_text': []
    }
    
    print("Testing comprehensive integration...")
    enhanced_result = integrate_context_tracking(structured_data, processed_result)
    
    print("\nResults with Comprehensive Coverage:")
    print("-" * 60)
    
    empty_contexts = 0
    total_fields = 0
    
    for i, row in enumerate(enhanced_result.get('enhanced_data_with_context', []), 1):
        total_fields += 1
        print(f"\n{i}. Field: {row['field']}")
        print(f"   Value: {row['value']}")
        print(f"   Has Context: {'✓' if row['has_context'] else '✗'}")
        print(f"   Confidence: {row.get('context_confidence', 0.0):.3f}")
        
        if row['context']:
            # Truncate for display
            context_display = row['context']
            if len(context_display) > 150:
                context_display = context_display[:147] + "..."
            print(f"   Context: {context_display}")
        else:
            print("   Context: (EMPTY)")
            empty_contexts += 1
    
    # Final assessment
    coverage_percentage = ((total_fields - empty_contexts) / total_fields) * 100 if total_fields > 0 else 0
    
    print(f"\nFinal Assessment:")
    print(f"  Total fields: {total_fields}")
    print(f"  Empty contexts: {empty_contexts}")
    print(f"  Coverage: {coverage_percentage:.1f}%")
    
    if empty_contexts == 0:
        print("  🎯 SUCCESS: 100% context coverage achieved!")
    elif empty_contexts <= 2:
        print("  ✅ VERY GOOD: Minimal empty contexts")
    else:
        print("  ⚠️  NEEDS IMPROVEMENT: Too many empty contexts")

if __name__ == "__main__":
    test_comprehensive_coverage()
    test_multi_domain_handling()
    test_weak_recovery()
    test_full_integration()