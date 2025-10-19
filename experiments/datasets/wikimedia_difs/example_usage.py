#!/usr/bin/env python3
"""
Example usage of Wikipedia streaming functionality.
"""

from stream_wikipedia import stream_wikipedia, stream_wikipedia_sample, estimate_tokens

def example_basic_streaming():
    """Basic example of streaming Wikipedia with default chunk size."""
    print("📚 Example 1: Basic streaming with 1000 token chunks")
    print("=" * 60)
    
    chunk_count = 0
    total_tokens = 0
    
    # Stream only a sample for demo purposes
    for chunk in stream_wikipedia_sample(token_length=1000, max_articles=50):
        chunk_count += 1
        chunk_tokens = estimate_tokens(chunk)
        total_tokens += chunk_tokens
        
        if chunk_count <= 2:  # Show first 2 chunks
            print(f"\n--- Chunk {chunk_count} ({chunk_tokens} tokens) ---")
            print(f"{chunk[:300]}...")
        
        if chunk_count >= 5:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Processed {chunk_count} chunks, ~{total_tokens} total tokens")


def example_language_variants():
    """Example with different Wikipedia language variants."""
    print("\n📚 Example 2: Different language variants")
    print("=" * 60)
    
    languages = ["en", "simple", "es", "fr"]
    
    for lang in languages:
        print(f"\n🏷️  Testing language: {lang}")
        chunk_count = 0
        
        for chunk in stream_wikipedia_sample(token_length=600, max_articles=3, language=lang):
            chunk_count += 1
            if chunk_count == 1:  # Show first chunk for each language
                print(f"   Sample text: {chunk[:150]}...")
            if chunk_count >= 3:  # Limit for demo
                break
        
        print(f"   Generated {chunk_count} chunks")


def example_small_chunks():
    """Example with smaller chunk sizes."""
    print("\n📚 Example 3: Small chunks (300 tokens)")
    print("=" * 60)
    
    chunk_count = 0
    
    for chunk in stream_wikipedia_sample(token_length=300, max_articles=10):
        chunk_count += 1
        
        if chunk_count <= 3:  # Show first 3 chunks
            print(f"\n--- Small Chunk {chunk_count} ({estimate_tokens(chunk)} tokens) ---")
            print(f"{chunk[:150]}...")
        
        if chunk_count >= 8:  # Stop after 8 chunks for demo
            break
    
    print(f"\n📊 Processed {chunk_count} small chunks")


def example_pipeline_integration():
    """Example showing how to integrate with data processing pipeline."""
    print("\n📚 Example 4: Pipeline integration")
    print("=" * 60)
    
    # Simulate processing pipeline
    processed_chunks = []
    
    for i, chunk in enumerate(stream_wikipedia_sample(token_length=700, max_articles=20)):
        # Simulate some processing (e.g., cleaning, entity extraction, etc.)
        processed_chunk = {
            'id': i,
            'text': chunk,
            'token_count': estimate_tokens(chunk),
            'word_count': len(chunk.split()),
            'char_count': len(chunk),
            'has_links': 'http' in chunk.lower() or 'www' in chunk.lower(),
            'is_technical': any(term in chunk.lower() for term in ['algorithm', 'network', 'system', 'computer']),
            'source': 'wikipedia'
        }
        
        processed_chunks.append(processed_chunk)
        
        if i < 2:  # Show first 2 processed chunks
            print(f"\nProcessed chunk {i}:")
            print(f"  Tokens: {processed_chunk['token_count']}")
            print(f"  Words: {processed_chunk['word_count']}")
            print(f"  Technical: {processed_chunk['is_technical']}")
            print(f"  Preview: {chunk[:100]}...")
        
        if i >= 4:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Pipeline processed {len(processed_chunks)} chunks")
    
    # Show summary statistics
    total_tokens = sum(chunk['token_count'] for chunk in processed_chunks)
    avg_tokens = total_tokens / len(processed_chunks)
    technical_chunks = sum(1 for chunk in processed_chunks if chunk['is_technical'])
    
    print(f"📈 Average tokens per chunk: {avg_tokens:.1f}")
    print(f"🔬 Technical chunks: {technical_chunks}/{len(processed_chunks)}")


def example_content_analysis():
    """Example analyzing Wikipedia content characteristics."""
    print("\n📚 Example 5: Content analysis")
    print("=" * 60)
    
    chunk_count = 0
    total_length = 0
    title_chunks = 0
    
    for chunk in stream_wikipedia_sample(token_length=800, max_articles=15):
        chunk_count += 1
        total_length += len(chunk)
        
        # Simple heuristic: if chunk starts with a title-like pattern
        lines = chunk.split('\n')
        if len(lines) > 0 and len(lines[0]) < 100 and not lines[0].endswith('.'):
            title_chunks += 1
        
        if chunk_count <= 2:  # Show analysis for first 2 chunks
            print(f"\n--- Analysis Chunk {chunk_count} ---")
            print(f"  Length: {len(chunk)} chars")
            print(f"  Tokens: {estimate_tokens(chunk)}")
            print(f"  Lines: {len(lines)}")
            print(f"  Preview: {chunk[:200]}...")
        
        if chunk_count >= 10:  # Stop after 10 chunks for demo
            break
    
    print(f"\n📊 Content Analysis Results:")
    print(f"   Total chunks: {chunk_count}")
    print(f"   Average length: {total_length // chunk_count if chunk_count > 0 else 0} chars")
    print(f"   Chunks with titles: {title_chunks}")


if __name__ == "__main__":
    print("🎬 Wikipedia Streaming Examples")
    print("=" * 80)
    
    try:
        example_basic_streaming()
        example_language_variants()
        example_small_chunks()
        example_pipeline_integration()
        example_content_analysis()
        
        print("\n🎉 All examples completed successfully!")
        print("\n💡 Note: Examples use mock data for demonstration.")
        print("   For real Wikipedia data, run the download script first:")
        print("   ./download_wikipedia_simple.sh [language] [date]")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you've set up the environment properly.")