#!/usr/bin/env python3
"""
Test script to validate the RAG system configuration and scripts.
This script tests the basic functionality without requiring API keys.
"""

import os
import sys
import subprocess
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    try:
        import tiktoken
        import openai
        import weaviate
        from dotenv import load_dotenv
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_environment_template():
    """Test that .env.example exists and has required keys."""
    print("Testing environment template...")
    env_example = Path(".env.example")
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    content = env_example.read_text()
    required_keys = [
        "OPENAI_API_KEY",
        "WEAVIATE_URL",
        "EMBEDDING_MODEL",
        "GPT_MODEL",
        "COLLECTION_NAME"
    ]
    
    for key in required_keys:
        if key not in content:
            print(f"❌ Required key {key} not found in .env.example")
            return False
    
    print("✅ Environment template valid")
    return True

def test_script_syntax():
    """Test that Python scripts have valid syntax."""
    print("Testing script syntax...")
    scripts = ["embed_text.py", "query_rag.py"]
    
    for script in scripts:
        if not Path(script).exists():
            print(f"❌ Script {script} not found")
            return False
        
        # Test syntax by compiling
        result = subprocess.run([sys.executable, "-m", "py_compile", script], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Syntax error in {script}: {result.stderr}")
            return False
    
    print("✅ All scripts have valid syntax")
    return True

def test_shell_scripts():
    """Test that shell scripts exist and are executable."""
    print("Testing shell scripts...")
    scripts = ["start_weaviate.sh", "stop_weaviate.sh"]
    
    for script in scripts:
        path = Path(script)
        if not path.exists():
            print(f"❌ Shell script {script} not found")
            return False
        
        if not os.access(script, os.X_OK):
            print(f"❌ Shell script {script} is not executable")
            return False
        
        # Test syntax
        result = subprocess.run(["bash", "-n", script], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Syntax error in {script}: {result.stderr}")
            return False
    
    print("✅ All shell scripts are valid and executable")
    return True

def test_help_commands():
    """Test that help commands work for Python scripts."""
    print("Testing help commands...")
    scripts = [
        ("embed_text.py", "--help"),
        ("query_rag.py", "--help")
    ]
    
    for script, flag in scripts:
        result = subprocess.run([sys.executable, script, flag], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Help command failed for {script}: {result.stderr}")
            return False
        
        if "usage:" not in result.stdout:
            print(f"❌ Help output invalid for {script}")
            return False
    
    print("✅ All help commands work correctly")
    return True

def test_readme():
    """Test that README.md exists and has required sections."""
    print("Testing README...")
    readme = Path("README.md")
    if not readme.exists():
        print("❌ README.md not found")
        return False
    
    content = readme.read_text()
    required_sections = [
        "Features",
        "Prerequisites", 
        "Quick Setup",
        "Usage",
        "Troubleshooting"
    ]
    
    for section in required_sections:
        if section not in content:
            print(f"❌ Required section '{section}' not found in README")
            return False
    
    print("✅ README is complete")
    return True

def main():
    """Run all tests."""
    print("🔍 Running RAG System Validation Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_environment_template,
        test_script_syntax,
        test_shell_scripts,
        test_help_commands,
        test_readme
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! The RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your OpenAI API key")
        print("2. Start Weaviate with: ./start_weaviate.sh")
        print("3. Embed some text with: python embed_text.py 'Your text here'")
        print("4. Query with: python query_rag.py 'Your question'")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())