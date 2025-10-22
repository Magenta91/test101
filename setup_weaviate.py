#!/usr/bin/env python3
"""
Setup script for Weaviate + LLM Context Enhancement
"""

import subprocess
import sys
import time
import requests
import os

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("OK Docker is installed")
            return True
        else:
            print("X Docker is not installed")
            return False
    except FileNotFoundError:
        print("X Docker is not installed")
        return False

def start_weaviate():
    """Start Weaviate using docker-compose"""
    print("Starting Weaviate...")
    
    try:
        # Stop any existing containers
        subprocess.run(['docker-compose', 'down'], capture_output=True)
        
        # Start Weaviate
        result = subprocess.run(['docker-compose', 'up', '-d'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("OK Weaviate container started")
            return True
        else:
            print(f"X Failed to start Weaviate: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("X docker-compose not found. Please install Docker Compose")
        return False

def wait_for_weaviate(max_wait=60):
    """Wait for Weaviate to be ready"""
    print("Waiting for Weaviate to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("http://localhost:8080/v1/meta", timeout=5)
            if response.status_code == 200:
                print("OK Weaviate is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
        print("   Still waiting...")
    
    print("X Weaviate did not start within the timeout period")
    return False

def check_env_file():
    """Check if .env file exists with required variables"""
    if not os.path.exists('.env'):
        print("X .env file not found")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        if 'OPENAI_API_KEY' in content:
            print("OK .env file found with OpenAI API key")
            return True
        else:
            print("X OPENAI_API_KEY not found in .env file")
            return False

def run_test():
    """Run the integration test"""
    print("Running integration test...")
    
    try:
        result = subprocess.run([sys.executable, 'test_weaviate_integration.py'], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"X Error running test: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("WEAVIATE + LLM CONTEXT ENHANCEMENT SETUP")
    print("=" * 60)
    
    # Step 1: Check prerequisites
    print("\n1. Checking prerequisites...")
    if not check_docker():
        print("Please install Docker first: https://docs.docker.com/get-docker/")
        return False
    
    if not check_env_file():
        return False
    
    # Step 2: Start Weaviate
    print("\n2. Starting Weaviate...")
    if not start_weaviate():
        return False
    
    # Step 3: Wait for Weaviate to be ready
    print("\n3. Waiting for Weaviate...")
    if not wait_for_weaviate():
        return False
    
    # Step 4: Run test
    print("\n4. Running integration test...")
    if run_test():
        print("\nSetup completed successfully!")
        print("\nYour Weaviate + LLM Context Enhancement is ready to use!")
        print("\nUsage:")
        print("- Process documents using your existing pipeline")
        print("- The results will now include 'polished_context' fields")
        print("- Weaviate is running at http://localhost:8080")
        print("\nTo stop Weaviate: docker-compose down")
        return True
    else:
        print("\nSetup test failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)