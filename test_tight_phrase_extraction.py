#!/usr/bin/env python3
"""
Test script for tight phrase extraction with metric anchor detection.
Tests the ability to extract precise metric phrases around numeric values.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import (
    generate_context_for_field,
    extract_metric_phrase,
    get_financial_metric_anchors
)

def test_metric_anchor_detection():
    """Test financial metric anchor detection"""
    print("=" * 80)
    print("FINANCIAL METRIC ANCHOR DETECTION TEST")
    print("=" * 80)
    
    anchors = get_financial_metric_anchors()
    print(f"Total anchors: {len(anchors)}")
    print("Key anchors:", anchors[:10])
    
    # Test anchor detection in sample text
    sample_text = "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%"
    
    for anchor in anchors[:5]:
        if anchor.lower() in sample_text.lower():
            print(f"✅ Found anchor '{anchor}' in sample text")
        else:
            print(f"❌ Anchor '{anchor}' not found")

def test_tight_phrase_extraction():
    """Test tight phrase extraction around numeric values"""
    print("\n" + "=" * 80)
    print("TIGHT PHRASE EXTRACTION TEST")
    print("=" * 80)
    
    # Sample AUB financial document text
    aub_text = """
    AUB Group Limited (ASX: AUB) today announced its results for the six months ended 31 December 2022.
    
    Key highlights include:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents), up 13.3%
    • Tysers contributed 3 months to 1HFY23 results and exceeded forecasts
    • FY23 upgraded underlying NPAT1 guidance of AUD 112.9mn to AUD 121.4mn
    
    SEGMENT PERFORMANCE:
    Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    The EBIT margin improved to 35.2%, up 410 basis points from prior year.
    
    New Zealand Broking achieved pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    EBIT margin expanded to 38.4%, up 140 basis points.
    
    Technology investment costs were AUD 3.4mn (1HFY22: AUD 2.2mn).
    Leverage ratio as of 31 December 2022 was 2.74.
    """
    
    anchors = get_financial_metric_anchors()
    
    test_values = [
        ("46.7mn", "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn)"),
        ("30.6mn", "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn)"),
        ("48.18 cents", "Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)"),
        ("17.0 cents", "Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents)"),
        ("49.9mn", "pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn)"),
        ("35.2%", "EBIT margin improved to 35.2%"),
        ("4.8mn", "pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn)"),
        ("2.74", "Leverage ratio as of 31 December 2022 was 2.74")
    ]
    
    for value, expected_pattern in test_values:
        print(f"\nTesting value: {value}")
        print(f"Expected pattern: {expected_pattern}")
        print("-" * 60)
        
        phrases = extract_metric_phrase(aub_text, value, anchors)
        
        if phrases:
            for i, (phrase, confidence) in enumerate(phrases):
                print(f"  Phrase {i+1} (confidence: {confidence:.3f}):")
                print(f"    {phrase}")
                
                # Check if the phrase contains key elements from expected pattern
                if any(key_word in phrase.lower() for key_word in expected_pattern.lower().split()[:3]):
                    print("    ✅ Contains expected elements")
                else:
                    print("    ⚠️  May not match expected pattern")
        else:
            print("  ❌ No phrases extracted")

def test_comparative_value_capture():
    """Test that comparative values in brackets are captured"""
    print("\n" + "=" * 80)
    print("COMPARATIVE VALUE CAPTURE TEST")
    print("=" * 80)
    
    comparative_text = """
    Financial Results Summary:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Revenue growth of 15% (1HFY22: 12%), showing improvement
    • EBIT margin at 35.2% (1HFY22: 31.1%), up 410bps
    """
    
    anchors = get_financial_metric_anchors()
    
    test_cases = [
        ("46.7mn", "Should capture both current and comparative values"),
        ("30.6mn", "Should capture the same phrase as 46.7mn"),
        ("15%", "Should capture revenue growth with comparison"),
        ("35.2%", "Should capture EBIT margin with comparison")
    ]
    
    for value, description in test_cases:
        print(f"\nTesting: {value} - {description}")
        print("-" * 50)
        
        phrases = extract_metric_phrase(comparative_text, value, anchors)
        
        if phrases:
            best_phrase, confidence = phrases[0]
            print(f"Extracted phrase (conf: {confidence:.3f}):")
            print(f"  {best_phrase}")
            
            # Check if comparative values are included
            if "(" in best_phrase and ")" in best_phrase:
                print("  ✅ Comparative values captured")
            else:
                print("  ⚠️  Comparative values may be missing")
        else:
            print("  ❌ No phrase extracted")

def test_integrated_tight_extraction():
    """Test integrated tight phrase extraction in generate_context_for_field"""
    print("\n" + "=" * 80)
    print("INTEGRATED TIGHT PHRASE EXTRACTION TEST")
    print("=" * 80)
    
    # AUB document text
    document_text = """
    AUB Group Limited (ASX: AUB) Financial Results - First Half FY23
    
    FINANCIAL HIGHLIGHTS:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)  
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share, up 13.3% from 15.0 cents
    • Revenue growth of 15% year-over-year to AUD 180.5mn
    
    SEGMENT PERFORMANCE:
    Australian Broking delivered strong pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    The EBIT margin improved to 35.2%, up 410 basis points from prior year.
    
    New Zealand Broking achieved pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    EBIT margin expanded to 38.4%, up 140 basis points.
    
    GUIDANCE:
    FY23 underlying NPAT1 guidance upgraded to AUD 112.9mn to AUD 121.4mn.
    Leverage ratio as of 31 December 2022 was 2.74.
    Technology investment costs were AUD 3.4mn (1HFY22: AUD 2.2mn).
    """
    
    test_cases = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn", "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn)"),
        ("Underlying_NPAT_1HFY22", "AUD 30.6mn", "Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn)"),
        ("Earnings_Per_Share", "48.18 cents", "Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)"),
        ("Australian_Broking_Profit", "AUD 49.9mn", "pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn)"),
        ("EBIT_Margin", "35.2%", "EBIT margin improved to 35.2%"),
        ("FY23_Guidance_Low", "AUD 112.9mn", "FY23 underlying NPAT1 guidance upgraded to AUD 112.9mn to AUD 121.4mn"),
        ("Leverage_Ratio", "2.74", "Leverage ratio as of 31 December 2022 was 2.74")
    ]
    
    print("Testing tight phrase extraction through generate_context_for_field:")
    print("=" * 70)
    
    for field, value, expected_elements in test_cases:
        print(f"\nField: {field}")
        print(f"Value: {value}")
        print(f"Expected elements: {expected_elements}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, document_text)
        
        if context:
            print(f"Generated context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Validate tightness - should be concise and focused
            word_count = len(context.split())
            if word_count <= 15:
                print(f"  ✅ Tight extraction ({word_count} words)")
            elif word_count <= 25:
                print(f"  ⚠️  Moderately tight ({word_count} words)")
            else:
                print(f"  ❌ Too verbose ({word_count} words)")
            
            # Check if value is present
            if value.replace("AUD ", "").replace("mn", "").replace("cents", "").strip() in context:
                print("  ✅ Value found in context")
            else:
                print("  ⚠️  Value not clearly found in context")
                
        else:
            print("  ❌ No context generated")

def test_anchor_vs_window_comparison():
    """Compare anchor-based vs window-based extraction"""
    print("\n" + "=" * 80)
    print("ANCHOR-BASED VS WINDOW-BASED EXTRACTION COMPARISON")
    print("=" * 80)
    
    test_text = """
    The company reported strong financial performance with underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), representing a significant improvement. This growth was driven by operational efficiency and market expansion strategies implemented throughout the period.
    """
    
    anchors = get_financial_metric_anchors()
    value = "46.7mn"
    
    print(f"Testing value: {value}")
    print(f"Source text: {test_text.strip()}")
    print("-" * 60)
    
    # Test anchor-based extraction
    anchor_phrases = extract_metric_phrase(test_text, value, anchors)
    print("\nAnchor-based extraction:")
    if anchor_phrases:
        phrase, conf = anchor_phrases[0]
        print(f"  Phrase: {phrase}")
        print(f"  Confidence: {conf:.3f}")
        print(f"  Length: {len(phrase.split())} words")
    else:
        print("  No anchor-based phrase found")
    
    # Compare with full context generation
    print("\nFull context generation:")
    context, confidence = generate_context_for_field("NPAT", value, test_text)
    print(f"  Context: {context}")
    print(f"  Confidence: {confidence:.3f}")
    print(f"  Length: {len(context.split())} words")

if __name__ == "__main__":
    print("TIGHT PHRASE EXTRACTION WITH METRIC ANCHORS TESTS")
    print("=" * 80)
    
    test_metric_anchor_detection()
    test_tight_phrase_extraction()
    test_comparative_value_capture()
    test_integrated_tight_extraction()
    test_anchor_vs_window_comparison()
    
    print("\n" + "=" * 80)
    print("TIGHT PHRASE EXTRACTION TESTING COMPLETED")
    print("=" * 80)