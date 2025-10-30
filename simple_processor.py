#!/usr/bin/env python3
"""
Simple PDF processor that bypasses AWS entirely
Use this if AWS keeps causing issues
"""

import os
from typing import Dict, Any

def extract_structured_data_from_pdf_bytes_simple(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Simple PDF extraction using only Tesseract OCR
    Completely bypasses AWS Textract
    """
    print("🔧 Using simple Tesseract-only processing")
    
    try:
        from tesseract_processor import TesseractProcessor
        tesseract = TesseractProcessor()
        result = tesseract.extract_text_from_pdf_bytes(pdf_bytes)
        result["extraction_method"] = "Tesseract OCR (Simple Mode)"
        
        # Ensure full_text is available
        if "document_text" in result and result["document_text"]:
            result["full_text"] = " ".join(result["document_text"])
        else:
            result["full_text"] = ""
        
        return result
    except Exception as e:
        print(f"❌ Simple processing failed: {e}")
        
        # If Tesseract fails due to library issues, try minimal extraction
        if "libcrypt" in str(e) or "shared object" in str(e):
            print("🔄 Tesseract has library issues, trying minimal text extraction...")
            try:
                from minimal_processor import extract_text_minimal
                return extract_text_minimal(pdf_bytes)
            except Exception as minimal_error:
                print(f"❌ Minimal extraction also failed: {minimal_error}")
        
        error_text = f"Error: Simple Tesseract processing failed: {str(e)}"
        return {
            "document_text": [error_text],
            "tables": [],
            "key_values": [],
            "footnotes": [],
            "footnote_markers": {},
            "enhanced_text": [],
            "full_text": error_text,
            "extraction_method": "Failed",
            "error": str(e)
        }