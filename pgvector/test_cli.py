#!/usr/bin/env python3
"""
Test script for the PostgreSQL pgvector CLI tool.
This script demonstrates all the CLI functionality.
"""

import json
import subprocess
import time
import sys
import uuid


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"COMMAND: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out!")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def create_test_embedding_file(filename, dimension=384):
    """Create a test embedding JSON file."""
    import numpy as np
    
    # Generate a random embedding
    embedding = np.random.rand(dimension).tolist()
    
    data = {
        "embedding": embedding,
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "metadata": {
            "dimension": dimension,
            "timestamp": time.time()
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Created test embedding file: {filename}")


def main():
    """Run all CLI tests."""
    print("PostgreSQL pgvector CLI Test Suite")
    print("Make sure PostgreSQL is running: docker compose up -d")
    print()
    
    # Test table name
    test_table = "test_embeddings"
    
    # Create test embedding files
    test_embedding_file = "test_embedding.json"
    query_embedding_file = "query_embedding.json"
    
    create_test_embedding_file(test_embedding_file)
    create_test_embedding_file(query_embedding_file)
    
    # List of test commands
    tests = [
        # List tables (should show default embeddings table)
        (["python", "pgvector_cli.py", "list-tables"], "List existing tables"),
        
        # Get info about default embeddings table
        (["python", "pgvector_cli.py", "table-info", "embeddings"], "Get embeddings table info"),
        
        # Create a test table
        (["python", "pgvector_cli.py", "create-table", test_table, "--vector-dimension", "384", "--description", "Test embeddings table"], "Create test table"),
        
        # List tables again (should show new table)
        (["python", "pgvector_cli.py", "list-tables"], "List tables after creation"),
        
        # Insert test embedding
        (["python", "pgvector_cli.py", "insert-embedding", test_table, "test-msg-1", "This is a test message for embedding", test_embedding_file], "Insert test embedding"),
        
        # Insert another test embedding
        (["python", "pgvector_cli.py", "insert-embedding", test_table, "test-msg-2", "Another test message with different content", test_embedding_file], "Insert second test embedding"),
        
        # Read table contents
        (["python", "pgvector_cli.py", "read-table", test_table, "--limit", "5"], "Read table contents"),
        
        # Get table info
        (["python", "pgvector_cli.py", "table-info", test_table], "Get test table info"),
        

        
        # Test help command
        (["python", "pgvector_cli.py", "--help"], "Show main help"),
        (["python", "pgvector_cli.py", "create-table", "--help"], "Show create-table help"),
        
        # Delete the test table
        (["python", "pgvector_cli.py", "delete-table", test_table], "Delete test table"),
        
        # List tables again (should not show deleted table)
        (["python", "pgvector_cli.py", "list-tables"], "List tables after deletion"),
    ]
    
    # Run all tests
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        time.sleep(1)  # Small delay between commands
    
    # Cleanup test files
    try:
        import os
        os.remove(test_embedding_file)
        os.remove(query_embedding_file)
        print(f"\nCleaned up test files: {test_embedding_file}, {query_embedding_file}")
    except:
        pass
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
