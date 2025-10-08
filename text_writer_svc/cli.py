#!/usr/bin/env python3

import click
import requests
import json
import sys
import uuid
from typing import Optional
from datetime import datetime

class TextWriterCLI:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
    
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to the service"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    def health_check(self):
        """Check service health"""
        return self._make_request('GET', '/health')
    
    def get_messages(self, limit: int = 10, offset: int = 0):
        """Get messages with pagination"""
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', '/messages', params=params)
    
    def get_message(self, message_id: str):
        """Get a specific message by ID"""
        return self._make_request('GET', f'/messages/{message_id}')
    
    def create_message(self, message: str, message_id: Optional[str] = None):
        """Create a new message"""
        data = {'message': message}
        if message_id:
            data['id'] = message_id
        return self._make_request('POST', '/messages', json=data)
    
    def get_stats(self):
        """Get service statistics"""
        return self._make_request('GET', '/stats')

@click.group()
@click.option('--url', default='http://localhost:5001', help='Base URL of the text writer service')
@click.pass_context
def cli(ctx, url):
    """Text Writer Service CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = TextWriterCLI(url)

@cli.command()
@click.pass_context
def health(ctx):
    """Check service health"""
    client = ctx.obj['client']
    try:
        result = client.health_check()
        click.echo(json.dumps(result, indent=2))
        if result.get('status') == 'healthy':
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--limit', '-l', default=10, help='Number of messages to retrieve')
@click.option('--offset', '-o', default=0, help='Number of messages to skip')
@click.option('--format', 'output_format', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def list(ctx, limit, offset, output_format):
    """List messages"""
    client = ctx.obj['client']
    result = client.get_messages(limit, offset)
    
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        messages = result['messages']
        total = result['total']
        
        click.echo(f"Messages {offset + 1}-{offset + len(messages)} of {total}")
        click.echo("-" * 80)
        
        for msg in messages:
            click.echo(f"ID: {msg['id']}")
            click.echo(f"Message: {msg['message'][:100]}{'...' if len(msg['message']) > 100 else ''}")
            click.echo(f"Created: {msg['created_at']}")
            click.echo(f"Processed: {msg['processed_at']}")
            click.echo("-" * 80)

@cli.command()
@click.argument('message_id')
@click.option('--format', 'output_format', type=click.Choice(['json', 'pretty']), default='pretty', help='Output format')
@click.pass_context
def get(ctx, message_id, output_format):
    """Get a specific message by ID"""
    client = ctx.obj['client']
    result = client.get_message(message_id)
    
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"ID: {result['id']}")
        click.echo(f"Message: {result['message']}")
        click.echo(f"Created: {result['created_at']}")
        click.echo(f"Processed: {result['processed_at']}")

@cli.command()
@click.argument('message')
@click.option('--id', 'message_id', help='Custom message ID (UUID will be generated if not provided)')
@click.pass_context
def create(ctx, message, message_id):
    """Create a new message"""
    client = ctx.obj['client']
    result = client.create_message(message, message_id)
    
    click.echo(f"Message created successfully!")
    click.echo(f"ID: {result['id']}")
    click.echo(f"Message: {result['message']}")

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['json', 'pretty']), default='pretty', help='Output format')
@click.pass_context
def stats(ctx, output_format):
    """Get service statistics"""
    client = ctx.obj['client']
    result = client.get_stats()
    
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo("Text Writer Service Statistics")
        click.echo("=" * 40)
        click.echo(f"Total Messages: {result['total_messages']}")
        click.echo(f"Recent Messages (1h): {result['recent_messages_1h']}")
        click.echo(f"Kafka Consumer Running: {result['kafka_consumer_running']}")
        if result['oldest_message']:
            click.echo(f"Oldest Message: {result['oldest_message']}")
        if result['newest_message']:
            click.echo(f"Newest Message: {result['newest_message']}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--batch-size', default=10, help='Number of messages to send per batch')
@click.pass_context
def send_file(ctx, file_path, batch_size):
    """Send messages from a text file (one message per line)"""
    client = ctx.obj['client']
    
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    click.echo(f"Sending {len(lines)} messages from {file_path}")
    
    with click.progressbar(lines, label='Sending messages') as bar:
        for line in bar:
            try:
                client.create_message(line)
            except Exception as e:
                click.echo(f"Failed to send message: {e}", err=True)
                continue
    
    click.echo("All messages sent!")

if __name__ == '__main__':
    cli()