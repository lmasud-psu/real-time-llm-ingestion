#!/usr/bin/env python3
"""
CLI tool for CQRS Embedding Generation Service

This tool provides command-line interface for interacting with the embedding processor service.
"""

import argparse
import requests
import json
import sys
import time
from typing import Dict, Any

class EmbeddingServiceClient:
    """Client for interacting with the embedding service"""
    
    def __init__(self, base_url: str = "http://localhost:5003"):
        self.base_url = base_url.rstrip('/')
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to the service"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = requests.get(url)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            sys.exit(1)
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return self._make_request('GET', '/health')
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return self._make_request('GET', '/status')
    
    def start_processor(self) -> Dict[str, Any]:
        """Start the embedding processor"""
        return self._make_request('POST', '/start')
    
    def stop_processor(self) -> Dict[str, Any]:
        """Stop the embedding processor"""
        return self._make_request('POST', '/stop')
    
    def process_batch(self) -> Dict[str, Any]:
        """Manually trigger batch processing"""
        return self._make_request('POST', '/process-batch')
    
    def search_embeddings(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for similar embeddings"""
        data = {'query': query, 'limit': limit}
        return self._make_request('POST', '/embeddings/search', data)

def cmd_health(args, client: EmbeddingServiceClient):
    """Health check command"""
    result = client.health_check()
    print(json.dumps(result, indent=2))

def cmd_status(args, client: EmbeddingServiceClient):
    """Status command"""
    result = client.get_status()
    print(json.dumps(result, indent=2))

def cmd_start(args, client: EmbeddingServiceClient):
    """Start processor command"""
    result = client.start_processor()
    print(json.dumps(result, indent=2))

def cmd_stop(args, client: EmbeddingServiceClient):
    """Stop processor command"""
    result = client.stop_processor()
    print(json.dumps(result, indent=2))

def cmd_process(args, client: EmbeddingServiceClient):
    """Manual batch processing command"""
    result = client.process_batch()
    print(json.dumps(result, indent=2))

def cmd_search(args, client: EmbeddingServiceClient):
    """Search embeddings command"""
    result = client.search_embeddings(args.query, args.limit)
    print(json.dumps(result, indent=2))

def cmd_monitor(args, client: EmbeddingServiceClient):
    """Monitor processor status"""
    print("Monitoring embedding processor (Press Ctrl+C to stop)...")
    try:
        while True:
            status = client.get_status()
            print(f"[{status.get('timestamp', 'unknown')}] "
                  f"Running: {status.get('running', False)}, "
                  f"Last ID: {status.get('last_processed_id', 0)}, "
                  f"Model: {'Loaded' if status.get('model_loaded', False) else 'Not loaded'}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='CQRS Embedding Generation Service CLI')
    parser.add_argument('--url', default='http://localhost:5003', 
                       help='Base URL of the embedding service')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health check command
    parser_health = subparsers.add_parser('health', help='Check service health')
    
    # Status command
    parser_status = subparsers.add_parser('status', help='Get processor status')
    
    # Start command
    parser_start = subparsers.add_parser('start', help='Start the embedding processor')
    
    # Stop command
    parser_stop = subparsers.add_parser('stop', help='Stop the embedding processor')
    
    # Process command
    parser_process = subparsers.add_parser('process', help='Manually trigger batch processing')
    
    # Search command
    parser_search = subparsers.add_parser('search', help='Search for similar embeddings')
    parser_search.add_argument('query', help='Query text to search for')
    parser_search.add_argument('--limit', type=int, default=10, help='Number of results to return')
    
    # Monitor command
    parser_monitor = subparsers.add_parser('monitor', help='Monitor processor status')
    parser_monitor.add_argument('--interval', type=int, default=5, 
                               help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create client
    client = EmbeddingServiceClient(args.url)
    
    # Route to appropriate command
    command_map = {
        'health': cmd_health,
        'status': cmd_status,
        'start': cmd_start,
        'stop': cmd_stop,
        'process': cmd_process,
        'search': cmd_search,
        'monitor': cmd_monitor,
    }
    
    if args.command in command_map:
        command_map[args.command](args, client)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

if __name__ == '__main__':
    main()