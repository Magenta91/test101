#!/usr/bin/env python3
"""
Test script to diagnose library issues
"""

import sys
import os
import subprocess

def test_libraries():
    """Test various libraries and dependencies"""
    
    print("🔍 Library Diagnostic Test")
    print("=" * 50)
    
    # Test Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Test basic imports
    print("\n📦 Testing basic imports...")
    try:
        import PIL
        print(f"✅ PIL/Pillow: {PIL.__version__}")
    except ImportError as e:
        print(f"❌ PIL/Pillow: {e}")
    
    try:
        import fitz
        print(f"✅ PyMuPDF: {fitz.__version__}")
    except ImportError as e:
        print(f"❌ PyMuPDF: {e}")
    
    # Test pytesseract
    print("\n🔍 Testing pytesseract...")
    try:
        import pytesseract
        print("✅ pytesseract imported successfully")
        
        # Test tesseract command
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {version}")
        except Exception as e:
            print(f"❌ Tesseract version check failed: {e}")
            
    except ImportError as e:
        print(f"❌ pytesseract import failed: {e}")
    
    # Test system tesseract
    print("\n🔧 Testing system tesseract...")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ System tesseract: {result.stdout.split()[1]}")
        else:
            print(f"❌ System tesseract failed: {result.stderr}")
    except Exception as e:
        print(f"❌ System tesseract error: {e}")
    
    # Test library files
    print("\n📚 Testing library files...")
    lib_paths = [
        '/lib/x86_64-linux-gnu/libcrypt.so.1',
        '/lib/x86_64-linux-gnu/libcrypt.so.2',
        '/usr/lib/x86_64-linux-gnu/libcrypt.so.1',
        '/usr/lib/x86_64-linux-gnu/libcrypt.so.2'
    ]
    
    for lib_path in lib_paths:
        if os.path.exists(lib_path):
            print(f"✅ Found: {lib_path}")
        else:
            print(f"❌ Missing: {lib_path}")
    
    # Test simple OCR
    print("\n🧪 Testing simple OCR...")
    try:
        from PIL import Image, ImageDraw
        import pytesseract
        
        # Create simple test image
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST", fill='black')
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        print(f"✅ OCR test result: '{text.strip()}'")
        
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_libraries()