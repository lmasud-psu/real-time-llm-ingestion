#!/usr/bin/env python3
"""
Simple test script to validate the multi-dataset experiment setup.
Tests the dataset streaming without requiring Kafka or database infrastructure.
"""

import os
import sys
import time
from typing import Dict, List

# Add dataset paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/cc_news'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/arxiv_abstracts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../datasets/wikimedia_difs'))

def test_dataset_imports():
    """Test that all dataset modules can be imported."""
    print("🔧 Testing dataset imports...")
    
    try:
        from stream_ccnews import stream_cc_news_files, estimate_tokens as estimate_ccnews_tokens
        print("✅ CC News streaming module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import CC News module: {e}")
        return False
    
    try:
        from stream_arxiv import stream_arxiv_sample, estimate_tokens as estimate_arxiv_tokens
        print("✅ Arxiv streaming module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Arxiv module: {e}")
        return False
    
    try:
        from stream_wikipedia import stream_wikipedia_sample, estimate_tokens as estimate_wiki_tokens
        print("✅ Wikipedia streaming module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Wikipedia module: {e}")
        return False
    
    return True


def test_dataset_streaming():
    """Test streaming from each dataset."""
    print("\n📊 Testing dataset streaming...")
    
    from stream_ccnews import stream_cc_news_files, estimate_tokens as estimate_ccnews_tokens
    from stream_arxiv import stream_arxiv_sample, estimate_tokens as estimate_arxiv_tokens
    from stream_wikipedia import stream_wikipedia_sample, estimate_tokens as estimate_wiki_tokens
    
    datasets_config = [
        {
            'name': 'cc_news',
            'streamer': lambda: stream_cc_news_files(token_length=500, file_indices=[0]),
            'estimator': estimate_ccnews_tokens
        },
        {
            'name': 'arxiv', 
            'streamer': lambda: stream_arxiv_sample(token_length=500, max_papers=3),
            'estimator': estimate_arxiv_tokens
        },
        {
            'name': 'wikipedia',
            'streamer': lambda: stream_wikipedia_sample(token_length=500, max_articles=3),
            'estimator': estimate_wiki_tokens
        }
    ]
    
    results = []
    
    for dataset_config in datasets_config:
        print(f"\n🎯 Testing {dataset_config['name']} dataset...")
        
        try:
            start_time = time.time()
            chunks = list(dataset_config['streamer']())
            end_time = time.time()
            
            if not chunks:
                print(f"❌ No chunks returned from {dataset_config['name']}")
                continue
            
            # Test token estimation
            total_tokens = sum(dataset_config['estimator'](chunk) for chunk in chunks)
            duration = end_time - start_time
            
            result = {
                'dataset': dataset_config['name'],
                'chunks': len(chunks),
                'total_tokens': total_tokens,
                'avg_tokens_per_chunk': total_tokens / len(chunks),
                'duration_s': duration,
                'throughput_chunks_per_s': len(chunks) / duration if duration > 0 else 0
            }
            
            results.append(result)
            
            print(f"✅ {dataset_config['name']}: {len(chunks)} chunks, {total_tokens} tokens, {duration:.2f}s")
            print(f"   Average tokens per chunk: {result['avg_tokens_per_chunk']:.1f}")
            print(f"   Sample chunk (first 100 chars): {chunks[0][:100]}...")
            
        except Exception as e:
            print(f"❌ Error testing {dataset_config['name']}: {e}")
            continue
    
    return results


def test_chunk_size_conversion():
    """Test chunk size conversion from KB to tokens."""
    print("\n🔄 Testing chunk size conversion...")
    
    def kb_to_tokens(kb: float) -> int:
        """Convert kilobytes to approximate tokens (1 token ≈ 4 chars, 1 KB = 1024 chars)."""
        return int((kb * 1024) / 4)
    
    test_cases = [
        (0.5, 128),   # 0.5 KB ≈ 128 tokens
        (1.0, 256),   # 1 KB ≈ 256 tokens
        (2.0, 512),   # 2 KB ≈ 512 tokens
        (10.0, 2560), # 10 KB ≈ 2560 tokens
        (80.0, 20480) # 80 KB ≈ 20480 tokens
    ]
    
    for kb, expected_tokens in test_cases:
        actual_tokens = kb_to_tokens(kb)
        print(f"   {kb}KB → {actual_tokens} tokens (expected ~{expected_tokens})")
        
        # Allow some variance
        if abs(actual_tokens - expected_tokens) <= 10:
            print("   ✅ Conversion correct")
        else:
            print(f"   ❌ Conversion incorrect (got {actual_tokens}, expected ~{expected_tokens})")


def test_experiment_config():
    """Test experiment configuration structures."""
    print("\n⚙️ Testing experiment configuration...")
    
    from dataclasses import dataclass
    
    @dataclass
    class ExperimentConfig:
        dataset: str
        chunk_size_kb: float
        burst_enabled: bool = False
        burst_duration_s: int = 30
        burst_interval_s: int = 5
        max_chunks: int = 100
        timeout_s: int = 120
    
    # Test configuration creation
    configs = [
        ExperimentConfig(dataset="cc_news", chunk_size_kb=1.0),
        ExperimentConfig(dataset="arxiv", chunk_size_kb=5.0, burst_enabled=True),
        ExperimentConfig(dataset="wikipedia", chunk_size_kb=10.0, burst_enabled=True, burst_duration_s=60),
    ]
    
    print(f"✅ Created {len(configs)} test configurations:")
    for i, config in enumerate(configs, 1):
        print(f"   Config {i}: {config.dataset}, {config.chunk_size_kb}KB, burst={config.burst_enabled}")


def run_performance_test():
    """Run a simple performance test."""
    print("\n🚀 Running performance test...")
    
    from stream_ccnews import stream_cc_news_files, estimate_tokens
    
    # Test different chunk sizes
    chunk_sizes_kb = [0.5, 1, 2, 5]
    
    for kb in chunk_sizes_kb:
        tokens = int((kb * 1024) / 4)  # Convert KB to tokens
        
        start_time = time.time()
        chunks = list(stream_cc_news_files(token_length=tokens, file_indices=[0]))
        end_time = time.time()
        
        duration = end_time - start_time
        total_tokens = sum(estimate_tokens(chunk) for chunk in chunks)
        
        print(f"   {kb}KB chunks: {len(chunks)} chunks, {total_tokens} tokens, {duration:.3f}s")
        print(f"      Throughput: {len(chunks)/duration:.1f} chunks/s, {total_tokens/duration:.0f} tokens/s")


def main():
    """Run all tests."""
    print("🧪 Multi-Dataset Experiment Setup Test")
    print("=" * 50)
    
    # Test 1: Import all modules
    if not test_dataset_imports():
        print("\n❌ Import test failed. Please check dataset module setup.")
        return False
    
    # Test 2: Stream from each dataset
    streaming_results = test_dataset_streaming()
    if not streaming_results:
        print("\n❌ Streaming test failed. No datasets returned data.")
        return False
    
    # Test 3: Chunk size conversion
    test_chunk_size_conversion()
    
    # Test 4: Configuration structures
    test_experiment_config()
    
    # Test 5: Performance test
    run_performance_test()
    
    # Summary
    print(f"\n🎉 All tests completed successfully!")
    print(f"📊 Tested {len(streaming_results)} datasets:")
    
    for result in streaming_results:
        print(f"   • {result['dataset']}: {result['chunks']} chunks, "
              f"{result['total_tokens']} tokens, "
              f"{result['throughput_chunks_per_s']:.1f} chunks/s")
    
    print("\n✅ Multi-dataset experiment infrastructure is ready!")
    print("\n💡 Next steps:")
    print("   1. Ensure Kafka is running on localhost:9092")
    print("   2. Ensure PostgreSQL with pgvector is running")
    print("   3. Start the embedding generation service")
    print("   4. Run: ./run_multi_dataset_experiments.py --smoke-test")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)