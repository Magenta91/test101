#!/usr/bin/env python3
"""
Minimal PDF processor that extracts text without OCR
Fallback for when Tesseract has library issues
"""

import fitz  # PyMuPDF
import time
from typing import Dict, Any

def extract_text_minimal(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract text from PDF using only PyMuPDF (no OCR)
    This works for PDFs with embedded text
    """
    start_time = time.time()
    
    try:
        print("🔧 Using minimal text extraction (PyMuPDF only - no OCR)")
        
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        all_text = []
        
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            
            if text.strip():
                # Split into lines and clean
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                all_text.extend(lines)
        
        pdf_document.close()
        
        processing_time = time.time() - start_time
        print(f"✅ Minimal text extraction completed in {processing_time:.1f}s")
        print(f"📄 Extracted {len(all_text)} lines of text")
        
        return {
            "document_text": all_text,
            "tables": [],
            "key_values": [],
            "footnotes": [],
            "footnote_markers": {},
            "enhanced_text": all_text,
            "full_text": " ".join(all_text),
            "extraction_method": "PyMuPDF Text Only (No OCR)",
            "processing_time": f"{processing_time:.1f}s"
        }
        
    except Exception as e:
        print(f"❌ Minimal extraction failed: {e}")
        error_text = f"Error: Minimal text extraction failed: {str(e)}"
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