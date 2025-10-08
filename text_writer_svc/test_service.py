#!/usr/bin/env python3

import unittest
import requests
import json
import uuid
import time
from typing import Dict, Any

class TestTextWriterService(unittest.TestCase):
    BASE_URL = "http://localhost:5001"
    
    def setUp(self):
        """Set up test fixtures"""
        # Wait for service to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        else:
            self.fail("Service not ready after 30 seconds")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('service', data)
        self.assertIn('version', data)
    
    def test_create_message(self):
        """Test creating a message"""
        test_message = f"Test message {uuid.uuid4()}"
        test_id = str(uuid.uuid4())
        
        payload = {
            "id": test_id,
            "message": test_message
        }
        
        response = requests.post(f"{self.BASE_URL}/messages", json=payload)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertEqual(data['id'], test_id)
        self.assertEqual(data['message'], test_message)
        self.assertEqual(data['status'], 'created')
    
    def test_get_message(self):
        """Test retrieving a specific message"""
        # First create a message
        test_message = f"Test get message {uuid.uuid4()}"
        test_id = str(uuid.uuid4())
        
        payload = {
            "id": test_id,
            "message": test_message
        }
        
        create_response = requests.post(f"{self.BASE_URL}/messages", json=payload)
        self.assertEqual(create_response.status_code, 201)
        
        # Then retrieve it
        get_response = requests.get(f"{self.BASE_URL}/messages/{test_id}")
        self.assertEqual(get_response.status_code, 200)
        
        data = get_response.json()
        self.assertEqual(data['id'], test_id)
        self.assertEqual(data['message'], test_message)
        self.assertIn('created_at', data)
        self.assertIn('processed_at', data)
    
    def test_get_nonexistent_message(self):
        """Test retrieving a non-existent message"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{self.BASE_URL}/messages/{fake_id}")
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data['error'], 'Message not found')
    
    def test_list_messages(self):
        """Test listing messages"""
        response = requests.get(f"{self.BASE_URL}/messages")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('messages', data)
        self.assertIn('total', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        self.assertIsInstance(data['messages'], list)
    
    def test_list_messages_with_pagination(self):
        """Test listing messages with pagination"""
        response = requests.get(f"{self.BASE_URL}/messages?limit=5&offset=0")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['limit'], 5)
        self.assertEqual(data['offset'], 0)
        self.assertTrue(len(data['messages']) <= 5)
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        response = requests.get(f"{self.BASE_URL}/stats")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_messages', data)
        self.assertIn('recent_messages_1h', data)
        self.assertIn('kafka_consumer_running', data)
        self.assertIsInstance(data['total_messages'], int)
        self.assertIsInstance(data['recent_messages_1h'], int)
        self.assertIsInstance(data['kafka_consumer_running'], bool)
    
    def test_create_message_without_id(self):
        """Test creating a message without providing an ID"""
        test_message = f"Test message without ID {uuid.uuid4()}"
        
        payload = {
            "message": test_message
        }
        
        response = requests.post(f"{self.BASE_URL}/messages", json=payload)
        self.assertEqual(response.status_code, 201)
        
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['message'], test_message)
        self.assertEqual(data['status'], 'created')
        
        # Verify the ID is a valid UUID
        try:
            uuid.UUID(data['id'])
        except ValueError:
            self.fail("Generated ID is not a valid UUID")
    
    def test_create_message_invalid_payload(self):
        """Test creating a message with invalid payload"""
        response = requests.post(f"{self.BASE_URL}/messages", json={})
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()