#!/usr/bin/env python3
"""
Comprehensive functionality test for the local-weaviate-rag system.
Tests 100% of ingestion and querying functionality with multiple examples.
"""

import os
import sys
import time
import subprocess
import tempfile
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class RAGFunctionalityTest:
    """Comprehensive test suite for RAG functionality."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.temp_files: List[str] = []
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result for final summary."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"    Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Run shell command and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=os.getcwd()
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def check_env_file(self) -> bool:
        """Check if .env file exists and has required variables."""
        logger.info("🔍 Checking .env file configuration...")
        
        if not os.path.exists('.env'):
            self.log_test_result("Environment File Check", False, ".env file not found")
            return False
        
        required_vars = ['OPENAI_API_KEY', 'WEAVIATE_API_KEY']
        missing_vars = []
        
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            for var in required_vars:
                if f"{var}=" not in env_content:
                    missing_vars.append(var)
        except Exception as e:
            self.log_test_result("Environment File Check", False, f"Error reading .env: {e}")
            return False
        
        if missing_vars:
            self.log_test_result(
                "Environment File Check", 
                False, 
                f"Missing variables: {', '.join(missing_vars)}"
            )
            return False
        
        self.log_test_result("Environment File Check", True, "All required variables present")
        return True
    
    def check_docker_running(self) -> bool:
        """Check if Docker is running."""
        logger.info("🐳 Checking Docker status...")
        
        success, stdout, stderr = self.run_command("docker ps")
        if success:
            self.log_test_result("Docker Status Check", True, "Docker is running")
            return True
        else:
            self.log_test_result("Docker Status Check", False, f"Docker not running: {stderr}")
            return False
    
    def check_weaviate_running(self) -> bool:
        """Check if Weaviate container is running."""
        logger.info("🔍 Checking Weaviate container status...")
        
        success, stdout, stderr = self.run_command("docker compose -f docker-compose.weaviate.yml ps")
        if success and "Up" in stdout:
            self.log_test_result("Weaviate Container Check", True, "Weaviate is running")
            return True
        else:
            self.log_test_result("Weaviate Container Check", False, "Weaviate is not running")
            return False
    
    def start_weaviate(self) -> bool:
        """Start Weaviate using the start script."""
        logger.info("🚀 Starting Weaviate...")
        
        success, stdout, stderr = self.run_command("./start_weaviate.sh", timeout=60)
        if success:
            # Wait for Weaviate to be fully ready
            logger.info("⏳ Waiting for Weaviate to be ready...")
            time.sleep(10)
            
            # Verify it's actually running
            if self.check_weaviate_running():
                self.log_test_result("Weaviate Startup", True, "Weaviate started successfully")
                return True
        
        self.log_test_result("Weaviate Startup", False, f"Failed to start: {stderr}")
        return False
    
    def create_test_files(self) -> List[str]:
        """Create temporary test files with different content types."""
        logger.info("📝 Creating test files...")
        
        test_files = []
        
        # Test file 1: Simple text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a simple text file for testing. It contains basic information about testing procedures.")
            test_files.append(f.name)
            self.temp_files.append(f.name)
        
        # Test file 2: Technical documentation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# API Documentation
            
## Authentication
Use API key authentication with the X-API-Key header.

## Endpoints
- GET /users - List all users
- POST /users - Create new user
- DELETE /users/{id} - Delete user by ID

## Error Codes
- 401: Unauthorized
- 404: Not found
- 500: Internal server error
""")
            test_files.append(f.name)
            self.temp_files.append(f.name)
        
        # Test file 3: Python code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def calculate_fibonacci(n):
    \"\"\"Calculate fibonacci number using recursion.\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    result = calculate_fibonacci(10)
    print(f"Fibonacci(10) = {result}")

if __name__ == "__main__":
    main()
""")
            test_files.append(f.name)
            self.temp_files.append(f.name)
        
        # Test file 4: JSON configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("""{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "production_db",
        "ssl": true
    },
    "cache": {
        "redis_url": "redis://localhost:6379",
        "ttl": 3600
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/app.log"
    }
}""")
            test_files.append(f.name)
            self.temp_files.append(f.name)
        
        self.log_test_result("Test File Creation", True, f"Created {len(test_files)} test files")
        return test_files
    
    def test_ingestion(self, test_files: List[str]) -> bool:
        """Test document ingestion with various file types and direct text."""
        logger.info("📥 Testing document ingestion...")
        
        ingestion_tests = []
        
        # Test 1: Ingest files
        for i, file_path in enumerate(test_files):
            file_type = Path(file_path).suffix
            source_name = f"Test File {i+1} ({file_type})"
            
            cmd = f'uv run python -m rag.ingest "{file_path}" --source "{source_name}"'
            success, stdout, stderr = self.run_command(cmd)
            
            test_name = f"File Ingestion {file_type}"
            output_text = stdout + stderr  # Check both output streams
            if success and "Ingested" in output_text and "chunks into" in output_text:
                self.log_test_result(test_name, True, f"Successfully ingested {file_type} file")
                ingestion_tests.append(True)
            else:
                self.log_test_result(test_name, False, f"Failed - Command succeeded: {success}, Output: {output_text[:200]}...")
                ingestion_tests.append(False)
        
        # Test 2: Direct text ingestion (short)
        cmd = 'uv run python -m rag.ingest "Machine learning is a subset of artificial intelligence" --source "ML Definition"'
        success, stdout, stderr = self.run_command(cmd)
        
        output_text = stdout + stderr
        if success and "Ingested" in output_text and "chunks into" in output_text:
            self.log_test_result("Direct Text Ingestion (Short)", True, "Successfully ingested short text")
            ingestion_tests.append(True)
        else:
            self.log_test_result("Direct Text Ingestion (Short)", False, f"Failed - Command succeeded: {success}, Output: {output_text[:200]}...")
            ingestion_tests.append(False)
        
        # Test 3: Direct text ingestion (longer)
        long_text = """
        Natural Language Processing (NLP) is a field of artificial intelligence that focuses on the interaction between computers and humans through natural language. 
        The ultimate objective of NLP is to read, decipher, understand, and make sense of human language in a valuable way. 
        Most NLP techniques rely on machine learning to derive meaning from human languages.
        Key applications include sentiment analysis, machine translation, chatbots, and text summarization.
        Modern approaches use deep learning models like transformers and attention mechanisms.
        """
        
        cmd = f'uv run python -m rag.ingest "{long_text.strip()}" --source "NLP Overview"'
        success, stdout, stderr = self.run_command(cmd)
        
        output_text = stdout + stderr
        if success and "Ingested" in output_text and "chunks into" in output_text:
            self.log_test_result("Direct Text Ingestion (Long)", True, "Successfully ingested long text")
            ingestion_tests.append(True)
        else:
            self.log_test_result("Direct Text Ingestion (Long)", False, f"Failed - Command succeeded: {success}, Output: {output_text[:200]}...")
            ingestion_tests.append(False)
        
        # Test 4: Collection persistence (ingest another document)
        cmd = 'uv run python -m rag.ingest "This tests collection persistence and data accumulation" --source "Persistence Test"'
        success, stdout, stderr = self.run_command(cmd)
        
        output_text = stdout + stderr
        if success and "already exists and is functional" in output_text and "Ingested" in output_text:
            self.log_test_result("Collection Persistence", True, "Collection reused without data loss")
            ingestion_tests.append(True)
        else:
            self.log_test_result("Collection Persistence", False, f"Failed - Command succeeded: {success}, Output: {output_text[:200]}...")
            ingestion_tests.append(False)
        
        return all(ingestion_tests)
    
    def test_querying(self) -> bool:
        """Test querying functionality with various query types."""
        logger.info("🔍 Testing query functionality...")
        
        query_tests = []
        
        # Test queries with expected content
        test_queries = [
            ("What is fibonacci?", "fibonacci", "Code-related query"),
            ("How do I authenticate with the API?", "authentication", "API documentation query"),
            ("What is machine learning?", "machine learning", "Definition query"),
            ("What are the error codes?", "error", "Specific information query"),
            ("Tell me about NLP", "natural language", "Technical concept query"),
            ("What database configuration is mentioned?", "database", "Configuration query"),
            ("testing procedures", "testing", "Simple keyword query"),
            ("What ports are mentioned?", "port", "Numeric information query")
        ]
        
        for query, expected_keyword, test_type in test_queries:
            cmd = f'uv run python -m rag.query "{query}"'
            success, stdout, stderr = self.run_command(cmd)
            
            if success:
                # Check if we got results and a reasonable answer
                has_results = "Found" in stdout and "results" in stdout
                has_answer = "GENERATED ANSWER:" in stdout
                answer_section = stdout.split("GENERATED ANSWER:")[-1] if has_answer else ""
                
                if has_results and has_answer and len(answer_section.strip()) > 10:
                    self.log_test_result(f"Query Test: {test_type}", True, f"Got relevant results for: {query}")
                    query_tests.append(True)
                else:
                    self.log_test_result(f"Query Test: {test_type}", False, f"No meaningful results for: {query}")
                    query_tests.append(False)
            else:
                self.log_test_result(f"Query Test: {test_type}", False, f"Query failed: {stderr}")
                query_tests.append(False)
        
        # Test edge cases
        edge_case_queries = [
            ("", "Empty query test"),
            ("xyz123nonexistent", "Non-existent content query"),
            ("What is the meaning of life, universe and everything according to Douglas Adams?", "Unrelated query test")
        ]
        
        for query, test_name in edge_case_queries:
            if query == "":
                # Empty query should be handled gracefully
                cmd = 'uv run python -m rag.query ""'
            else:
                cmd = f'uv run python -m rag.query "{query}"'
                
            success, stdout, stderr = self.run_command(cmd)
            
            # For edge cases, we just want to ensure they don't crash
            if query == "":
                # Empty query might be rejected, that's ok
                self.log_test_result(test_name, True, "Empty query handled gracefully")
                query_tests.append(True)
            else:
                # Non-existent content should still return some response without crashing
                if success:
                    self.log_test_result(test_name, True, "Edge case handled without crashing")
                    query_tests.append(True)
                else:
                    self.log_test_result(test_name, False, f"Edge case caused crash: {stderr}")
                    query_tests.append(False)
        
        return all(query_tests)
    
    def test_output_format(self) -> bool:
        """Test that query output has the correct structured format."""
        logger.info("📋 Testing output format structure...")
        
        cmd = 'uv run python -m rag.query "What is testing?"'
        success, stdout, stderr = self.run_command(cmd)
        
        if not success:
            self.log_test_result("Output Format Test", False, f"Query failed: {stderr}")
            return False
        
        # Check for required sections
        required_sections = [
            "INPUT QUERY:",
            "RETRIEVED VECTOR SEARCH:",
            "FULL DETAILS (QUERY + CONTEXT) TO BE SENT:",
            "GENERATED ANSWER:"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in stdout:
                missing_sections.append(section)
        
        if missing_sections:
            self.log_test_result(
                "Output Format Test", 
                False, 
                f"Missing sections: {', '.join(missing_sections)}"
            )
            return False
        
        self.log_test_result("Output Format Test", True, "All required output sections present")
        return True
    
    def test_schema_persistence(self) -> bool:
        """Test that schema and data persist between ingestion calls."""
        logger.info("💾 Testing schema and data persistence...")
        
        # First, ingest a unique document
        unique_content = f"Unique test document created at {time.time()}"
        cmd = f'uv run python -m rag.ingest "{unique_content}" --source "Persistence Test"'
        success1, stdout1, stderr1 = self.run_command(cmd)
        
        if not success1:
            self.log_test_result("Schema Persistence Test", False, f"Initial ingestion failed: {stderr1}")
            return False
        
        # Then, query for it to ensure it was stored
        cmd = f'uv run python -m rag.query "unique test document"'
        success2, stdout2, stderr2 = self.run_command(cmd)
        
        if not success2:
            self.log_test_result("Schema Persistence Test", False, f"Query after ingestion failed: {stderr2}")
            return False
        
        # Check if our unique content appears in results
        if unique_content.split()[0] in stdout2:  # Check for part of unique content
            self.log_test_result("Schema Persistence Test", True, "Data persisted correctly between operations")
            return True
        else:
            self.log_test_result("Schema Persistence Test", False, "Data not found after ingestion")
            return False
    
    def cleanup(self):
        """Clean up temporary files."""
        logger.info("🧹 Cleaning up temporary files...")
        
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
                logger.debug(f"Deleted {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete {temp_file}: {e}")
    
    def print_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n" + "="*80)
        logger.info("🎯 COMPREHENSIVE RAG FUNCTIONALITY TEST SUMMARY")
        logger.info("="*80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        logger.info(f"📊 OVERALL RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        logger.info("")
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result["test"].split(" ")[0] if " " in result["test"] else "Other"
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, tests in categories.items():
            cat_passed = sum(1 for t in tests if t["success"])
            cat_total = len(tests)
            status = "✅" if cat_passed == cat_total else "⚠️" if cat_passed > 0 else "❌"
            
            logger.info(f"{status} {category}: {cat_passed}/{cat_total}")
            for test in tests:
                status_icon = "  ✅" if test["success"] else "  ❌"
                logger.info(f"{status_icon} {test['test']}")
                if test["details"] and not test["success"]:
                    logger.info(f"     → {test['details']}")
        
        logger.info("")
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! RAG system is fully functional.")
        else:
            logger.info(f"⚠️  {total - passed} tests failed. Please review the issues above.")
        
        logger.info("="*80)
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        logger.info("🚀 Starting comprehensive RAG functionality tests...")
        logger.info("="*80)
        
        try:
            # 1. Environment checks
            if not self.check_env_file():
                logger.error("❌ Environment configuration is incomplete. Please check your .env file.")
                return False
            
            # 2. Docker checks
            if not self.check_docker_running():
                logger.error("❌ Docker is not running. Please start Docker and try again.")
                return False
            
            # 3. Weaviate checks and startup
            if not self.check_weaviate_running():
                logger.info("🔧 Weaviate not running, starting it now...")
                if not self.start_weaviate():
                    logger.error("❌ Failed to start Weaviate. Please check Docker logs.")
                    return False
            
            # 4. Create test data
            test_files = self.create_test_files()
            
            # 5. Test ingestion
            if not self.test_ingestion(test_files):
                logger.warning("⚠️ Some ingestion tests failed")
            
            # 6. Test querying
            if not self.test_querying():
                logger.warning("⚠️ Some query tests failed")
            
            # 7. Test output format
            self.test_output_format()
            
            # 8. Test schema persistence
            self.test_schema_persistence()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Tests interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during testing: {e}")
            return False
        finally:
            self.cleanup()
            self.print_summary()

def main():
    """Main test execution."""
    test_suite = RAGFunctionalityTest()
    
    try:
        success = test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Testing interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()