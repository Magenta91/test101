#!/usr/bin/env python3
"""
Test Precision Improvements for Context Extraction
Tests the specific issues mentioned: mismatches, trimmed contexts, over-inclusion, truncation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context_tracker import generate_context_for_field, handle_truncation_and_chopping

def test_mismatch_prevention():
    """Test prevention of field-value mismatches"""
    print("="*80)
    print("MISMATCH PREVENTION TEST")
    print("="*80)
    
    # Test document with potential mismatch scenarios
    document = """
    The company reported results for the period 1HFY23. Technology investments required significant 
    investment costs during the period. Performance showed improvement across all divisions.
    Fully franked interim dividend of 17.0 cents per share (1HFY22: 17.0 cps) was declared.
    Life360, Inc. reported strong revenue growth of 33% YoY reaching $95.2 million.
    """
    
    test_cases = [
        ("Period", "1HFY23", "Should NOT match dividend context"),
        ("Company", "Life360, Inc.", "Should NOT match revenue snippet"),
        ("Technology_Impact", "investment costs", "Should NOT match dividend"),
        ("Interim_Dividend", "17.0 cents", "Should correctly match dividend")
    ]
    
    for field, value, expectation in test_cases:
        print(f"Testing: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, document)
        
        if context:
            print(f"Context (confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for mismatches
            if field == "Period" and "dividend" in context.lower():
                print("  ❌ MISMATCH: Period field matched dividend context")
            elif field == "Company" and "revenue" in context.lower() and "Life360" not in context:
                print("  ❌ MISMATCH: Company field matched unrelated revenue")
            else:
                print("  ✅ APPROPRIATE: Context matches field/value")
        else:
            print("  ✅ CORRECTLY EMPTY: No context generated (avoiding mismatch)")
        print()

def test_eps_context_completion():
    """Test complete EPS context extraction without trimming"""
    print("="*80)
    print("EPS CONTEXT COMPLETION TEST")
    print("="*80)
    
    # Document with EPS information
    document = """
    The company delivered strong financial results. Underlying earnings per share of 48.18 cents 
    per share (1HFY22: 40.30 cents) reflected the improved performance. Reported earnings per share 
    of 0.41 cents (1HFY22: 38.50 cents) included one-off charges. Basic earnings per share increased to 45.20 cents.
    """
    
    test_cases = [
        ("Underlying_EPS_1HFY23", "48.18 cents", "Should include 'Underlying earnings per share'"),
        ("Reported_EPS_1HFY23", "0.41 cents", "Should include 'Reported earnings per share'"),
        ("Basic_EPS", "45.20 cents", "Should include 'Basic earnings per share'")
    ]
    
    for field, value, expectation in test_cases:
        print(f"Testing: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, document)
        
        print(f"Context (confidence: {confidence:.3f}):")
        print(f"  {context}")
        
        # Check completeness
        if 'earnings per share' in context.lower():
            print("  ✅ Complete: Contains 'earnings per share'")
        else:
            print("  ❌ Incomplete: Missing 'earnings per share'")
            
        if '1HFY22:' in context or 'increased' in context:
            print("  ✅ Complete: Contains comparative values")
        else:
            print("  ⚠️  Missing comparative values")
        print()

def test_over_inclusion_prevention():
    """Test prevention of over-inclusive contexts"""
    print("="*80)
    print("OVER-INCLUSION PREVENTION TEST")
    print("="*80)
    
    # Document with multiple sections that could cause over-inclusion
    document = """
    Australian Broking division achieved strong results with EBIT Margin of 35.2% driven by operational efficiency.
    
    Tysers contributed 3 months of profit following acquisition. The integration is proceeding well.
    1HFY23 included 3 months of Tysers profit for the first time, contributing significantly to results.
    
    Annual revenue growth of 22% YoY was achieved. Management provided guidance for continued growth.
    The outlook remains positive with strong momentum expected to continue into the second half.
    """
    
    test_cases = [
        ("Tysers_Contribution_1HFY23", "3 months of profit", "Should get exact bullet, not EBIT margin"),
        ("Australian_Broking_Margin", "35.2%", "Should NOT include long guidance"),
        ("Annual_Revenue_Growth", "22% YoY", "Should NOT include long guidance")
    ]
    
    for field, value, expectation in test_cases:
        print(f"Testing: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, document)
        
        if context:
            word_count = len(context.split())
            print(f"Context ({word_count} words, confidence: {confidence:.3f}):")
            print(f"  {context}")
            
            # Check for over-inclusion
            if field == "Tysers_Contribution_1HFY23":
                if "3 months" in context and "Tysers" in context:
                    print("  ✅ Appropriate: Contains relevant Tysers information")
                elif "EBIT" in context or "35.2%" in context:
                    print("  ❌ Over-inclusive: Contains unrelated EBIT margin")
                else:
                    print("  ⚠️  May be incomplete")
            elif word_count <= 15:
                print("  ✅ Appropriately concise")
            else:
                print("  ⚠️  May be over-inclusive")
        else:
            print("  ✅ CORRECTLY EMPTY: Avoided potential over-inclusion")
        print()

def test_truncation_handling():
    """Test improved truncation and chopping prevention"""
    print("="*80)
    print("TRUNCATION HANDLING TEST")
    print("="*80)
    
    # Test cases for truncation
    test_cases = [
        ("FY23_Upgraded_Underlying_NPAT_Guidance: AUD 112.9mn to AUD 125.0mn", "Should preserve complete guidance"),
        ("Annualized_Revenue_Growth: 34% YoY growth was achieved", "Should preserve 'YoY' not 'Yo Y..'"),
        ("This is a very long context that exceeds normal limits and should be truncated properly at sentence boundaries to avoid word chopping and maintain readability while preserving the essential information.", "Should truncate at sentence boundary")
    ]
    
    for input_text, expectation in test_cases:
        print(f"Testing: {input_text[:50]}...")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        result = handle_truncation_and_chopping(input_text, 100)  # Short limit for testing
        
        print(f"Result: {result}")
        
        # Check for proper handling
        if "YoY" in input_text and "YoY" in result:
            print("  ✅ Preserved abbreviation correctly")
        elif "Yo Y" in result:
            print("  ❌ Chopped abbreviation incorrectly")
        
        if result.endswith('...') and not result.endswith(' ...'):
            print("  ✅ Proper truncation indicator")
        elif len(result) < len(input_text) and not result.endswith('.'):
            print("  ⚠️  May have chopped mid-sentence")
        else:
            print("  ✅ Proper sentence preservation")
        print()

def test_ceo_quote_handling():
    """Test CEO quote extraction and routing"""
    print("="*80)
    print("CEO QUOTE HANDLING TEST")
    print("="*80)
    
    # Document with CEO quotes
    document = """
    CEO Michael Emmett said: "All parts of AUB Group performed strongly during 1H23 with momentum continuing into the second half."
    Managing Director commented: "The outlook remains positive for continued growth."
    Chairman noted: "We are pleased with the strategic progress made this period."
    """
    
    test_cases = [
        ("CEO_Statement", "performed strongly", "Should capture full CEO quote"),
        ("CEO_Comment_Performance", "momentum continuing", "Should capture performance comment"),
        ("Management_Outlook", "outlook remains positive", "Should capture management statement")
    ]
    
    for field, value, expectation in test_cases:
        print(f"Testing: {field} = {value}")
        print(f"Expectation: {expectation}")
        print("-" * 50)
        
        context, confidence = generate_context_for_field(field, value, document)
        
        print(f"Context (confidence: {confidence:.3f}):")
        print(f"  {context}")
        
        # Check quote indicators
        quote_indicators = ['said:', 'commented:', 'noted:']
        has_indicator = any(indicator in context.lower() for indicator in quote_indicators)
        
        if has_indicator:
            print("  ✅ Contains quote indicator")
        else:
            print("  ❌ Missing quote indicator")
            
        if len(context) > 50:  # Reasonable quote length
            print("  ✅ Captures full quote context")
        else:
            print("  ⚠️  Context may be incomplete")
        print()

def main():
    """Run all precision improvement tests"""
    print("PRECISION IMPROVEMENTS TESTING")
    print("="*80)
    
    test_mismatch_prevention()
    test_eps_context_completion()
    test_over_inclusion_prevention()
    test_truncation_handling()
    test_ceo_quote_handling()
    
    print("="*80)
    print("PRECISION IMPROVEMENTS TESTING COMPLETED")
    print("="*80)

if __name__ == "__main__":
    main()