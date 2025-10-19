#!/usr/bin/env python3
"""
Test script for CQRS Embedding Generation Service

This script tests the embedding generation service functionality.
"""

import sys
import time
import requests
import json
import psycopg2
import psycopg2.extras
from typing import Dict, Any

def test_database_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='realtime_llm',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✓ Database connection successful: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_service_health():
    """Test service health endpoint"""
    try:
        response = requests.get('http://localhost:5003/health')
        response.raise_for_status()
        result = response.json()
        print(f"✓ Service health check: {result}")
        return True
    except Exception as e:
        print(f"✗ Service health check failed: {e}")
        return False

def test_service_status():
    """Test service status endpoint"""
    try:
        response = requests.get('http://localhost:5003/status')
        response.raise_for_status()
        result = response.json()
        print(f"✓ Service status: {result}")
        return True
    except Exception as e:
        print(f"✗ Service status check failed: {e}")
        return False

def test_processor_start():
    """Test starting the processor"""
    try:
        response = requests.post('http://localhost:5003/start')
        response.raise_for_status()
        result = response.json()
        print(f"✓ Processor start: {result}")
        return True
    except Exception as e:
        print(f"✗ Processor start failed: {e}")
        return False

def test_manual_batch_processing():
    """Test manual batch processing"""
    try:
        response = requests.post('http://localhost:5003/process-batch')
        response.raise_for_status()
        result = response.json()
        print(f"✓ Manual batch processing: {result}")
        return True
    except Exception as e:
        print(f"✗ Manual batch processing failed: {e}")
        return False

def test_embedding_search():
    """Test embedding search functionality"""
    try:
        # First, make sure we have some embeddings
        time.sleep(2)  # Wait for processing
        
        search_data = {
            'query': 'artificial intelligence machine learning',
            'limit': 5
        }
        response = requests.post('http://localhost:5003/embeddings/search', json=search_data)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Embedding search: Found {len(result.get('results', []))} results")
        return True
    except Exception as e:
        print(f"✗ Embedding search failed: {e}")
        return False

def check_embeddings_in_database():
    """Check if embeddings were created in the database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='realtime_llm',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM text_embeddings;')
        count = cursor.fetchone()[0]
        print(f"✓ Embeddings in database: {count} records")
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        print(f"✗ Failed to check embeddings in database: {e}")
        return False

def insert_test_message():
    """Insert a test message to verify real-time processing"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='realtime_llm',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        
        test_content = f"This is a test message for real-time processing - {int(time.time())}"
        cursor.execute(
            "INSERT INTO text_messages (content, source) VALUES (%s, %s) RETURNING id;",
            (test_content, 'test')
        )
        message_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✓ Inserted test message with ID: {message_id}")
        
        cursor.close()
        conn.close()
        return message_id
    except Exception as e:
        print(f"✗ Failed to insert test message: {e}")
        return None

def verify_test_message_processed(message_id: int, max_wait: int = 30):
    """Verify that the test message was processed"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='realtime_llm',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        
        for i in range(max_wait):
            cursor.execute(
                "SELECT id FROM text_embeddings WHERE text_message_id = %s;",
                (message_id,)
            )
            result = cursor.fetchone()
            
            if result:
                print(f"✓ Test message {message_id} processed successfully")
                cursor.close()
                conn.close()
                return True
            
            time.sleep(1)
        
        print(f"✗ Test message {message_id} not processed within {max_wait} seconds")
        cursor.close()
        conn.close()
        return False
        
    except Exception as e:
        print(f"✗ Failed to verify test message processing: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Running CQRS Embedding Generation Service Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Service Health", test_service_health),
        ("Service Status", test_service_status),
        ("Processor Start", test_processor_start),
        ("Manual Batch Processing", test_manual_batch_processing),
        ("Embeddings in Database", check_embeddings_in_database),
        ("Embedding Search", test_embedding_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Test real-time processing
    print(f"\n🔍 Running: Real-time Processing Test")
    message_id = insert_test_message()
    if message_id:
        realtime_result = verify_test_message_processed(message_id)
        results.append(("Real-time Processing", realtime_result))
    else:
        results.append(("Real-time Processing", False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)