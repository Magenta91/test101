#!/usr/bin/env python3
"""
Test script for numeric-aware context generation enhancements.
Tests the ability to capture contextual phrases for numeric and tabular values.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import (
    generate_context_for_field,
    is_numeric_value,
    extract_numeric_context_window,
    extract_numeric_pair_context
)

def test_numeric_detection():
    """Test numeric value detection"""
    print("=" * 80)
    print("NUMERIC VALUE DETECTION TEST")
    print("=" * 80)
    
    test_cases = [
        ("46.7mn", True),
        ("AUD 46.7 million", True),
        ("15%", True),
        ("$115.5 million", True),
        ("30.6mn", True),
        ("12% increase", True),
        ("John Smith", False),
        ("Engineering degree", False),
        ("O+ blood group", False),
        ("2.74", True),
        ("17.0 cents", True),
        ("AUD 112.9mn to AUD 121.4mn", True)
    ]
    
    for value, expected in test_cases:
        result = is_numeric_value(value)
        status = "✅" if result == expected else "❌"
        print(f"{status} {value:<25} -> {result} (expected: {expected})")

def test_numeric_window_extraction():
    """Test numeric context window extraction"""
    print("\n" + "=" * 80)
    print("NUMERIC WINDOW EXTRACTION TEST")
    print("=" * 80)
    
    # Sample financial document text
    financial_text = """
    AUB Group Limited (ASX: AUB) today announced its results for the six months ended 31 December 2022.
    
    Key highlights include:
    • Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), up 52.6%
    • Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents)
    • Reported NPAT of AUD 0.4mn (1HFY22: AUD 29.7mn)
    • Interim dividend of 17.0 cents per share (1HFY22: 15.0 cents), up 13.3%
    • Tysers contributed 3 months to 1HFY23 results and exceeded forecasts
    • FY23 upgraded underlying NPAT1 guidance of AUD 112.9mn to AUD 121.4mn
    
    Australian Broking delivered pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    New Zealand Broking achieved pre-tax profit of AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    """
    
    test_values = [
        "46.7mn",
        "30.6mn", 
        "48.18 cents",
        "17.0 cents",
        "49.9mn",
        "38.3mn",
        "4.8mn"
    ]
    
    for value in test_values:
        print(f"\nTesting value: {value}")
        print("-" * 50)
        contexts = extract_numeric_context_window(value, financial_text)
        
        if contexts:
            for i, (context, confidence) in enumerate(contexts):
                print(f"  Context {i+1} (confidence: {confidence:.3f}):")
                print(f"    {context}")
        else:
            print("  No context found")

def test_numeric_pair_context():
    """Test numeric pair context extraction"""
    print("\n" + "=" * 80)
    print("NUMERIC PAIR CONTEXT EXTRACTION TEST")
    print("=" * 80)
    
    # Sample text with comparative numeric pairs
    comparative_text = """
    Financial Performance Summary:
    
    Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), representing a 52.6% increase.
    Underlying earnings per share of 48.18 cents (1HFY22: 40.30 cents).
    Australian Broking pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    New Zealand operations achieved AUD 4.8mn (1HFY22: AUD 3.5mn), up 34.6%.
    Interim dividend declared at 17.0 cents per share (1HFY22: 15.0 cents).
    """
    
    test_values = [
        "46.7mn",
        "30.6mn",
        "49.9mn", 
        "38.3mn",
        "4.8mn",
        "3.5mn"
    ]
    
    for value in test_values:
        print(f"\nTesting value: {value}")
        print("-" * 50)
        contexts = extract_numeric_pair_context(value, comparative_text)
        
        if contexts:
            for i, (context, confidence) in enumerate(contexts):
                print(f"  Context {i+1} (confidence: {confidence:.3f}):")
                print(f"    {context}")
        else:
            print("  No pair context found")

def test_integrated_numeric_context():
    """Test integrated numeric context generation"""
    print("\n" + "=" * 80)
    print("INTEGRATED NUMERIC CONTEXT GENERATION TEST")
    print("=" * 80)
    
    # Comprehensive financial document
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
    """
    
    test_cases = [
        ("Underlying_NPAT_1HFY23", "AUD 46.7mn"),
        ("Underlying_NPAT_1HFY22", "AUD 30.6mn"),
        ("Earnings_Per_Share", "48.18 cents"),
        ("Interim_Dividend", "17.0 cents"),
        ("Australian_Broking_Profit", "AUD 49.9mn"),
        ("Australian_Broking_Previous", "AUD 38.3mn"),
        ("EBIT_Margin", "35.2%"),
        ("NZ_Broking_Profit", "AUD 4.8mn"),
        ("FY23_Guidance_Low", "AUD 112.9mn"),
        ("FY23_Guidance_High", "AUD 121.4mn"),
        ("Leverage_Ratio", "2.74")
    ]
    
    print("Testing numeric-aware context generation:")
    print("=" * 60)
    
    for field, value in test_cases:
        print(f"\nField: {field}")
        print(f"Value: {value}")
        print("-" * 40)
        
        context, confidence = generate_context_for_field(field, value, document_text)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Validate that the context contains the value
            if value.replace("AUD ", "").replace("mn", "").replace("cents", "").strip() in context:
                print("  ✅ Value found in context")
            else:
                print("  ⚠️  Value not found in context")
        else:
            print("  ❌ No context generated")

def test_comparative_context_capture():
    """Test that both values in comparative pairs get the same context"""
    print("\n" + "=" * 80)
    print("COMPARATIVE CONTEXT CAPTURE TEST")
    print("=" * 80)
    
    document_text = """
    Key Financial Metrics:
    Underlying NPAT1 of AUD 46.7mn (1HFY22: AUD 30.6mn), representing strong growth.
    Australian Broking pre-tax profit of AUD 49.9mn (1HFY22: AUD 38.3mn), up 30.3%.
    """
    
    comparative_pairs = [
        ("Current_NPAT", "46.7mn", "Previous_NPAT", "30.6mn"),
        ("Current_Broking", "49.9mn", "Previous_Broking", "38.3mn")
    ]
    
    for current_field, current_value, previous_field, previous_value in comparative_pairs:
        print(f"\nTesting comparative pair:")
        print(f"  {current_field}: {current_value}")
        print(f"  {previous_field}: {previous_value}")
        print("-" * 50)
        
        current_context, current_conf = generate_context_for_field(current_field, current_value, document_text)
        previous_context, previous_conf = generate_context_for_field(previous_field, previous_value, document_text)
        
        print(f"Current context (conf: {current_conf:.3f}):")
        print(f"  {current_context}")
        print(f"Previous context (conf: {previous_conf:.3f}):")
        print(f"  {previous_context}")
        
        # Check if both contexts capture the comparative information
        if current_value.replace("mn", "") in current_context and previous_value.replace("mn", "") in current_context:
            print("  ✅ Current context captures both values")
        else:
            print("  ⚠️  Current context incomplete")
            
        if current_value.replace("mn", "") in previous_context and previous_value.replace("mn", "") in previous_context:
            print("  ✅ Previous context captures both values")
        else:
            print("  ⚠️  Previous context incomplete")

if __name__ == "__main__":
    print("NUMERIC-AWARE CONTEXT GENERATION TESTS")
    print("=" * 80)
    
    test_numeric_detection()
    test_numeric_window_extraction()
    test_numeric_pair_context()
    test_integrated_numeric_context()
    test_comparative_context_capture()
    
    print("\n" + "=" * 80)
    print("NUMERIC CONTEXT TESTING COMPLETED")
    print("=" * 80)