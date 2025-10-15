#!/usr/bin/env python3
"""
Enhanced server startup script with better error handling and diagnostics.
"""

import sys
import os
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")
    
    required_modules = [
        'flask',
        'fuzzywuzzy',
        'openai',
        'boto3',
        'pandas',
        'openpyxl'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nMissing modules: {', '.join(missing_modules)}")
        print("Install with: pip install " + ' '.join(missing_modules))
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    required_env_vars = [
        'OPENAI_API_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        if os.environ.get(var):
            print(f"✅ {var}")
        else:
            print(f"❌ {var} - MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\nMissing environment variables: {', '.join(missing_vars)}")
        print("Set them in your .env file or environment")
        return False
    
    return True

def start_server():
    """Start the Flask server with enhanced error handling"""
    try:
        print("\nStarting Flask server...")
        from app import app
        
        # Start server with enhanced configuration
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent double startup
        )
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("Enhanced Document Processing Server")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n⚠️  Environment check failed - server may not work properly")
        print("Continuing anyway...")
    
    # Start server
    print("\n🚀 Starting server...")
    start_server()