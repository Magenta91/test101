#!/usr/bin/env python3
"""
Test script for refined context generation with indirect relation capture
and cross-domain filtering.
"""

import json
from context_tracker import (
    generate_context_for_field,
    integrate_context_tracking,
    is_relevant_sentence,
    get_enhanced_semantic_groups,
    get_enhanced_anti_patterns
)

def test_indirect_relation_capture():
    """Test capturing indirectly related sentences"""
    
    print("=" * 90)
    print("INDIRECT RELATION CAPTURE TEST")
    print("=" * 90)
    print()
    
    # Financial document with direct and indirect relations
    financial_document = """
    Life360 Inc. reported strong financial performance for Q4 2024.
    Revenue grew by 15% year-over-year, reflecting strong insurance premium collections.
    The company's total revenue reached $115.5 million in the quarter.
    Net profit after tax increased by 12% compared to FY22.
    Earnings per share rose 10%, reflecting profit expansion across all segments.
    Strong margin growth indicated improved profitability and operational efficiency.
    The profit growth reflected in earnings per share demonstrates sustainable business model.
    Insurance premium revenue contributed significantly to overall growth.
    Operating expenses were well controlled, supporting profit margins.
    Revenue recognition policies ensure accurate financial reporting.
    The company maintained workforce diversity across all departments.
    Blood group information is maintained for employee emergency contacts.
    """
    
    test_cases = [
        {
            "field": "Revenue",
            "value": "$115.5 million",
            "should_include_direct": ["total revenue reached $115.5 million"],
            "should_include_indirect": ["Revenue grew by 15%", "insurance premium collections", "Insurance premium revenue"],
            "should_exclude": ["workforce diversity", "Blood group information"]
        },
        {
            "field": "Net_Profit", 
            "value": "12% increase",
            "should_include_direct": ["Net profit after tax increased by 12%"],
            "should_include_indirect": ["Earnings per share rose 10%", "profit expansion", "Strong margin growth", "profit growth reflected"],
            "should_exclude": ["Revenue grew by 15%", "workforce diversity"]
        },
        {
            "field": "Blood_Group",
            "value": "O+",
            "should_include_direct": ["Blood group information"],
            "should_include_indirect": ["employee emergency contacts"],
            "should_exclude": ["Revenue grew", "profit expansion", "workforce diversity"]
        }
    ]
    
    print("Indirect Relation Test Results:")
    print("-" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        print("-" * 50)
        
        # Generate context with refined logic
        context, confidence = generate_context_for_field(field, value, financial_document)
        
        print(f"Generated Context (Confidence: {confidence:.3f}):")
        if context:
            print(f"  {context}")
        else:
            print("  (no relevant context found)")
        
        if context:
            context_lower = context.lower()
            
            # Check direct inclusions
            direct_found = 0
            for direct_term in test_case["should_include_direct"]:
                if direct_term.lower() in context_lower:
                    direct_found += 1
                    print(f"  ✅ Direct relation found: '{direct_term}'")
                else:
                    print(f"  ❌ Missing direct relation: '{direct_term}'")
            
            # Check indirect inclusions
            indirect_found = 0
            for indirect_term in test_case["should_include_indirect"]:
                if indirect_term.lower() in context_lower:
                    indirect_found += 1
                    print(f"  ✅ Indirect relation found: '{indirect_term}'")
                else:
                    print(f"  ⚠️  Missing indirect relation: '{indirect_term}'")
            
            # Check exclusions
            excluded_count = 0
            for exclude_term in test_case["should_exclude"]:
                if exclude_term.lower() not in context_lower:
                    excluded_count += 1
                    print(f"  ✅ Correctly excluded: '{exclude_term}'")
                else:
                    print(f"  ❌ Incorrectly included: '{exclude_term}'")
            
            # Overall assessment
            total_should_include = len(test_case["should_include_direct"]) + len(test_case["should_include_indirect"])
            total_found = direct_found + indirect_found
            inclusion_rate = total_found / total_should_include if total_should_include > 0 else 0
            exclusion_rate = excluded_count / len(test_case["should_exclude"]) if test_case["should_exclude"] else 1.0
            
            if inclusion_rate >= 0.7 and exclusion_rate >= 0.8:
                print(f"  🎯 EXCELLENT: High precision with indirect relation capture")
            elif inclusion_rate >= 0.5 and exclusion_rate >= 0.6:
                print(f"  ✅ GOOD: Decent relation capture with filtering")
            else:
                print(f"  ⚠️  NEEDS IMPROVEMENT: Low precision or missing relations")
        
        print()

def test_cross_domain_filtering():
    """Test filtering of cross-domain irrelevant content"""
    
    print("=" * 90)
    print("CROSS-DOMAIN FILTERING TEST")
    print("=" * 90)
    print()
    
    # Document with mixed domains that should be filtered
    mixed_domain_document = """
    Lokesh Kumar was born in Jaipur, Rajasthan, and his birthplace provides regional context.
    As an Indian national, his citizenship status is important for understanding his work authorization.
    His O+ blood group is noted for emergency contact purposes in medical records.
    Born in Jaipur and has O+ blood group, he completed his engineering degree.
    The company operates globally with diverse workforce across multiple regions.
    Revenue growth contributed to employee satisfaction and retention rates.
    Net profit margins improved due to operational efficiency and cost management.
    Blood money transactions are strictly prohibited under financial regulations.
    The average age of our user base indicates strong market penetration.
    Company age in the market demonstrates stability and customer trust.
    """
    
    test_cases = [
        {
            "field": "Citizenship",
            "value": "Indian national",
            "should_include": ["As an Indian national", "citizenship status", "work authorization"],
            "should_exclude": ["birthplace provides regional context", "O+ blood group", "engineering degree"]
        },
        {
            "field": "Blood_Group",
            "value": "O+",
            "should_include": ["O+ blood group", "emergency contact purposes", "medical records"],
            "should_exclude": ["Born in Jaipur", "citizenship status", "engineering degree", "blood money"]
        },
        {
            "field": "Net_Profit",
            "value": "improved margins",
            "should_include": ["Net profit margins improved", "operational efficiency", "cost management"],
            "should_exclude": ["employee satisfaction", "user base", "company age", "blood money"]
        }
    ]
    
    print("Cross-Domain Filtering Results:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        field = test_case["field"]
        value = test_case["value"]
        
        print(f"\nTest {i}: {field} = '{value}'")
        print("-" * 40)
        
        context, confidence = generate_context_for_field(field, value, mixed_domain_document)
        
        print(f"Generated Context (Confidence: {confidence:.3f}):")
        if context:
            print(f"  {context}")
        else:
            print("  (no relevant context found)")
        
        if context:
            context_lower = context.lower()
            
            # Check what should be included
            included_correctly = 0
            for include_term in test_case["should_include"]:
                if include_term.lower() in context_lower:
                    included_correctly += 1
                    print(f"  ✅ Correctly included: '{include_term}'")
                else:
                    print(f"  ❌ Missing expected: '{include_term}'")
            
            # Check what should be excluded
            excluded_correctly = 0
            for exclude_term in test_case["should_exclude"]:
                if exclude_term.lower() not in context_lower:
                    excluded_correctly += 1
                    print(f"  ✅ Correctly excluded: '{exclude_term}'")
                else:
                    print(f"  ⚠️  Incorrectly included: '{exclude_term}'")
            
            # Assessment
            inclusion_score = included_correctly / len(test_case["should_include"]) if test_case["should_include"] else 1.0
            exclusion_score = excluded_correctly / len(test_case["should_exclude"]) if test_case["should_exclude"] else 1.0
            
            if inclusion_score >= 0.7 and exclusion_score >= 0.8:
                print(f"  🎯 EXCELLENT: Precise cross-domain filtering")
            elif inclusion_score >= 0.5 and exclusion_score >= 0.6:
                print(f"  ✅ GOOD: Decent filtering with some issues")
            else:
                print(f"  ❌ POOR: Significant filtering problems")

def test_full_integration_refined():
    """Test full integration with refined context generation"""
    
    print("\n" + "=" * 90)
    print("FULL INTEGRATION TEST - REFINED CONTEXT GENERATION")
    print("=" * 90)
    print()
    
    # Comprehensive document with mixed content
    document_text = [
        "Life360 Inc. reported strong financial performance for Q4 2024.",
        "Revenue grew by 15% year-over-year, reflecting strong insurance premium collections.",
        "The company's total revenue reached $115.5 million in the quarter.",
        "Net profit after tax increased by 12% compared to FY22.",
        "Earnings per share rose 10%, reflecting profit expansion across all segments.",
        "Strong margin growth indicated improved profitability and operational efficiency.",
        "John Smith, CEO, was born in California and has extensive leadership experience.",
        "As an American citizen, his citizenship status supports global operations.",
        "His A+ blood group is recorded in company medical files for emergencies.",
        "The company operates globally with diverse workforce across multiple regions.",
        "Employee satisfaction surveys show positive correlation with revenue growth.",
        "Blood money transactions are strictly prohibited under financial regulations."
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
                    'Company_Name': 'Life360 Inc.',
                    'Revenue': '$115.5 million',
                    'Revenue_Growth': '15%',
                    'Net_Profit': '12% increase',
                    'CEO_Name': 'John Smith',
                    'Citizenship': 'American citizen',
                    'Blood_Group': 'A+'
                }
            }
        ],
        'processed_key_values': {
            'structured_key_values': {}
        },
        'processed_document_text': []
    }
    
    print("Testing refined integration...")
    enhanced_result = integrate_context_tracking(structured_data, processed_result)
    
    print("\nResults with Refined Context Generation:")
    print("-" * 70)
    
    for i, row in enumerate(enhanced_result.get('enhanced_data_with_context', []), 1):
        print(f"\n{i}. Field: {row['field']}")
        print(f"   Value: {row['value']}")
        print(f"   Has Context: {'✓' if row['has_context'] else '✗'}")
        print(f"   Confidence: {row.get('context_confidence', 0.0):.3f}")
        
        if row['context']:
            print(f"   Context: {row['context']}")
            
            # Quality assessment for key fields
            field = row['field']
            context_lower = row['context'].lower()
            
            if field == 'Revenue':
                if 'revenue' in context_lower and 'blood' not in context_lower:
                    print("   🎯 EXCELLENT: Revenue context without cross-domain contamination")
                elif 'revenue' in context_lower:
                    print("   ✅ GOOD: Revenue context found")
                else:
                    print("   ❌ POOR: Missing revenue context")
            
            elif field == 'Net_Profit':
                if 'profit' in context_lower and 'blood' not in context_lower and 'citizenship' not in context_lower:
                    print("   🎯 EXCELLENT: Profit context without cross-domain contamination")
                elif 'profit' in context_lower:
                    print("   ✅ GOOD: Profit context found")
                else:
                    print("   ❌ POOR: Missing profit context")
            
            elif field == 'Blood_Group':
                if 'blood group' in context_lower and 'revenue' not in context_lower and 'profit' not in context_lower:
                    print("   🎯 EXCELLENT: Blood group context without financial contamination")
                elif 'blood group' in context_lower:
                    print("   ⚠️  PARTIAL: Blood group found but may have contamination")
                else:
                    print("   ❌ POOR: Missing blood group context")
        else:
            print("   Context: (no relevant context found)")
    
    # Summary
    summary = enhanced_result.get('context_tracking_summary', {})
    print(f"\nRefined Context Generation Summary:")
    print(f"  Total fields: {summary.get('total_fields', 0)}")
    print(f"  Fields with context: {summary.get('fields_with_context', 0)}")
    print(f"  Context coverage: {summary.get('context_coverage_percentage', 0)}%")

if __name__ == "__main__":
    test_indirect_relation_capture()
    test_cross_domain_filtering()
    test_full_integration_refined()