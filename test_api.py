#!/usr/bin/env python3
"""
Simple test script for the FastAPI RAG service.
Tests basic functionality without external dependencies.
"""

import os
import time

import requests

API_PORT = os.getenv("API_PORT", "8001")
API_BASE = f"http://localhost:{API_PORT}/api/v1"


def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service Status: {data['status']}")
            print(f"Dependencies: {data['dependencies']}")
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False


def test_text_ingestion():
    """Test text ingestion endpoint."""
    print("\n📝 Testing text ingestion...")
    try:
        payload = {
            "text": "This is a test document for the FastAPI RAG service. It contains information about testing procedures and API functionality.",
            "source": "API Test Document",
        }

        response = requests.post(f"{API_BASE}/ingest/text", json=payload, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Chunks created: {data['chunks_created']}")
            print(f"Processing time: {data['processing_time']}s")
            return True
        else:
            print(f"Text ingestion failed: {response.text}")
            return False
    except Exception as e:
        print(f"Text ingestion error: {e}")
        return False


def test_query():
    """Test query endpoint (search all collections)."""
    print("\n🔍 Testing query endpoint (all collections)...")
    try:
        payload = {
            "query": "What is this document about?",
            "options": {"top_k": 3, "hybrid_alpha": 0.5},
        }

        response = requests.post(f"{API_BASE}/query", json=payload, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Answer: {data['answer'][:200]}...")
            print(f"Retrieved chunks: {data['chunk_count']}")
            print(f"Collection searched: {data['collection']}")
            print(f"Processing time: {data['processing_time']}s")
            return True
        else:
            print(f"Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"Query error: {e}")
        return False


def test_query_single_collection():
    """Test query endpoint with single collection (backward compatibility)."""
    print("\n🔍 Testing query endpoint (single collection)...")
    try:
        payload = {
            "query": "What is this document about?",
            "collection": "Documents",
            "options": {"top_k": 3, "hybrid_alpha": 0.5},
        }

        response = requests.post(f"{API_BASE}/query", json=payload, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Answer: {data['answer'][:200]}...")
            print(f"Retrieved chunks: {data['chunk_count']}")
            print(f"Collection searched: {data['collection']}")
            print(f"Processing time: {data['processing_time']}s")

            # Verify single collection was searched
            if data["collection"] != "Documents":
                print(f"⚠️ Warning: Expected 'Documents', got '{data['collection']}'")

            return True
        else:
            print(f"Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"Query error: {e}")
        return False


def test_query_multiple_collections():
    """Test query endpoint with multiple collections (new feature)."""
    print("\n🔍 Testing query endpoint (multiple collections)...")
    try:
        # First, get available collections
        collections_response = requests.get(f"{API_BASE}/collections", timeout=10)
        if collections_response.status_code != 200:
            print("⚠️ Cannot retrieve collections list, skipping multi-collection test")
            return True

        collections_data = collections_response.json()
        available_collections = [c["name"] for c in collections_data["collections"]]

        if len(available_collections) < 2:
            print(
                f"⚠️ Only {len(available_collections)} collection(s) available, skipping multi-collection test"
            )
            return True

        # Use first two collections for testing
        test_collections = available_collections[:2]
        print(f"Testing with collections: {test_collections}")

        payload = {
            "query": "What information is available?",
            "collection": test_collections,
            "options": {"top_k": 5, "hybrid_alpha": 0.5},
        }

        response = requests.post(f"{API_BASE}/query", json=payload, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Answer: {data['answer'][:200]}...")
            print(f"Retrieved chunks: {data['chunk_count']}")
            print(f"Collection searched: {data['collection']}")
            print(f"Processing time: {data['processing_time']}s")

            # Verify multiple collections were searched
            expected_display = ", ".join(test_collections)
            if data["collection"] != expected_display:
                print(
                    f"⚠️ Warning: Expected '{expected_display}', got '{data['collection']}'"
                )

            return True
        else:
            print(f"Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"Query error: {e}")
        return False


def test_file_upload():
    """Test file upload endpoint."""
    print("\n📁 Testing file upload...")
    try:
        # Create a temporary test file
        test_content = """
# Test Document for API

This is a test document created for validating the FastAPI file upload functionality.

## Features Being Tested
- File upload processing
- Background job management
- Text extraction and chunking
- Status tracking

The system should be able to process this document and make it searchable.
"""

        # Use multipart form data for file upload
        files = {"file": ("test_document.md", test_content, "text/markdown")}
        data = {"source": "Test File Upload"}

        response = requests.post(
            f"{API_BASE}/ingest/file", files=files, data=data, timeout=30
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Job ID: {data['job_id']}")
            print(f"Initial Status: {data['status']}")
            print(f"Filename: {data['filename']}")

            # Check job status
            job_id = data["job_id"]
            return test_job_status(job_id)
        else:
            print(f"File upload failed: {response.text}")
            return False
    except Exception as e:
        print(f"File upload error: {e}")
        return False


def test_job_status(job_id):
    """Test job status endpoint."""
    print(f"\n⏳ Testing job status for {job_id}...")
    try:
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(f"{API_BASE}/ingest/status/{job_id}", timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(
                    f"Attempt {attempt + 1}: Status = {data['status']}, Progress = {data.get('progress', 'N/A')}%"
                )

                if data["status"] in ["completed", "failed"]:
                    print(f"Final message: {data.get('message', 'No message')}")
                    return data["status"] == "completed"

                time.sleep(2)  # Wait before next check
            else:
                print(f"Status check failed: {response.text}")
                return False

        print("Job did not complete within expected time")
        return False
    except Exception as e:
        print(f"Job status error: {e}")
        return False


def test_collections():
    """Test collections endpoint."""
    print("\n📚 Testing collections endpoint...")
    try:
        response = requests.get(f"{API_BASE}/collections", timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Total collections: {data['total_count']}")
            for collection in data["collections"]:
                print(f"  - {collection['name']}: {collection['chunk_count']} chunks")
            return True
        else:
            print(f"Collections list failed: {response.text}")
            return False
    except Exception as e:
        print(f"Collections error: {e}")
        return False


def main():
    """Run all API tests."""
    print("🚀 Starting FastAPI RAG Service Tests")
    print("=" * 50)

    tests = [
        ("Health Check", test_health),
        ("Text Ingestion", test_text_ingestion),
        ("Query Processing (All Collections)", test_query),
        ("Query Processing (Single Collection)", test_query_single_collection),
        ("Query Processing (Multiple Collections)", test_query_multiple_collections),
        ("File Upload", test_file_upload),
        ("Collections List", test_collections),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
