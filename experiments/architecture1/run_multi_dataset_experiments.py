#!/usr/bin/env python3
"""
Multi-Dataset Ingestion Experiment Runner for Architecture 1

This script runs comprehensive ingestion experiments across CC News, Wikipedia, and Arxiv datasets
with configurable chunk sizes and burst patterns. It measures end-to-end latency from streaming
to Kafka input topic through embedding generation service to output topic and finally persistence 
in vector database via writer service.

Architecture 1 Pipeline:
1. Data -> text-messages topic (input)
2. Embedding service reads from text-messages, generates embeddings
3. Embedding service writes to embeddings topic (output)
4. Writer service reads embeddings topic and persists to PostgreSQL
"""

import os
import sys
import json
import time
import uuid
import argparse
import csv
import threading
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Iterator, Union
from pathlib import Path

import psycopg2
from psycopg2 import sql as _psql_sql
from kafka import KafkaProducer, KafkaConsumer

# Import our dataset streaming modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/cc_news'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/arxiv_abstracts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/wikimedia_difs'))

try:
    from stream_ccnews import stream_cc_news_files, estimate_tokens as estimate_ccnews_tokens
    from stream_arxiv import stream_arxiv_sample, estimate_tokens as estimate_arxiv_tokens
    from stream_wikipedia import stream_wikipedia_sample, estimate_tokens as estimate_wiki_tokens
except ImportError as e:
    print(f"Error importing dataset modules: {e}")
    print("Make sure you're running from the architecture1 directory and all dataset modules are available.")
    sys.exit(1)


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run."""
    dataset: str
    chunk_size_kb: float
    burst_enabled: bool = False
    burst_duration_s: int = 30
    burst_interval_s: int = 5
    max_chunks: int = 100
    timeout_s: int = 120


@dataclass
class ExperimentResult:
    """Results from a single experiment run."""
    config: ExperimentConfig
    chunks_produced: int
    chunks_processed: int  # Embeddings generated
    chunks_persisted: int  # Written to database
    start_time: float
    end_time: float
    avg_latency_ms: float
    throughput_chunks_per_s: float
    throughput_tokens_per_s: float
    success_rate: float
    total_tokens: int
    error_count: int = 0
    errors: List[str] = None


def estimate_tokens(text: str) -> int:
    """Estimate tokens in text using simple character-based approximation."""
    if not text:
        return 0
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4


def kb_to_tokens(kb: float) -> int:
    """Convert KB to estimated token count."""
    return int((kb * 1024) / 4)


def chunk_text_by_tokens(text: str, target_tokens: int) -> List[str]:
    """Chunk text to target token count."""
    if not text:
        return []
    
    estimated_chars_per_chunk = target_tokens * 4
    chunks = []
    
    start = 0
    while start < len(text):
        end = min(start + estimated_chars_per_chunk, len(text))
        chunks.append(text[start:end])
        start = end
    
    return chunks


def wait_for_embedding(conn, table: str, message_id: str, timeout_s: int = 60) -> bool:
    """Check if embedding exists in database."""
    start_time = time.time()
    with conn.cursor() as cursor:
        while time.time() - start_time < timeout_s:
            try:
                # For architecture1, check embeddings table with id field
                cursor.execute(f"SELECT 1 FROM {table} WHERE id = %s LIMIT 1", (message_id,))
                result = cursor.fetchone()
                if result:
                    return True
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
    return False


class Architecture1ExperimentRunner:
    """Experiment runner for Architecture 1 (Kafka pipeline)."""
    
    def __init__(self, architecture: str, model: str):
        self.architecture = architecture
        self.model = model
        
        # Kafka configuration for Architecture 1
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.input_topic = os.getenv('KAFKA_INPUT_TOPIC', 'text-messages')
        self.output_topic = os.getenv('KAFKA_OUTPUT_TOPIC', 'embeddings')
        
        # Database configuration for Architecture 1
        self.db_host = os.getenv('DATABASE_HOST', 'localhost')
        self.db_port = int(os.getenv('DATABASE_PORT', '5432'))
        self.db_name = os.getenv('DATABASE_NAME', 'embeddings_db')
        self.db_user = os.getenv('DATABASE_USER', 'postgres')
        self.db_password = os.getenv('DATABASE_PASSWORD', 'password')
        self.table = os.getenv('DATABASE_TABLE', 'embeddings')
        
        # Initialize connections
        self.producer = None
        self.consumer = None
        self.db_conn = None
        
    def connect(self):
        """Establish connections to Kafka and database."""
        try:
            # Kafka producer for text messages
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            
            # Kafka consumer for embeddings output
            self.consumer = KafkaConsumer(
                self.output_topic,
                bootstrap_servers=self.kafka_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=False,
                group_id=f'experiment-{uuid.uuid4()}'
            )
            
            # Database connection
            self.db_conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            self.db_conn.autocommit = True
            
            print(f"✅ Connected to Kafka ({self.kafka_servers}) and database ({self.db_host}:{self.db_port})")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close all connections."""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        if self.db_conn:
            self.db_conn.close()
    
    def stream_dataset(self, dataset: str, target_tokens: int, max_chunks: int) -> Iterator[Dict]:
        """Stream dataset with chunking."""
        chunk_count = 0
        
        if dataset == 'cc_news':
            for text_chunk in stream_cc_news_files(
                token_length=target_tokens,
                file_indices=[0, 1]  # First 2 files
            ):
                if chunk_count >= max_chunks:
                    break
                yield {
                    'id': str(uuid.uuid4()),
                    'text': text_chunk,
                    'metadata': {
                        'dataset': dataset,
                        'source': 'cc_news',
                        'tokens': estimate_tokens(text_chunk)
                    },
                    'timestamp': time.time()
                }
                chunk_count += 1
                
        elif dataset == 'arxiv':
            for text_chunk in stream_arxiv_sample(
                token_length=target_tokens,
                max_papers=max_chunks//10
            ):
                if chunk_count >= max_chunks:
                    break
                yield {
                    'id': str(uuid.uuid4()),
                    'text': text_chunk,
                    'metadata': {
                        'dataset': dataset,
                        'source': 'arxiv',
                        'tokens': estimate_tokens(text_chunk)
                    },
                    'timestamp': time.time()
                }
                chunk_count += 1
                
        elif dataset == 'wikipedia':
            for text_chunk in stream_wikipedia_sample(
                token_length=target_tokens,
                max_articles=max_chunks//10
            ):
                if chunk_count >= max_chunks:
                    break
                yield {
                    'id': str(uuid.uuid4()),
                    'text': text_chunk,
                    'metadata': {
                        'dataset': dataset,
                        'source': 'wikipedia',
                        'tokens': estimate_tokens(text_chunk)
                    },
                    'timestamp': time.time()
                }
                chunk_count += 1
    
    def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a single experiment."""
        print(f"🚀 Running experiment: {config.dataset}, {config.chunk_size_kb}KB chunks, burst={config.burst_enabled}")
        
        target_tokens = kb_to_tokens(config.chunk_size_kb)
        
        start_time = time.time()
        produced_ids = []
        total_tokens = 0
        
        try:
            # Phase 1: Stream data to Kafka input topic
            for chunk in self.stream_dataset(config.dataset, target_tokens, config.max_chunks):
                message = {
                    'id': chunk['id'],
                    'text': chunk['text'],
                    'metadata': chunk['metadata'],
                    'timestamp': chunk['timestamp']
                }
                
                # Send to input topic (text-messages)
                self.producer.send(
                    self.input_topic,
                    key=chunk['id'],
                    value=message
                )
                
                produced_ids.append(chunk['id'])
                total_tokens += chunk['metadata']['tokens']
                
                # Burst pattern implementation
                if config.burst_enabled:
                    # Send bursts of messages then pause
                    if len(produced_ids) % 5 == 0:  # Every 5 messages
                        time.sleep(config.burst_interval_s / 1000.0)  # Short pause
                else:
                    # Steady rate - small delay between messages
                    time.sleep(0.01)  # 10ms delay
            
            self.producer.flush()
            print(f"📊 Produced {len(produced_ids)} chunks ({total_tokens} tokens) to {self.input_topic}")
            
            # Architecture 1 pipeline: Wait for embedding generation AND database persistence
            processed_ids = self._wait_for_embeddings_topic(produced_ids, config.timeout_s)
            persisted_ids = self._wait_for_database_persistence(produced_ids, config.timeout_s)
            
            end_time = time.time()
            duration = end_time - start_time
            
            chunks_processed = len(processed_ids)
            chunks_persisted = len(persisted_ids)
            
            # Calculate metrics
            avg_latency_ms = (duration * 1000) / max(1, chunks_persisted)
            throughput_chunks_per_s = chunks_persisted / max(0.001, duration)
            throughput_tokens_per_s = total_tokens / max(0.001, duration)
            success_rate = chunks_persisted / max(1, len(produced_ids))
            
            print(f"✅ Experiment completed: {chunks_persisted}/{len(produced_ids)} processed, {success_rate*100:.1f}% success rate")
            
            return ExperimentResult(
                config=config,
                chunks_produced=len(produced_ids),
                chunks_processed=chunks_processed,
                chunks_persisted=chunks_persisted,
                start_time=start_time,
                end_time=end_time,
                avg_latency_ms=avg_latency_ms,
                throughput_chunks_per_s=throughput_chunks_per_s,
                throughput_tokens_per_s=throughput_tokens_per_s,
                success_rate=success_rate,
                total_tokens=total_tokens
            )
            
        except Exception as e:
            print(f"❌ Experiment failed: {e}")
            return ExperimentResult(
                config=config,
                chunks_produced=len(produced_ids),
                chunks_processed=0,
                chunks_persisted=0,
                start_time=start_time,
                end_time=time.time(),
                avg_latency_ms=0,
                throughput_chunks_per_s=0,
                throughput_tokens_per_s=0,
                success_rate=0,
                total_tokens=total_tokens,
                error_count=1,
                errors=[str(e)]
            )
    
    def _wait_for_embeddings_topic(self, produced_ids: List[str], timeout_s: int) -> set:
        """Wait for messages to appear in embeddings output topic."""
        print(f"⏳ Monitoring embeddings topic ({self.output_topic}) for {len(produced_ids)} messages...")
        
        processed_ids = set()
        start_time = time.time()
        check_interval = 2  # seconds
        
        while time.time() - start_time < timeout_s and len(processed_ids) < len(produced_ids):
            # Poll for new messages with timeout
            messages = self.consumer.poll(timeout_ms=check_interval * 1000)
            
            for topic_partition, records in messages.items():
                for record in records:
                    if record.key in produced_ids:
                        processed_ids.add(record.key)
            
            elapsed = int(time.time() - start_time)
            current_count = len(processed_ids)
            if elapsed % 5 == 0:  # Print every 5 seconds
                print(f"⏳ {elapsed}s/{timeout_s}s - Embeddings generated: {current_count}/{len(produced_ids)}")
        
        final_count = len(processed_ids)
        elapsed = int(time.time() - start_time)
        
        if final_count < len(produced_ids):
            print(f"⚠️  Embedding generation incomplete after {elapsed}s: {final_count}/{len(produced_ids)}")
        else:
            print(f"🏁 Embedding generation complete: {final_count}/{len(produced_ids)}")
        
        return processed_ids
    
    def _wait_for_database_persistence(self, produced_ids: List[str], timeout_s: int) -> set:
        """Wait for messages to be persisted in database."""
        print(f"⏳ Monitoring database table ({self.table}) for {len(produced_ids)} messages...")
        
        persisted_ids = set()
        start_time = time.time()
        check_interval = 5  # seconds
        
        while time.time() - start_time < timeout_s and len(persisted_ids) < len(produced_ids):
            current_count = 0
            
            try:
                with self.db_conn.cursor() as cursor:
                    for msg_id in produced_ids:
                        if msg_id not in persisted_ids:
                            if wait_for_embedding(self.db_conn, self.table, msg_id, timeout_s=1):
                                persisted_ids.add(msg_id)
                                current_count += 1
            except Exception as e:
                print(f"⚠️  Database check error: {e}")
                time.sleep(1)
                continue
            
            elapsed = int(time.time() - start_time)
            if elapsed % check_interval == 0:  # Print every 5 seconds
                print(f"⏳ {elapsed}s/{timeout_s}s - Database persisted: {len(persisted_ids)}/{len(produced_ids)}")
            
            time.sleep(1)
        
        final_count = len(persisted_ids)
        elapsed = int(time.time() - start_time)
        
        if final_count < len(produced_ids):
            print(f"⚠️  Database persistence incomplete after {elapsed}s: {final_count}/{len(produced_ids)}")
        else:
            print(f"🏁 Database persistence complete: {final_count}/{len(produced_ids)}")
        
        return persisted_ids


def run_smoke_test(runner: Architecture1ExperimentRunner) -> bool:
    """Run smoke test with minimal configuration."""
    print("🔥 Running smoke test...")
    
    configs = [
        ExperimentConfig(dataset='cc_news', chunk_size_kb=1.0, max_chunks=3, timeout_s=60),
        ExperimentConfig(dataset='cc_news', chunk_size_kb=2.0, burst_enabled=True, max_chunks=3, timeout_s=60)
    ]
    
    all_passed = True
    for i, config in enumerate(configs, 1):
        print(f"🧪 Smoke test {i}/{len(configs)}: {config.dataset}, {config.chunk_size_kb}KB, burst={config.burst_enabled}")
        result = runner.run_experiment(config)
        
        if result.success_rate < 0.5:  # At least 50% success for smoke test
            print(f"❌ Smoke test {i} failed: {result.success_rate*100:.1f}% success rate")
            all_passed = False
        else:
            print(f"✅ Smoke test {i} passed: {result.success_rate*100:.1f}% success rate")
    
    return all_passed


def save_results(results: List[ExperimentResult], output_dir: Path, architecture: str, model: str):
    """Save experiment results to CSV files."""
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    # Detailed results
    detailed_file = output_dir / f'experiment_results_{timestamp}.csv'
    with open(detailed_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'architecture', 'model', 'dataset', 'chunk_size_kb', 'burst_enabled',
            'chunks_produced', 'chunks_processed', 'chunks_persisted',
            'duration_s', 'avg_latency_ms', 'throughput_chunks_per_s', 
            'throughput_tokens_per_s', 'success_rate', 'total_tokens',
            'error_count', 'timestamp'
        ])
        
        for result in results:
            writer.writerow([
                architecture, model,
                result.config.dataset, result.config.chunk_size_kb, result.config.burst_enabled,
                result.chunks_produced, result.chunks_processed, result.chunks_persisted,
                result.end_time - result.start_time, result.avg_latency_ms,
                result.throughput_chunks_per_s, result.throughput_tokens_per_s,
                result.success_rate, result.total_tokens, result.error_count,
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.start_time))
            ])
    
    # Summary results
    summary_file = output_dir / f'experiment_results_{timestamp}_summary.csv'
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'dataset', 'avg_chunks_per_s', 'avg_tokens_per_s', 'avg_success_rate',
            'total_experiments', 'total_chunks', 'total_tokens'
        ])
        
        # Group by dataset
        dataset_stats = {}
        for result in results:
            dataset = result.config.dataset
            if dataset not in dataset_stats:
                dataset_stats[dataset] = []
            dataset_stats[dataset].append(result)
        
        for dataset, dataset_results in dataset_stats.items():
            avg_chunks_per_s = sum(r.throughput_chunks_per_s for r in dataset_results) / len(dataset_results)
            avg_tokens_per_s = sum(r.throughput_tokens_per_s for r in dataset_results) / len(dataset_results)
            avg_success_rate = sum(r.success_rate for r in dataset_results) / len(dataset_results)
            total_chunks = sum(r.chunks_produced for r in dataset_results)
            total_tokens = sum(r.total_tokens for r in dataset_results)
            
            writer.writerow([
                dataset, avg_chunks_per_s, avg_tokens_per_s, avg_success_rate,
                len(dataset_results), total_chunks, total_tokens
            ])
    
    print(f"📄 Detailed results saved to: {detailed_file.name}")
    print(f"📄 Summary results saved to: {summary_file.name}")
    
    return detailed_file, summary_file


def main():
    parser = argparse.ArgumentParser(description='Architecture 1 Multi-Dataset Experiment Runner')
    parser.add_argument('--architecture', default='architecture1',
                      help='Architecture name for tracking')
    parser.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2',
                      help='Model name used by embedding service')
    parser.add_argument('--datasets', nargs='+', default=['cc_news'],
                      choices=['cc_news', 'arxiv', 'wikipedia'],
                      help='Datasets to test')
    parser.add_argument('--chunk-sizes', nargs='+', type=float, default=[1.0, 5.0, 10.0],
                      help='Chunk sizes in KB')
    parser.add_argument('--burst-durations', nargs='+', type=int, default=[10, 30],
                      help='Burst durations in seconds')
    parser.add_argument('--max-chunks', type=int, default=100,
                      help='Maximum chunks per experiment')
    parser.add_argument('--timeout', type=int, default=120,
                      help='Timeout per experiment in seconds')
    parser.add_argument('--no-burst', action='store_true',
                      help='Skip burst experiments')
    parser.add_argument('--smoke-test', action='store_true',
                      help='Run minimal validation test')
    parser.add_argument('--output-dir', default='./experiment_results',
                      help='Output directory for results (default: ./experiment_results)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize experiment runner
    runner = Architecture1ExperimentRunner(args.architecture, args.model)
    
    try:
        runner.connect()
        
        if args.smoke_test:
            success = run_smoke_test(runner)
            if success:
                print("✅ All smoke tests passed!")
                # Save smoke test results with timestamp
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                smoke_file = output_dir / f'smoke_test_results_{timestamp}.csv'
                with open(smoke_file, 'w') as f:
                    f.write("test_type,status,timestamp\n")
                    f.write(f"smoke_test,passed,{timestamp}\n")
                print(f"📄 Smoke test results saved to: {smoke_file.name}")
                return 0
            else:
                print("❌ Smoke tests failed!")
                return 1
        
        # Generate experiment configurations
        configs = []
        for dataset in args.datasets:
            for chunk_size in args.chunk_sizes:
                # Non-burst experiment
                configs.append(ExperimentConfig(
                    dataset=dataset,
                    chunk_size_kb=chunk_size,
                    burst_enabled=False,
                    max_chunks=args.max_chunks,
                    timeout_s=args.timeout
                ))
                
                # Burst experiments
                if not args.no_burst:
                    for burst_duration in args.burst_durations:
                        configs.append(ExperimentConfig(
                            dataset=dataset,
                            chunk_size_kb=chunk_size,
                            burst_enabled=True,
                            burst_duration_s=burst_duration,
                            max_chunks=args.max_chunks,
                            timeout_s=args.timeout
                        ))
        
        print(f"🚀 Starting {len(configs)} experiments...")
        
        # Run experiments
        results = []
        for i, config in enumerate(configs, 1):
            print(f"\n{'='*60}")
            print(f"Experiment {i}/{len(configs)}")
            result = runner.run_experiment(config)
            results.append(result)
            
            # Short pause between experiments
            time.sleep(2)
        
        # Save results
        save_results(results, output_dir, args.architecture, args.model)
        
        # Print summary
        successful = sum(1 for r in results if r.success_rate > 0.8)
        print(f"\n🏁 Experiments completed: {successful}/{len(results)} successful")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Experiments interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        return 1
    finally:
        runner.disconnect()


if __name__ == '__main__':
    sys.exit(main())