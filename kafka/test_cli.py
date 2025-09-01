#!/usr/bin/env python3
"""
Test script for the Kafka CLI tool.
This script demonstrates all the CLI functionality.
"""

import subprocess
import time
import sys
import json


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


def main():
    """Run all CLI tests."""
    print("Kafka CLI Test Suite")
    print("Make sure Kafka is running: docker compose up -d")
    
    # Test topic name
    test_topic = "test-topic-cli"
    
    # List of test commands
    tests = [
        # List topics (should show existing topics)
        (["python", "kafka_cli.py", "list-topics"], "List existing topics"),
        
        # Create a test topic
        (["python", "kafka_cli.py", "create-topic", test_topic, "--partitions", "2"], "Create test topic"),
        
        # List topics again (should show new topic)
        (["python", "kafka_cli.py", "list-topics"], "List topics after creation"),
        
        # Write some test messages
        (["python", "kafka_cli.py", "write", test_topic, "Hello, Kafka!"], "Write simple message"),
        (["python", "kafka_cli.py", "write", test_topic, json.dumps({"user": "test", "action": "login"}), "--key", "user-1"], "Write JSON message with key"),
        (["python", "kafka_cli.py", "write", test_topic, "Another test message", "--key", "msg-2"], "Write message with key"),
        
        # Read messages
        (["python", "kafka_cli.py", "read", test_topic, "--max-messages", "5"], "Read messages from topic"),
        
        # Try to create the same topic again (should fail gracefully)
        (["python", "kafka_cli.py", "create-topic", test_topic], "Try to create existing topic"),
        
        # Test help command
        (["python", "kafka_cli.py", "--help"], "Show main help"),
        (["python", "kafka_cli.py", "create-topic", "--help"], "Show create-topic help"),
        
        # Delete the test topic
        (["python", "kafka_cli.py", "delete-topic", test_topic], "Delete test topic"),
        
        # List topics again (should not show deleted topic)
        (["python", "kafka_cli.py", "list-topics"], "List topics after deletion"),
    ]
    
    # Run all tests
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        time.sleep(1)  # Small delay between commands
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
