#!/usr/bin/env python3
"""
Test script for AUB-specific context extraction fixes addressing:
1. PDF special bullet characters (†, ‡, ••)
2. OCR artifacts like "NPAT?" and "per share? of"
3. Fragmented contexts missing metric names
4. Over-inclusion across sections
5. CEO quote handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import (
    generate_context_for_field,
    clean_ocr_artifacts,
    extract_sentences_from_text,
    find_minimal_relevant_clause,
    split_into_clauses
)

def test_pdf_special_characters():
    """Test handling of PDF special bullet characters"""
    print("=" * 80)
    print("PDF SPECIAL CHARACTERS TEST")
    print("=" * 80)
    
    # Simulate AUB PDF text with special characters
    aub_pdf_text = """
    Key highlights include:
    † Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    † Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    † Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    
    AUSTRALIAN BROKING:
    •• Pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%
    •• EBIT margin of 35.2%, up 410bps from 1HFY22
    
    NEW ZEALAND BROKING:
    •• Pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%
    """
    
    sentences = extract_sentences_from_text(aub_pdf_text)
    
    print(f"Extracted {len(sentences)} sentences from PDF text:")
    for i, (sentence, idx) in enumerate(sentences):
        print(f"  {i+1}. [{idx}] {sentence}")
        
        # Check for proper bullet handling
        if sentence.startswith(('†', '••', '•')):
            print("    ❌ Bullet character not cleaned")
        else:
            print("    ✅ Bullet character cleaned")

def test_ocr_artifact_fixes():
    """Test enhanced OCR artifact cleaning"""
    print("\n" + "=" * 80)
    print("ENHANCED OCR ARTIFACT FIXES TEST")
    print("=" * 80)
    
    test_cases = [
        ("Underlying NPAT? of AUD 46.7mn", "Should remove ? from NPAT"),
        ("per share? of 48.18 cents", "Should fix 'per share? of'"),
        ("Tax? of AUD 0.4mn", "Should fix 'Tax? of'"),
        ("profit? of AUD 49.9mn", "Should fix 'profit? of'"),
        ("earnings? per share", "Should remove ? from earnings"),
    ]
    
    for dirty_text, description in test_cases:
        cleaned = clean_ocr_artifacts(dirty_text)
        print(f"\nTest: {description}")
        print(f"  Input:  '{dirty_text}'")
        print(f"  Output: '{cleaned}'")
        
        if '?' in cleaned:
            print("  ❌ OCR artifacts still present")
        else:
            print("  ✅ OCR artifacts cleaned")

def test_fragmented_context_completion():
    """Test completion of fragmented contexts"""
    print("\n" + "=" * 80)
    print("FRAGMENTED CONTEXT COMPLETION TEST")
    print("=" * 80)
    
    # Simulate fragmented text that might result from poor clause splitting
    fragmented_text = """
    Financial highlights:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn)
    """
    
    test_cases = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn", "Should include 'Underlying NPAT1'"),
        ("Reported_NPAT_1HFY23", "AUD 0.4mn", "Should include 'Reported NPAT'"),
        ("Australian_Broking_Profit", "AUD 49.9mn", "Should include 'pre-tax profit'")
    ]
    
    for field, value, expectation in test_cases:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, fragmented_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for completeness
            context_lower = context.lower()
            if field.startswith("Underlying") and ("underlying" in context_lower or "npat" in context_lower):
                print("  ✅ Complete: Contains metric identifier")
            elif field.startswith("Reported") and ("reported" in context_lower or "npat" in context_lower):
                print("  ✅ Complete: Contains metric identifier")
            elif "profit" in context_lower:
                print("  ✅ Complete: Contains metric identifier")
            else:
                print("  ⚠️  May be incomplete - check for metric name")
                
        else:
            print("  ❌ No context generated")

def test_section_isolation():
    """Test that contexts don't bleed across sections"""
    print("\n" + "=" * 80)
    print("SECTION ISOLATION TEST")
    print("=" * 80)
    
    # Multi-section text that could cause cross-contamination
    multi_section_text = """
    AUSTRALIAN BROKING:
    Pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    EBIT margin of 35.2%, up 410bps from 1HFY22.
    
    These increases were driven by organic and bolt-on acquisition growth.
    
    NEW ZEALAND BROKING:
    Pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    EBIT margin of 38.4%, up 140bps from 1HFY22.
    
    CAPITAL MANAGEMENT:
    Leverage ratio of 2.74 at 31 December 2022.
    Cash and undrawn debt facilities of AUD 50.3mn.
    """
    
    isolation_tests = [
        ("Australian_Broking_Profit", "AUD 49.9mn", "Should NOT include NZ or Capital sections"),
        ("New_Zealand_Profit", "AUD 4.8mn", "Should NOT include Australian or Capital sections"),
        ("Leverage_Ratio", "2.74", "Should NOT include profit information")
    ]
    
    for field, value, expectation in isolation_tests:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, multi_section_text)
        
        if context:
            word_count = len(context.split())
            print(f"Context ({word_count} words, confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for cross-section contamination
            contamination_phrases = [
                'driven by', 'these increases', 'organic and bolt-on',
                'capital management', 'cash and undrawn', 'new zealand', 'australian'
            ]
            
            # Remove expected phrases for the specific field
            if 'australian' in field.lower():
                contamination_phrases = [p for p in contamination_phrases if 'australian' not in p]
            elif 'new_zealand' in field.lower():
                contamination_phrases = [p for p in contamination_phrases if 'new zealand' not in p]
            
            found_contamination = [phrase for phrase in contamination_phrases if phrase in context.lower()]
            
            if found_contamination:
                print(f"  ❌ Cross-section contamination: {found_contamination}")
            else:
                print("  ✅ No cross-section contamination")
                
            if word_count <= 15:
                print("  ✅ Appropriately concise")
            else:
                print("  ⚠️  May be too verbose")
                
        else:
            print("  ❌ No context generated")

def test_ceo_quote_handling():
    """Test CEO quote and statement handling"""
    print("\n" + "=" * 80)
    print("CEO QUOTE HANDLING TEST")
    print("=" * 80)
    
    # Text with CEO quotes
    ceo_text = """
    Financial highlights include strong performance across all divisions.
    
    CEO Michael Emmett said: "All parts of AUB Group performed strongly during 1H23 with momentum continuing into the second half. We are pleased with these results and look forward to continued growth."
    
    The Board has determined a fully franked interim dividend of 17.0 cents per share.
    """
    
    quote_tests = [
        ("CEO_Statement", "performed strongly", "Should capture full CEO quote"),
        ("CEO_Comment", "momentum continuing", "Should capture CEO commentary"),
        ("Management_Quote", "pleased with results", "Should capture management statement")
    ]
    
    for field, value, expectation in quote_tests:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, ceo_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for quote indicators
            if 'said:' in context or 'commented:' in context:
                print("  ✅ Contains quote indicator")
            else:
                print("  ⚠️  Missing quote indicator")
                
            # Check for completeness
            if len(context) > 50:  # Quotes should be longer
                print("  ✅ Appropriate length for quote")
            else:
                print("  ⚠️  May be too short for complete quote")
                
        else:
            print("  ❌ No context generated")

def test_quality_control():
    """Test enhanced quality control and artifact rejection"""
    print("\n" + "=" * 80)
    print("QUALITY CONTROL TEST")
    print("=" * 80)
    
    # Text with various quality issues
    quality_test_text = """
    • Underlying NPAT? of AUD 46.7mn + Underlying earnings per share? of 48.18 cents
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Pre-tax profit of AUD 49.9mn, up 30.3%
    """
    
    quality_tests = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn", "Should reject contexts with '?' or '+'"),
        ("Earnings_Per_Share", "48.18 cents", "Should reject contexts with artifacts"),
        ("Reported_NPAT_1HFY23", "AUD 0.4mn", "Should accept clean contexts")
    ]
    
    for field, value, expectation in quality_tests:
        print(f"\nTesting: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 40)
        
        context, confidence = generate_context_for_field(field, value, quality_test_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for artifacts
            if '+' in context or '?' in context:
                print("  ❌ FAILED: Contains artifacts that should be rejected")
            else:
                print("  ✅ PASSED: Clean context without artifacts")
                
            # Check confidence
            if confidence >= 0.6:
                print("  ✅ PASSED: Meets confidence threshold")
            else:
                print("  ❌ FAILED: Below confidence threshold")
                
        else:
            print("  ✅ PASSED: Correctly rejected low-quality context")

if __name__ == "__main__":
    print("AUB-SPECIFIC CONTEXT EXTRACTION FIXES TESTS")
    print("=" * 80)
    
    test_pdf_special_characters()
    test_ocr_artifact_fixes()
    test_fragmented_context_completion()
    test_section_isolation()
    test_ceo_quote_handling()
    test_quality_control()
    
    print("\n" + "=" * 80)
    print("AUB-SPECIFIC FIXES TESTING COMPLETED")
    print("=" * 80)