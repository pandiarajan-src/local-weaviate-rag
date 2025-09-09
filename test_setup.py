#!/usr/bin/env python3
"""
Test script to validate the RAG system setup
"""

import os
import sys
import requests
from config import Config

def test_docker_availability():
    """Test if Docker is available"""
    try:
        os.system("docker --version > /dev/null 2>&1")
        print("✓ Docker is available")
        return True
    except:
        print("✗ Docker is not available")
        return False

def test_weaviate_connection():
    """Test if Weaviate is running and accessible"""
    try:
        response = requests.get(f"{Config.WEAVIATE_URL}/v1/meta", timeout=5)
        if response.status_code == 200:
            print("✓ Weaviate is running and accessible")
            print(f"  Version: {response.json().get('version', 'unknown')}")
            return True
        else:
            print(f"✗ Weaviate returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Weaviate. Make sure it's running with ./start_weaviate.sh")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Weaviate: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    try:
        # Test if .env file exists
        if os.path.exists(".env"):
            print("✓ .env file found")
        else:
            print("⚠ .env file not found. Copy .env.example to .env and configure it")
        
        # Test API key (without validating)
        if Config.OPENAI_API_KEY:
            if Config.OPENAI_API_KEY == "your_openai_api_key_here":
                print("⚠ OpenAI API key is set to placeholder value")
            else:
                print("✓ OpenAI API key is configured")
        else:
            print("✗ OpenAI API key is not set")
        
        print(f"✓ Weaviate URL: {Config.WEAVIATE_URL}")
        print(f"✓ Embedding model: {Config.EMBEDDING_MODEL}")
        print(f"✓ Chat model: {Config.CHAT_MODEL}")
        print(f"✓ Chunk size: {Config.CHUNK_SIZE}")
        print(f"✓ Chunk overlap: {Config.CHUNK_OVERLAP}")
        
        return True
    except Exception as e:
        print(f"✗ Error checking environment config: {e}")
        return False

def test_dependencies():
    """Test if required Python packages are installed"""
    required_packages = [
        "weaviate",
        "openai", 
        "tiktoken",
        "numpy",
        "requests",
        "dotenv"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstall missing packages with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Local Weaviate RAG System Setup")
    print("=" * 50)
    
    tests = [
        ("Docker Availability", test_docker_availability),
        ("Python Dependencies", test_dependencies),
        ("Environment Configuration", test_environment_config),
        ("Weaviate Connection", test_weaviate_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✓ PASS" if results[i] else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Start Weaviate: ./start_weaviate.sh")
        print("2. Ingest documents: python ingest_documents.py --file your_file.txt")
        print("3. Query system: python query_rag.py --interactive")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above before using the system.")
        sys.exit(1)

if __name__ == "__main__":
    main()