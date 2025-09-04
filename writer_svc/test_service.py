#!/usr/bin/env python3
"""
Test script for the Writer Service
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_service():
    """Test the writer service endpoints"""
    base_url = "http://localhost:5000"
    
    try:
        # Test health endpoint
        logger.info("Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
        
        # Test config endpoint
        logger.info("Testing config endpoint...")
        response = requests.get(f"{base_url}/config")
        print(f"Config: {response.status_code} - {response.json()}")
        
        # Test stats endpoint
        logger.info("Testing stats endpoint...")
        response = requests.get(f"{base_url}/stats")
        print(f"Stats: {response.status_code} - {response.json()}")
        
        # Test start endpoint
        logger.info("Testing start endpoint...")
        response = requests.post(f"{base_url}/start")
        print(f"Start: {response.status_code} - {response.json()}")
        
        # Wait a bit and check stats again
        time.sleep(2)
        response = requests.get(f"{base_url}/stats")
        print(f"Stats after start: {response.status_code} - {response.json()}")
        
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to writer service. Is it running?")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_service()
