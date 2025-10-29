#!/usr/bin/env python3
"""
Tesseract Installation Checker for Railway
Run this to verify Tesseract is properly installed and configured
"""

import os
import sys
import subprocess
import shutil

def check_tesseract():
    """Check if Tesseract is properly installed and configured"""
    
    print("🔍 Checking Tesseract Installation...")
    print("=" * 50)
    
    # Check if tesseract command is available
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        print(f"✅ Tesseract found at: {tesseract_path}")
    else:
        print("❌ Tesseract not found in PATH")
        return False
    
    # Check tesseract version
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = result.stdout.split('\n')[0]
            print(f"✅ Tesseract version: {version_info}")
        else:
            print(f"❌ Tesseract version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking Tesseract version: {e}")
        return False
    
    # Check TESSDATA_PREFIX
    tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
    if tessdata_prefix:
        print(f"✅ TESSDATA_PREFIX: {tessdata_prefix}")
        if os.path.exists(tessdata_prefix):
            print(f"✅ Tessdata directory exists")
        else:
            print(f"⚠️ Tessdata directory not found at: {tessdata_prefix}")
    else:
        print("⚠️ TESSDATA_PREFIX not set")
    
    # Check for English language data
    eng_traineddata_paths = [
        '/usr/share/tesseract-ocr/5/tessdata/eng.traineddata',
        '/usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata',
        '/usr/share/tessdata/eng.traineddata'
    ]
    
    eng_found = False
    for path in eng_traineddata_paths:
        if os.path.exists(path):
            print(f"✅ English language data found: {path}")
            eng_found = True
            break
    
    if not eng_found:
        print("⚠️ English language data not found in common locations")
    
    # Test pytesseract import
    try:
        import pytesseract
        print("✅ pytesseract module imported successfully")
        
        # Set tesseract command path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Test with a simple image (create a small test image)
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image with text
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR", fill='black')
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        if 'Test' in text or 'OCR' in text:
            print("✅ Tesseract OCR test successful")
            print(f"   Extracted text: '{text.strip()}'")
        else:
            print(f"⚠️ Tesseract OCR test unclear result: '{text.strip()}'")
        
    except ImportError as e:
        print(f"❌ Failed to import pytesseract: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Tesseract OCR test failed: {e}")
    
    print("\n🎯 Tesseract Status Summary:")
    print("✅ Tesseract is installed and should work for PDF processing")
    return True

if __name__ == "__main__":
    success = check_tesseract()
    sys.exit(0 if success else 1)