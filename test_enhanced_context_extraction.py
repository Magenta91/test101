#!/usr/bin/env python3
"""
Test script for enhanced context extraction with clause-level trimming and improved numeric handling.
Tests the fixes for over-extended contexts, missed numeric contexts, and semantic over-inclusion.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import (
    generate_context_for_field,
    split_into_clauses,
    find_minimal_relevant_clause,
    normalize_field_name,
    extract_sentences_from_text
)

def test_clause_trimming():
    """Test clause-level trimming functionality"""
    print("=" * 80)
    print("CLAUSE-LEVEL TRIMMING TEST")
    print("=" * 80)
    
    # Test sentence with multiple clauses
    test_sentence = "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%, while the CEO said momentum continuing into the second half"
    
    print(f"Original sentence: {test_sentence}")
    print("-" * 60)
    
    clauses = split_into_clauses(test_sentence)
    print(f"Split into {len(clauses)} clauses:")
    for i, clause in enumerate(clauses):
        print(f"  {i+1}. {clause}")
    
    # Test finding minimal relevant clause
    field = "Underlying_NPAT_1HFY23"
    value = "AUD 46.7mn"
    
    best_clause, confidence = find_minimal_relevant_clause(clauses, field, value)
    print(f"\nBest clause for {field} = {value}:")
    print(f"  Clause: {best_clause}")
    print(f"  Confidence: {confidence:.3f}")

def test_field_normalization():
    """Test field name normalization"""
    print("\n" + "=" * 80)
    print("FIELD NAME NORMALIZATION TEST")
    print("=" * 80)
    
    test_fields = [
        "Underlying_NPAT_1HFY23",
        "Revenue_Growth_Percentage",
        "EBIT.Margin.Current.Period",
        "Pre-Tax-Profit-Amount",
        "FY23_Guidance_Low"
    ]
    
    for field in test_fields:
        normalized = normalize_field_name(field)
        print(f"{field:<30} -> {normalized}")

def test_enhanced_sentence_extraction():
    """Test enhanced sentence extraction with bullet point handling"""
    print("\n" + "=" * 80)
    print("ENHANCED SENTENCE EXTRACTION TEST")
    print("=" * 80)
    
    # Sample text with bullet points like AUB document
    sample_text = """
    AUB Group Limited (ASX: AUB) today announced its results for the six months ended 31 December 2022.
    
    Key highlights include:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents), up 13.3%
    
    CEO Michael Emmett said: "All parts of AUB Group performed strongly during 1H23 with momentum continuing into the second half."
    """
    
    sentences = extract_sentences_from_text(sample_text)
    
    print(f"Extracted {len(sentences)} sentences:")
    for i, (sentence, idx) in enumerate(sentences):
        print(f"  {i+1}. [{idx}] {sentence}")

def test_over_extended_context_fix():
    """Test that over-extended contexts are now properly trimmed"""
    print("\n" + "=" * 80)
    print("OVER-EXTENDED CONTEXT FIX TEST")
    print("=" * 80)
    
    # Simulate AUB document with CEO quotes and commentary
    aub_document = """
    AUB Group Limited (ASX: AUB) Financial Results - First Half FY23
    
    FINANCIAL HIGHLIGHTS:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share, up 13.3% from 15.0 cents
    
    CEO Michael Emmett commented: "All parts of AUB Group performed strongly during 1H23 with momentum continuing into the second half. We are pleased to announce these results and look forward to the full year outlook."
    
    The company's strategic initiatives and operational excellence have driven these results across all divisions.
    """
    
    test_cases = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn"),
        ("Underlying_NPAT_1HFY22", "AUD 30.6mn"),
        ("Earnings_Per_Share", "48.18 cents"),
        ("Interim_Dividend", "17.0 cents")
    ]
    
    for field, value in test_cases:
        print(f"\nTesting: {field} = {value}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, aub_document)
        
        if context:
            word_count = len(context.split())
            print(f"Context ({word_count} words, confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check if context is appropriately concise
            if word_count <= 15:
                print("  ✅ EXCELLENT: Very concise context")
            elif word_count <= 25:
                print("  ✅ GOOD: Reasonably concise context")
            elif word_count <= 40:
                print("  ⚠️  ACCEPTABLE: Moderate length context")
            else:
                print("  ❌ POOR: Context too verbose")
            
            # Check if CEO commentary is excluded
            if any(phrase in context.lower() for phrase in ['ceo', 'commented', 'said', 'pleased to announce', 'look forward']):
                print("  ❌ ISSUE: CEO commentary included")
            else:
                print("  ✅ GOOD: CEO commentary excluded")
                
        else:
            print("  ❌ No context generated")

def test_numeric_comparative_handling():
    """Test enhanced numeric handling with financial comparatives"""
    print("\n" + "=" * 80)
    print("NUMERIC COMPARATIVE HANDLING TEST")
    print("=" * 80)
    
    # Test document with various comparative patterns
    financial_text = """
    SEGMENT PERFORMANCE:
    Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    The EBIT margin improved to 35.2%, up 410 basis points from prior year.
    
    New Zealand Broking achieved pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    EBIT margin expanded to 38.4%, up 140 basis points.
    
    Technology investment costs were AUD 3.4mn (1HFY22: AUD 2.2mn).
    """
    
    test_cases = [
        ("Australian_Broking_Profit", "AUD 49.9mn"),
        ("Australian_Broking_Previous", "AUD 38.3mn"),
        ("EBIT_Margin", "35.2%"),
        ("NZ_Broking_Profit", "AUD 4.8mn"),
        ("Technology_Costs", "AUD 3.4mn")
    ]
    
    for field, value in test_cases:
        print(f"\nTesting: {field} = {value}")
        print("-" * 40)
        
        context, confidence = generate_context_for_field(field, value, financial_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check if comparative values are captured as units
            if "(" in context and ")" in context:
                print("  ✅ Comparative values captured as unit")
            else:
                print("  ⚠️  No comparative values found")
                
        else:
            print("  ❌ No context generated")

def test_anti_pattern_filtering():
    """Test enhanced anti-pattern filtering for financial commentary"""
    print("\n" + "=" * 80)
    print("ANTI-PATTERN FILTERING TEST")
    print("=" * 80)
    
    # Text with various types of commentary that should be filtered
    commentary_text = """
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    
    CEO Michael Emmett said: "We are pleased to announce these strong results and momentum continuing into the second half."
    
    The management believes the outlook remains positive and expects to deliver strong performance going forward.
    
    According to the chairman, the company performed strongly during the period with upgraded the outlook for the full year.
    """
    
    field = "Underlying_NPAT_1HFY23"
    value = "AUD 46.7mn"
    
    print(f"Testing: {field} = {value}")
    print("Source text contains CEO quotes and management commentary")
    print("-" * 60)
    
    context, confidence = generate_context_for_field(field, value, commentary_text)
    
    if context:
        print(f"Generated context (confidence: {confidence:.3f}):")
        print(f"  {context}")
        
        # Check for anti-pattern exclusion
        anti_patterns = ['said', 'pleased to announce', 'momentum continuing', 'believes', 'expects', 'according to', 'performed strongly']
        
        found_anti_patterns = [pattern for pattern in anti_patterns if pattern in context.lower()]
        
        if found_anti_patterns:
            print(f"  ❌ ISSUE: Anti-patterns found: {found_anti_patterns}")
        else:
            print("  ✅ EXCELLENT: Anti-patterns successfully filtered")
            
    else:
        print("  ❌ No context generated")

if __name__ == "__main__":
    print("ENHANCED CONTEXT EXTRACTION TESTS")
    print("=" * 80)
    
    test_clause_trimming()
    test_field_normalization()
    test_enhanced_sentence_extraction()
    test_over_extended_context_fix()
    test_numeric_comparative_handling()
    test_anti_pattern_filtering()
    
    print("\n" + "=" * 80)
    print("ENHANCED CONTEXT EXTRACTION TESTING COMPLETED")
    print("=" * 80)