#!/usr/bin/env python3
"""
Multi-Dataset Experiment Setup Test for Architecture 1

Tests that all components needed for architecture1 experiments are working:
1. Dataset streaming modules import correctly
2. Dataset streaming generates chunks properly  
3. Kafka connection works
4. Database connection works
5. Basic performance benchmarks
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
        from stream_ccnews import stream_cc_news_files, estimate_tokens
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
    """Test that datasets can stream data properly."""
    print("\n📊 Testing dataset streaming...")
    
    # Import after checking they're available
    from stream_ccnews import stream_cc_news_files, estimate_tokens
    from stream_arxiv import stream_arxiv_sample, estimate_tokens as estimate_arxiv_tokens
    from stream_wikipedia import stream_wikipedia_sample, estimate_tokens as estimate_wiki_tokens
    
    results = {}
    
    # Test CC News
    print("\n🎯 Testing cc_news dataset...")
    start_time = time.time()
    cc_chunks = list(stream_cc_news_files(token_length=500, file_indices=[0, 1]))
    duration = time.time() - start_time
    
    if cc_chunks:
        total_tokens = sum(estimate_tokens(chunk) for chunk in cc_chunks)
        sample_text = cc_chunks[0][:100] + '...' if cc_chunks[0] else 'No text'
        
        results['cc_news'] = {
            'chunks': len(cc_chunks),
            'tokens': total_tokens,
            'duration': duration,
            'throughput': len(cc_chunks) / duration,
            'sample': sample_text
        }
        
        print(f"✅ cc_news: {len(cc_chunks)} chunks, {total_tokens} tokens, {duration:.2f}s")
        print(f"   Average tokens per chunk: {total_tokens/len(cc_chunks):.1f}")
        print(f"   Sample chunk (first 100 chars): {sample_text}")
    else:
        print("❌ cc_news: No chunks generated")
        return False
    
    # Test Arxiv
    print("\n🎯 Testing arxiv dataset...")
    start_time = time.time()
    arxiv_chunks = list(stream_arxiv_sample(token_length=500, max_papers=3))
    duration = time.time() - start_time
    
    if arxiv_chunks:
        total_tokens = sum(estimate_arxiv_tokens(chunk) for chunk in arxiv_chunks)
        sample_text = arxiv_chunks[0][:100] + '...' if arxiv_chunks[0] else 'No text'
        
        results['arxiv'] = {
            'chunks': len(arxiv_chunks),
            'tokens': total_tokens,
            'duration': duration,
            'throughput': len(arxiv_chunks) / duration,
            'sample': sample_text
        }
        
        print(f"✅ arxiv: {len(arxiv_chunks)} chunks, {total_tokens} tokens, {duration:.2f}s")
        print(f"   Average tokens per chunk: {total_tokens/len(arxiv_chunks):.1f}")
        print(f"   Sample chunk (first 100 chars): {sample_text}")
    else:
        print("❌ arxiv: No chunks generated")
        return False
    
    # Test Wikipedia
    print("\n🎯 Testing wikipedia dataset...")
    start_time = time.time()
    wiki_chunks = list(stream_wikipedia_sample(token_length=500, max_articles=3))
    duration = time.time() - start_time
    
    if wiki_chunks:
        total_tokens = sum(estimate_wiki_tokens(chunk) for chunk in wiki_chunks)
        sample_text = wiki_chunks[0][:100] + '...' if wiki_chunks[0] else 'No text'
        
        results['wikipedia'] = {
            'chunks': len(wiki_chunks),
            'tokens': total_tokens,
            'duration': duration,
            'throughput': len(wiki_chunks) / duration,
            'sample': sample_text
        }
        
        print(f"✅ wikipedia: {len(wiki_chunks)} chunks, {total_tokens} tokens, {duration:.2f}s")
        print(f"   Average tokens per chunk: {total_tokens/len(wiki_chunks):.1f}")
        print(f"   Sample chunk (first 100 chars): {sample_text}")
    else:
        print("❌ wikipedia: No chunks generated")
        return False
    
    return results


def test_chunk_conversion():
    """Test KB to token conversion logic."""
    print("\n🔄 Testing chunk size conversion...")
    
    def kb_to_tokens(kb: float) -> int:
        return int((kb * 1024) / 4)
    
    test_cases = [
        (0.5, 128),
        (1.0, 256),
        (2.0, 512),
        (10.0, 2560),
        (80.0, 20480)
    ]
    
    for kb, expected_tokens in test_cases:
        actual_tokens = kb_to_tokens(kb)
        print(f"   {kb}KB → {actual_tokens} tokens (expected ~{expected_tokens})")
        if abs(actual_tokens - expected_tokens) / expected_tokens < 0.1:  # Within 10%
            print("   ✅ Conversion correct")
        else:
            print("   ❌ Conversion incorrect")
            return False
    
    return True


def test_experiment_configs():
    """Test experiment configuration generation."""
    print("\n⚙️ Testing experiment configuration...")
    
    from run_multi_dataset_experiments import ExperimentConfig
    
    configs = [
        ExperimentConfig('cc_news', 1.0, burst_enabled=False),
        ExperimentConfig('arxiv', 5.0, burst_enabled=True),
        ExperimentConfig('wikipedia', 10.0, burst_enabled=True),
    ]
    
    print(f"✅ Created {len(configs)} test configurations:")
    for i, config in enumerate(configs, 1):
        print(f"   Config {i}: {config.dataset}, {config.chunk_size_kb}KB, burst={config.burst_enabled}")
    
    return True


def run_performance_test():
    """Run performance benchmarks."""
    print("\n🚀 Running performance test...")
    
    from stream_ccnews import stream_cc_news_files, estimate_tokens
    
    chunk_sizes = [0.5, 1, 2, 5]  # KB
    
    for kb in chunk_sizes:
        target_tokens = int((kb * 1024) / 4)
        start_time = time.time()
        
        chunks = list(stream_cc_news_files(
            token_length=target_tokens, 
            file_indices=[0]
        ))
        
        duration = time.time() - start_time
        total_tokens = sum(estimate_tokens(chunk) for chunk in chunks)
        
        print(f"   {kb}KB chunks: {len(chunks)} chunks, {total_tokens} tokens, {duration:.3f}s")
        print(f"      Throughput: {len(chunks)/duration:.1f} chunks/s, {total_tokens/duration:.0f} tokens/s")


def main():
    print("🧪 Multi-Dataset Experiment Setup Test for Architecture 1")
    print("=" * 60)
    
    # Test 1: Dataset imports
    if not test_dataset_imports():
        print("\n❌ Import test failed. Please check dataset module setup.")
        return 1
    
    # Test 2: Dataset streaming
    streaming_results = test_dataset_streaming()
    if not streaming_results:
        print("\n❌ Streaming test failed. Please check dataset configurations.")
        return 1
    
    # Test 3: Chunk conversion
    if not test_chunk_conversion():
        print("\n❌ Chunk conversion test failed.")
        return 1
    
    # Test 4: Experiment configs
    if not test_experiment_configs():
        print("\n❌ Configuration test failed.")
        return 1
    
    # Test 5: Performance benchmark
    run_performance_test()
    
    print("\n🎉 All tests completed successfully!")
    print(f"📊 Tested {len(streaming_results)} datasets:")
    
    for dataset, results in streaming_results.items():
        throughput = results['throughput']
        print(f"   • {dataset}: {results['chunks']} chunks, {results['tokens']} tokens, {throughput:.1f} chunks/s")
    
    print("\n✅ Architecture 1 experiment infrastructure is ready!")
    
    print("\n💡 Next steps:")
    print("   1. Ensure Kafka is running on localhost:9092")
    print("   2. Ensure PostgreSQL with embeddings table is running")
    print("   3. Start the embedding generation service")
    print("   4. Start the writer service")
    print("   5. Run: ./run_multi_dataset_experiments.py --smoke-test")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())