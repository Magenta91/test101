#!/usr/bin/env python3
"""
Test script for final context extraction improvements addressing:
1. Fragmented/incomplete contexts
2. Over-inclusion of adjacent text
3. OCR artifact handling
4. Context deduplication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import (
    generate_context_for_field,
    clean_ocr_artifacts,
    clean_segment_artifacts,
    extract_sentences_from_text,
    split_into_clauses,
    find_minimal_relevant_clause
)

def test_ocr_artifact_cleaning():
    """Test OCR artifact cleaning functionality"""
    print("=" * 80)
    print("OCR ARTIFACT CLEANING TEST")
    print("=" * 80)
    
    test_cases = [
        ("Underlying NPAT? of AUD 46.7mn", "Underlying NPAT of AUD 46.7mn"),
        ("EPS? per share of 48.18 cents", "EPS per share of 48.18 cents"),
        ("Revenue? grew by 15%", "Revenue grew by 15%"),
        ("EBIT? margin improved", "EBIT margin improved"),
        ("Profit? after tax", "Profit after tax")
    ]
    
    for dirty_text, expected in test_cases:
        cleaned = clean_ocr_artifacts(dirty_text)
        status = "✅" if cleaned == expected else "❌"
        print(f"{status} '{dirty_text}' -> '{cleaned}' (expected: '{expected}')")

def test_fragmented_context_fix():
    """Test that fragmented contexts are now complete"""
    print("\n" + "=" * 80)
    print("FRAGMENTED CONTEXT FIX TEST")
    print("=" * 80)
    
    # Simulate AUB document with potential fragmentation issues
    aub_text = """
    Key highlights include:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents), up 13.3%
    
    Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    The EBIT margin improved to 35.2%, up 410 basis points from prior year.
    """
    
    test_cases = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn", "Should include 'Underlying NPAT1'"),
        ("Underlying_NPAT_1HFY22", "AUD 30.6mn", "Should be same complete phrase"),
        ("Reported_NPAT_1HFY23", "AUD 0.4mn", "Should include 'Reported NPAT'"),
        ("Australian_Broking_Profit", "AUD 49.9mn", "Should include 'pre-tax profit'")
    ]
    
    for field, value, expectation in test_cases:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, aub_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for completeness
            if field.startswith("Underlying_NPAT") and "underlying npat" in context.lower():
                print("  ✅ Complete: Contains metric name")
            elif field.startswith("Reported_NPAT") and "reported npat" in context.lower():
                print("  ✅ Complete: Contains metric name")
            elif field.startswith("Australian_Broking") and "profit" in context.lower():
                print("  ✅ Complete: Contains metric name")
            else:
                print("  ⚠️  May be incomplete - check metric name inclusion")
                
            # Check for comparative values
            if "(" in context and ")" in context:
                print("  ✅ Complete: Contains comparative values")
            else:
                print("  ⚠️  Missing comparative values")
                
        else:
            print("  ❌ No context generated")

def test_over_inclusion_prevention():
    """Test prevention of over-inclusion of adjacent text"""
    print("\n" + "=" * 80)
    print("OVER-INCLUSION PREVENTION TEST")
    print("=" * 80)
    
    # Text with multiple sections that could cause over-inclusion
    multi_section_text = """
    AUSTRALIAN BROKING:
    • Pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%
    • EBIT margin of 35.2%, up 410bps from 1HFY22
    
    These increases were driven by organic and bolt-on acquisition growth.
    
    NEW ZEALAND BROKING:
    • Pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%
    • EBIT margin of 38.4%, up 140bps from 1HFY22
    
    CAPITAL MANAGEMENT:
    • Leverage ratio of 2.74 at 31 December 2022
    • Cash and undrawn debt facilities of AUD 50.3mn
    """
    
    test_cases = [
        ("Australian_Broking_Profit", "AUD 49.9mn", "Should NOT include NZ section"),
        ("New_Zealand_Profit", "AUD 4.8mn", "Should NOT include Australian section"),
        ("Leverage_Ratio", "2.74", "Should NOT include cash facilities")
    ]
    
    for field, value, expectation in test_cases:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, multi_section_text)
        
        if context:
            word_count = len(context.split())
            print(f"Context ({word_count} words, confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for over-inclusion indicators
            over_inclusion_phrases = [
                'driven by', 'these increases', 'organic and bolt-on',
                'capital management', 'cash and undrawn'
            ]
            
            found_over_inclusion = [phrase for phrase in over_inclusion_phrases if phrase in context.lower()]
            
            if found_over_inclusion:
                print(f"  ❌ Over-inclusion detected: {found_over_inclusion}")
            else:
                print("  ✅ No over-inclusion detected")
                
            if word_count <= 20:
                print("  ✅ Appropriately concise")
            else:
                print("  ⚠️  May be too verbose")
                
        else:
            print("  ❌ No context generated")

def test_clause_preservation():
    """Test that financial comparatives are preserved as complete units"""
    print("\n" + "=" * 80)
    print("CLAUSE PRESERVATION TEST")
    print("=" * 80)
    
    # Test sentence with financial comparative that should be preserved
    test_sentence = "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%, while management expects continued growth"
    
    print(f"Original sentence:")
    print(f"  {test_sentence}")
    print()
    
    clauses = split_into_clauses(test_sentence)
    print(f"Split into {len(clauses)} clauses:")
    for i, clause in enumerate(clauses):
        print(f"  {i+1}. {clause}")
    
    # Test finding the best clause
    field = "Underlying_NPAT_1HFY23"
    value = "AUD 46.7mn"
    
    best_clause, confidence = find_minimal_relevant_clause(clauses, field, value)
    print(f"\nBest clause for {field} = {value}:")
    print(f"  Clause: {best_clause}")
    print(f"  Confidence: {confidence:.3f}")
    
    # Validate the clause contains both metric and comparative
    if "underlying npat" in best_clause.lower() and "1hfy22" in best_clause.lower():
        print("  ✅ Complete: Contains both metric name and comparative")
    else:
        print("  ⚠️  May be incomplete")

def test_enhanced_sentence_extraction():
    """Test enhanced sentence extraction with artifact cleaning"""
    print("\n" + "=" * 80)
    print("ENHANCED SENTENCE EXTRACTION TEST")
    print("=" * 80)
    
    # Text with OCR artifacts and formatting issues
    messy_text = """
    Key highlights include:
    • Underlying NPAT? of AUD 46.7mn (1HFY22: AUD 30.6mn) + Underlying earnings per share? of 48.18 cents
    • Reported NPAT? of AUD 0.4mn + Interim dividend of 17.0 cents
    
    CEO Michael Emmett said: "Strong performance continues."
    """
    
    sentences = extract_sentences_from_text(messy_text)
    
    print(f"Extracted {len(sentences)} sentences:")
    for i, (sentence, idx) in enumerate(sentences):
        print(f"  {i+1}. [{idx}] {sentence}")
        
        # Check for artifact cleaning
        if "?" in sentence:
            print("    ⚠️  OCR artifacts still present")
        else:
            print("    ✅ Clean text")

def test_context_precision():
    """Test overall context precision and quality"""
    print("\n" + "=" * 80)
    print("CONTEXT PRECISION TEST")
    print("=" * 80)
    
    # Comprehensive test document
    comprehensive_text = """
    AUB Group Limited (ASX: AUB) Financial Results - First Half FY23
    
    FINANCIAL HIGHLIGHTS:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents), up 13.3%
    
    CEO Michael Emmett commented: "All parts of AUB Group performed strongly during 1H23 with momentum continuing into the second half."
    
    SEGMENT PERFORMANCE:
    Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    The EBIT margin improved to 35.2%, up 410 basis points from prior year.
    
    These increases were driven by organic and bolt-on acquisition growth across all divisions.
    """
    
    precision_tests = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn"),
        ("Earnings_Per_Share", "48.18 cents"),
        ("Australian_Broking_Profit", "AUD 49.9mn"),
        ("EBIT_Margin", "35.2%")
    ]
    
    print("Testing precision and quality of generated contexts:")
    print("=" * 60)
    
    for field, value in precision_tests:
        print(f"\nField: {field}")
        print(f"Value: {value}")
        print("-" * 40)
        
        context, confidence = generate_context_for_field(field, value, comprehensive_text)
        
        if context:
            word_count = len(context.split())
            print(f"Context ({word_count} words, confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Quality checks
            quality_score = 0
            
            # Check 1: Contains the value
            if value.replace("AUD ", "").replace("mn", "").replace("cents", "").strip() in context:
                quality_score += 1
                print("  ✅ Contains target value")
            else:
                print("  ❌ Missing target value")
            
            # Check 2: Appropriate length (5-25 words)
            if 5 <= word_count <= 25:
                quality_score += 1
                print("  ✅ Appropriate length")
            else:
                print("  ⚠️  Length may be suboptimal")
            
            # Check 3: No CEO commentary
            if not any(phrase in context.lower() for phrase in ['ceo', 'commented', 'said', 'momentum']):
                quality_score += 1
                print("  ✅ No CEO commentary")
            else:
                print("  ❌ Contains CEO commentary")
            
            # Check 4: High confidence
            if confidence >= 0.8:
                quality_score += 1
                print("  ✅ High confidence")
            else:
                print("  ⚠️  Moderate confidence")
            
            print(f"  Quality Score: {quality_score}/4")
            
        else:
            print("  ❌ No context generated")

if __name__ == "__main__":
    print("FINAL CONTEXT EXTRACTION IMPROVEMENTS TESTS")
    print("=" * 80)
    
    test_ocr_artifact_cleaning()
    test_fragmented_context_fix()
    test_over_inclusion_prevention()
    test_clause_preservation()
    test_enhanced_sentence_extraction()
    test_context_precision()
    
    print("\n" + "=" * 80)
    print("FINAL IMPROVEMENTS TESTING COMPLETED")
    print("=" * 80)