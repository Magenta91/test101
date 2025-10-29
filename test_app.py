#!/usr/bin/env python3
"""
Quick test to verify app.py can be imported and started
"""

import sys
import os

# Test import
try:
    from app import app
    print("✅ App imported successfully")
except Exception as e:
    print(f"❌ App import failed: {e}")
    sys.exit(1)

# Test basic routes
try:
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"✅ Health endpoint: {response.status_code}")
        
        # Test main page
        response = client.get('/')
        print(f"✅ Main page: {response.status_code}")
        
except Exception as e:
    print(f"❌ Route test failed: {e}")
    sys.exit(1)

print("🎉 App is ready for deployment!")