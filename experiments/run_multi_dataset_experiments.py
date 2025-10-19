#!/usr/bin/env python3
"""
Multi-Dataset Ingestion Experiment Runner

This script runs comprehensive ingestion experiments across CC News, Wikipedia, and Arxiv datasets
with configurable chunk sizes and burst patterns. It measures end-to-end latency from streaming
to Kafka topic through embedding generation and persistence in vector database.
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datasets/cc_news'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datasets/arxiv_abstracts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'datasets/wikimedia_difs'))

try:
    from stream_ccnews import stream_cc_news_files, estimate_tokens as estimate_ccnews_tokens
    from stream_arxiv import stream_arxiv_sample, estimate_tokens as estimate_arxiv_tokens
    from stream_wikipedia import stream_wikipedia_sample, estimate_tokens as estimate_wiki_tokens
except ImportError as e:
    print(f"Error importing dataset modules: {e}")
    print("Make sure you're running from the experiments directory and all dataset modules are available.")
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
    architecture: str
    model: str
    dataset: str
    chunk_size_kb: float
    burst_length_s: Optional[int]  # Renamed for clarity (burst duration)
    result_ms: float  # Primary result metric (avg latency)
    chunk_size_tokens: int
    burst_enabled: bool
    burst_interval_s: Optional[int]
    chunks_produced: int
    chunks_processed: int
    chunks_persisted: int
    total_duration_ms: float
    throughput_chunks_per_s: float
    throughput_tokens_per_s: float
    success_rate: float
    status: str
    error_message: Optional[str] = None


class DatasetStreamer:
    """Wrapper for different dataset streaming APIs."""
    
    @staticmethod
    def get_streamer(dataset: str, chunk_size_tokens: int, max_chunks: int) -> Iterator[str]:
        """Get appropriate streamer for dataset type."""
        if dataset == "cc_news":
            # CC News doesn't have max_chunks parameter, use file_indices to limit
            return stream_cc_news_files(token_length=chunk_size_tokens, file_indices=[0, 1])  # First 2 files
        elif dataset == "arxiv":
            return stream_arxiv_sample(token_length=chunk_size_tokens, max_papers=max_chunks)
        elif dataset == "wikipedia":
            return stream_wikipedia_sample(token_length=chunk_size_tokens, max_articles=max_chunks)
        else:
            raise ValueError(f"Unknown dataset: {dataset}")
    
    @staticmethod
    def estimate_tokens(dataset: str, text: str) -> int:
        """Get appropriate token estimator for dataset type."""
        if dataset == "cc_news":
            return estimate_ccnews_tokens(text)
        elif dataset == "arxiv":
            return estimate_arxiv_tokens(text)
        elif dataset == "wikipedia":
            return estimate_wiki_tokens(text)
        else:
            return len(text) // 4  # Fallback estimation


def kb_to_tokens(kb: float) -> int:
    """Convert kilobytes to approximate tokens (1 token ≈ 4 chars, 1 KB = 1024 chars)."""
    return int((kb * 1024) / 4)


def get_pg_conn():
    """Get PostgreSQL connection for verification."""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = int(os.getenv('DATABASE_PORT', '5434'))  # Architecture3 uses port 5434
    database = os.getenv('DATABASE_NAME', 'realtime_llm')  # Architecture3 uses realtime_llm
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', 'password')  # Architecture3 uses 'password'
    return psycopg2.connect(host=host, port=port, database=database, user=user, password=password)


def wait_for_embedding(conn, table: str, message_id: str, timeout_s: int = 60) -> bool:
    """Wait for embedding to appear in database table."""
    try:
        with conn.cursor() as cur:
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                # For CQRS architecture, check text_embeddings table with text_message_id
                if table == 'text_embeddings':
                    cur.execute(f"SELECT 1 FROM {table} WHERE text_message_id = %s", (message_id,))
                else:
                    cur.execute(f"SELECT 1 FROM {table} WHERE id = %s", (message_id,))
                found = cur.fetchone() is not None
                if found:
                    return True
                time.sleep(0.5)
        return False
    except Exception as e:
        print(f"Database error checking for {message_id}: {e}")
        return False


class BurstController:
    """Controls burst streaming patterns."""
    
    def __init__(self, duration_s: int, interval_s: int):
        self.duration_s = duration_s
        self.interval_s = interval_s
        self.start_time = time.time()
        self.last_burst_start = 0
        self.bursting = True
        
    def should_send_now(self) -> bool:
        """Determine if we should send data now based on burst pattern."""
        elapsed = time.time() - self.start_time
        
        if elapsed >= self.duration_s:
            return False  # Experiment duration completed
            
        # Calculate position in burst cycle
        cycle_time = elapsed % (2 * self.interval_s)  # burst + pause
        
        # First half of cycle = burst, second half = pause
        return cycle_time < self.interval_s


class ExperimentRunner:
    """Main experiment runner class."""
    
    def __init__(self, bootstrap_servers: str, input_topic: str, output_topic: str, table: str, 
                 architecture: str, model: str):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.table = table
        self.architecture = architecture
        self.model = model
        
    def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a single experiment with the given configuration."""
        print(f"🚀 Running experiment: {config.dataset}, {config.chunk_size_kb}KB chunks, burst={config.burst_enabled}")
        
        start_time = time.time()
        chunk_size_tokens = kb_to_tokens(config.chunk_size_kb)
        
        try:
            # Get data streamer
            streamer = DatasetStreamer.get_streamer(config.dataset, chunk_size_tokens, config.max_chunks)
            
            # Setup Kafka producer
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
            )
            
            # Initialize tracking variables
            produced_ids = []
            processed_ids = set()
            persisted_ids = set()
            total_tokens = 0
            
            # Setup burst controller if needed
            burst_controller = None
            if config.burst_enabled:
                burst_controller = BurstController(config.burst_duration_s, config.burst_interval_s)
            
            # For CQRS architecture, we skip Kafka output monitoring 
            # and go directly to database verification
            
            # Stream and produce data
            for i, chunk in enumerate(streamer):
                # Check burst pattern
                if burst_controller and not burst_controller.should_send_now():
                    time.sleep(0.1)  # Small delay during pause
                    continue
                
                message_id = str(uuid.uuid4())
                tokens = DatasetStreamer.estimate_tokens(config.dataset, chunk)
                total_tokens += tokens
                
                payload = {
                    'id': message_id,
                    'text': chunk,
                    'timestamp': time.time(),
                    'source': f'ingestion-experiment-{config.dataset}',
                    'experiment_config': {
                        'dataset': config.dataset,
                        'chunk_size_kb': config.chunk_size_kb,
                        'chunk_size_tokens': chunk_size_tokens,
                        'burst_enabled': config.burst_enabled
                    }
                }
                
                try:
                    future = producer.send(self.input_topic, value=payload, key=message_id)
                    future.get(timeout=10)
                    produced_ids.append(message_id)
                    
                    if config.burst_enabled and burst_controller.should_send_now():
                        # During burst, send rapidly
                        time.sleep(0.01)
                    elif not config.burst_enabled:
                        # Regular streaming, small delay
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"❌ Failed to produce message {message_id}: {e}")
                    continue
                
                # Check if we've reached experiment limits
                if burst_controller and time.time() - burst_controller.start_time >= config.burst_duration_s:
                    break
                    
                if len(produced_ids) >= config.max_chunks:
                    break
            
            producer.flush()
            producer.close()
            
            # For CQRS architecture: Wait for database processing directly
            print(f"🔍 Verifying CQRS processing for {len(produced_ids)} messages...")
            processed_ids = self._wait_for_cqrs_processing(produced_ids, config.timeout_s)
            persisted_ids = processed_ids  # In CQRS, processed = persisted
            
            # Calculate results
            end_time = time.time()
            total_duration_ms = (end_time - start_time) * 1000
            
            chunks_produced = len(produced_ids)
            chunks_processed = len(processed_ids)
            chunks_persisted = len(persisted_ids)
            
            avg_latency_ms = total_duration_ms / max(1, chunks_processed)
            throughput_chunks_per_s = chunks_processed / max(0.001, (end_time - start_time))
            throughput_tokens_per_s = total_tokens / max(0.001, (end_time - start_time))
            success_rate = chunks_processed / max(1, chunks_produced)
            
            result = ExperimentResult(
                architecture=self.architecture,
                model=self.model,
                dataset=config.dataset,
                chunk_size_kb=config.chunk_size_kb,
                burst_length_s=config.burst_duration_s if config.burst_enabled else None,
                result_ms=avg_latency_ms,
                chunk_size_tokens=chunk_size_tokens,
                burst_enabled=config.burst_enabled,
                burst_interval_s=config.burst_interval_s if config.burst_enabled else None,
                chunks_produced=chunks_produced,
                chunks_processed=chunks_processed,
                chunks_persisted=chunks_persisted,
                total_duration_ms=total_duration_ms,
                throughput_chunks_per_s=throughput_chunks_per_s,
                throughput_tokens_per_s=throughput_tokens_per_s,
                success_rate=success_rate,
                status='success'
            )
            
            print(f"✅ Experiment completed: {chunks_processed}/{chunks_produced} processed, {success_rate*100:.1f}% success rate")
            return result
            
        except Exception as e:
            print(f"❌ Experiment failed: {e}")
            return ExperimentResult(
                architecture=self.architecture,
                model=self.model,
                dataset=config.dataset,
                chunk_size_kb=config.chunk_size_kb,
                burst_length_s=config.burst_duration_s if config.burst_enabled else None,
                result_ms=0,
                chunk_size_tokens=chunk_size_tokens,
                burst_enabled=config.burst_enabled,
                burst_interval_s=config.burst_interval_s if config.burst_enabled else None,
                chunks_produced=0,
                chunks_processed=0,
                chunks_persisted=0,
                total_duration_ms=0,
                throughput_chunks_per_s=0,
                throughput_tokens_per_s=0,
                success_rate=0,
                status='error',
                error_message=str(e)
            )
    
    def _wait_for_cqrs_processing(self, produced_ids: List[str], timeout_s: int) -> set:
        """Wait for CQRS service to process messages and return processed IDs."""
        print(f"⏳ Waiting up to {timeout_s}s for CQRS processing...")
        
        processed_ids = set()
        deadline = time.time() + timeout_s
        last_count = 0
        
        while time.time() < deadline:
            try:
                conn = get_pg_conn()
                for msg_id in produced_ids:
                    if msg_id not in processed_ids:
                        # Check if embedding exists in database
                        if wait_for_embedding(conn, self.table, msg_id, timeout_s=1):
                            processed_ids.add(msg_id)
                conn.close()
                
                current_count = len(processed_ids)
                if current_count > last_count:
                    print(f"📈 CQRS processed: {current_count}/{len(produced_ids)}")
                    last_count = current_count
                
                if current_count >= len(produced_ids):
                    break
                    
            except Exception as e:
                print(f"❌ Database check error: {e}")
                
            time.sleep(2)  # Check every 2 seconds
        
        print(f"🏁 Final CQRS processing: {len(processed_ids)}/{len(produced_ids)}")
        return processed_ids


def save_results_csv(results: List[ExperimentResult], output_path: str):
    """Save experiment results to CSV file."""
    if not results:
        return
    
    # Primary CSV with requested columns
    primary_fieldnames = [
        'Architecture', 'Model', 'Dataset', 'Chunk', 'Burst_Length', 'Result_ms'
    ]
    
    # Detailed CSV with all metrics
    detailed_fieldnames = [
        'architecture', 'model', 'dataset', 'chunk_size_kb', 'burst_length_s', 'result_ms',
        'chunk_size_tokens', 'burst_enabled', 'burst_interval_s', 'chunks_produced', 
        'chunks_processed', 'chunks_persisted', 'total_duration_ms', 
        'throughput_chunks_per_s', 'throughput_tokens_per_s', 'success_rate', 
        'status', 'error_message'
    ]
    
    # Save primary CSV (user-requested format)
    primary_path = output_path.replace('.csv', '_summary.csv')
    with open(primary_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(primary_fieldnames)
        
        for result in results:
            writer.writerow([
                result.architecture,
                result.model, 
                result.dataset,
                result.chunk_size_kb,
                result.burst_length_s if result.burst_length_s is not None else '',
                result.result_ms
            ])
    
    # Save detailed CSV (full metrics)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=detailed_fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(asdict(result))
    
    print(f"📄 Summary results saved to: {primary_path}")
    print(f"📄 Detailed results saved to: {output_path}")


def run_smoke_test(runner: ExperimentRunner) -> bool:
    """Run a quick smoke test to verify the setup is working."""
    print("🔥 Running smoke test...")
    
    smoke_configs = [
        ExperimentConfig(
            dataset="cc_news",
            chunk_size_kb=1.0,
            burst_enabled=False,
            max_chunks=3,
            timeout_s=60
        ),
        ExperimentConfig(
            dataset="cc_news", 
            chunk_size_kb=2.0,
            burst_enabled=True,
            burst_duration_s=10,
            burst_interval_s=2,
            max_chunks=3,
            timeout_s=60
        )
    ]
    
    results = []
    for i, config in enumerate(smoke_configs, 1):
        print(f"🧪 Smoke test {i}/{len(smoke_configs)}: {config.dataset}, {config.chunk_size_kb}KB, burst={config.burst_enabled}")
        result = runner.run_experiment(config)
        results.append(result)
        
        if result.status != 'success':
            print(f"❌ Smoke test {i} failed: {result.error_message}")
            return False
    
    # Save smoke test results
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    smoke_csv = f"smoke_test_results_{timestamp}.csv"
    save_results_csv(results, smoke_csv)
    
    print("✅ All smoke tests passed!")
    print(f"📄 Smoke test results saved to: {smoke_csv}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Run comprehensive ingestion experiments across multiple datasets')
    
    # Kafka configuration
    parser.add_argument('--bootstrap-servers', default=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    parser.add_argument('--input-topic', default=os.getenv('KAFKA_INPUT_TOPIC', 'text-messages'))
    parser.add_argument('--output-topic', default=os.getenv('KAFKA_OUTPUT_TOPIC', 'embeddings'))
    parser.add_argument('--table', default=os.getenv('EMBEDDINGS_TABLE', 'text_embeddings'))
    
    # Required experiment parameters
    parser.add_argument('--architecture', required=True,
                      help='Architecture name (e.g., "architecture1", "architecture2")')
    parser.add_argument('--model', required=True, 
                      help='Model name (e.g., "sentence-transformers/all-MiniLM-L6-v2")')
    
    # Experiment configuration
    parser.add_argument('--datasets', nargs='+', default=['cc_news', 'arxiv', 'wikipedia'], 
                      help='Datasets to test (default: all)')
    parser.add_argument('--chunk-sizes', nargs='+', type=float, 
                      default=[0.5, 1, 2, 5, 10, 20, 40, 80],
                      help='Chunk sizes in KB to test (default: 0.5 to 80)')
    parser.add_argument('--burst-durations', nargs='+', type=int, default=[30, 60],
                      help='Burst durations in seconds (default: 30, 60)')
    parser.add_argument('--burst-interval', type=int, default=5,
                      help='Burst interval in seconds (default: 5)')
    parser.add_argument('--max-chunks', type=int, default=50,
                      help='Maximum chunks per experiment (default: 50)')
    parser.add_argument('--timeout', type=int, default=300,
                      help='Timeout per experiment in seconds (default: 300)')
    
    # Execution modes
    parser.add_argument('--smoke-test', action='store_true', 
                      help='Run smoke test only')
    parser.add_argument('--no-burst', action='store_true',
                      help='Skip burst experiments')
    parser.add_argument('--output-dir', default='./experiment_results',
                      help='Output directory for results (default: ./experiment_results)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize experiment runner
    runner = ExperimentRunner(
        bootstrap_servers=args.bootstrap_servers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        table=args.table,
        architecture=args.architecture,
        model=args.model
    )
    
    # Run smoke test if requested
    if args.smoke_test:
        # For smoke test, use default values if not provided
        if not hasattr(args, 'architecture') or not args.architecture:
            args.architecture = "test_architecture" 
        if not hasattr(args, 'model') or not args.model:
            args.model = "test_model"
        
        # Re-initialize runner with smoke test defaults
        runner = ExperimentRunner(
            bootstrap_servers=args.bootstrap_servers,
            input_topic=args.input_topic,
            output_topic=args.output_topic,
            table=args.table,
            architecture=args.architecture,
            model=args.model
        )
        
        smoke_passed = run_smoke_test(runner)
        sys.exit(0 if smoke_passed else 1)
    
    # Generate experiment configurations
    configs = []
    
    for dataset in args.datasets:
        for chunk_size in args.chunk_sizes:
            # Regular streaming experiment
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
                        burst_interval_s=args.burst_interval,
                        max_chunks=args.max_chunks,
                        timeout_s=args.timeout
                    ))
    
    print(f"🎯 Running {len(configs)} experiments...")
    
    # Run all experiments
    all_results = []
    
    for i, config in enumerate(configs, 1):
        print(f"\n📊 Experiment {i}/{len(configs)}")
        result = runner.run_experiment(config)
        all_results.append(result)
        
        # Save intermediate results
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        csv_path = output_dir / f"ingestion_results_{timestamp}.csv"
        save_results_csv(all_results, str(csv_path))
        
        # Brief delay between experiments
        time.sleep(2)
    
    # Generate summary
    print(f"\n🎉 All experiments completed!")
    print(f"📈 Total experiments: {len(all_results)}")
    
    successful = [r for r in all_results if r.status == 'success']
    failed = [r for r in all_results if r.status == 'error']
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_throughput = sum(r.throughput_chunks_per_s for r in successful) / len(successful)
        avg_success_rate = sum(r.success_rate for r in successful) / len(successful)
        print(f"📊 Average throughput: {avg_throughput:.2f} chunks/s")
        print(f"📊 Average success rate: {avg_success_rate*100:.1f}%")
    
    # Final results save
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    final_csv = output_dir / f"final_ingestion_results_{timestamp}.csv"
    save_results_csv(all_results, str(final_csv))
    
    print(f"\n📄 Final results saved to: {final_csv}")


if __name__ == '__main__':
    main()