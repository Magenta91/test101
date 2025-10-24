#!/usr/bin/env python3
"""
Analyze the difference between the two Excel files
"""

import pandas as pd

def analyze_excel_files():
    # Read both files
    df_latest = pd.read_excel('extracted_data_comments (57).xlsx')
    df_original = pd.read_excel('extracted_data_comments (39).xlsx')
    
    print("=== COMPARISON ANALYSIS ===")
    print(f"LATEST FILE: {len(df_latest)} rows")
    print(f"ORIGINAL FILE: {len(df_original)} rows")
    print(f"DIFFERENCE: {len(df_original) - len(df_latest)} fewer rows in latest")
    
    print("\n=== LATEST FILE - First 15 fields ===")
    for i, row in df_latest.head(15).iterrows():
        field = str(row['field'])[:35]
        value = str(row['value'])[:15]
        context = str(row['context'])[:50]
        print(f"{i+1:2d}. {field:35} | {value:15} | {context}...")
    
    print("\n=== ORIGINAL FILE - First 15 fields ===")
    for i, row in df_original.head(15).iterrows():
        field = str(row['field'])[:35]
        value = str(row['value'])[:15]
        context = str(row['context'])[:50]
        print(f"{i+1:2d}. {field:35} | {value:15} | {context}...")
    
    print("\n=== FIELD TYPE ANALYSIS ===")
    
    # Analyze field patterns
    latest_fields = set(df_latest['field'].tolist())
    original_fields = set(df_original['field'].tolist())
    
    print(f"Unique fields in LATEST: {len(latest_fields)}")
    print(f"Unique fields in ORIGINAL: {len(original_fields)}")
    
    # Fields only in original (missing from latest)
    missing_fields = original_fields - latest_fields
    print(f"\nFields MISSING from latest ({len(missing_fields)}):")
    for field in sorted(list(missing_fields))[:20]:  # Show first 20
        print(f"  - {field}")
    
    # Fields only in latest (new in latest)
    new_fields = latest_fields - original_fields
    print(f"\nFields NEW in latest ({len(new_fields)}):")
    for field in sorted(list(new_fields))[:20]:  # Show first 20
        print(f"  + {field}")
    
    print("\n=== CONTEXT QUALITY ANALYSIS ===")
    
    # Analyze context quality
    latest_with_context = df_latest[df_latest['context'].notna() & (df_latest['context'] != '')]
    original_with_context = df_original[df_original['context'].notna() & (df_original['context'] != '')]
    
    print(f"LATEST: {len(latest_with_context)}/{len(df_latest)} fields have context ({len(latest_with_context)/len(df_latest)*100:.1f}%)")
    print(f"ORIGINAL: {len(original_with_context)}/{len(df_original)} fields have context ({len(original_with_context)/len(df_original)*100:.1f}%)")
    
    # Sample context quality
    print("\nLATEST - Context samples:")
    for i, row in latest_with_context.head(5).iterrows():
        print(f"  {row['field']}: {str(row['context'])[:80]}...")
    
    print("\nORIGINAL - Context samples:")
    for i, row in original_with_context.head(5).iterrows():
        print(f"  {row['field']}: {str(row['context'])[:80]}...")

if __name__ == "__main__":
    analyze_excel_files()