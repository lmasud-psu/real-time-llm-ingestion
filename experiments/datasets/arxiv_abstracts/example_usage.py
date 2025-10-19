#!/usr/bin/env python3
"""
Example usage of Arxiv Abstracts 2021 streaming functionality.
"""

from stream_arxiv import stream_arxiv, stream_arxiv_categories, stream_arxiv_sample, estimate_tokens

def example_basic_streaming():
    """Basic example of streaming Arxiv with default chunk size."""
    print("📚 Example 1: Basic streaming with 1000 token chunks")
    print("=" * 60)
    
    chunk_count = 0
    total_tokens = 0
    
    # Stream only a sample for demo purposes
    for chunk in stream_arxiv_sample(token_length=1000, max_papers=100):
        chunk_count += 1
        chunk_tokens = estimate_tokens(chunk)
        total_tokens += chunk_tokens
        
        if chunk_count <= 2:  # Show first 2 chunks
            print(f"\n--- Chunk {chunk_count} ({chunk_tokens} tokens) ---")
            print(f"{chunk[:300]}...")
        
        if chunk_count >= 5:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Processed {chunk_count} chunks, ~{total_tokens} total tokens")


def example_category_filtering():
    """Example with category filtering."""
    print("\n📚 Example 2: Computer Science papers only")
    print("=" * 60)
    
    chunk_count = 0
    
    # Filter for computer science categories
    cs_categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.NE']
    
    for chunk in stream_arxiv_categories(token_length=800, categories=cs_categories):
        chunk_count += 1
        
        if chunk_count <= 2:  # Show first 2 chunks
            print(f"\n--- CS Chunk {chunk_count} ({estimate_tokens(chunk)} tokens) ---")
            print(f"{chunk[:200]}...")
        
        if chunk_count >= 5:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Processed {chunk_count} CS chunks")


def example_small_chunks():
    """Example with smaller chunk sizes."""
    print("\n📚 Example 3: Small chunks (300 tokens)")
    print("=" * 60)
    
    chunk_count = 0
    
    for chunk in stream_arxiv_sample(token_length=300, max_papers=20):
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
    
    for i, chunk in enumerate(stream_arxiv_sample(token_length=600, max_papers=30)):
        # Simulate some processing (e.g., cleaning, tokenization, etc.)
        processed_chunk = {
            'id': i,
            'text': chunk,
            'token_count': estimate_tokens(chunk),
            'word_count': len(chunk.split()),
            'char_count': len(chunk),
            'has_math': '$' in chunk or 'equation' in chunk.lower(),
            'domain': 'arxiv'
        }
        
        processed_chunks.append(processed_chunk)
        
        if i < 2:  # Show first 2 processed chunks
            print(f"\nProcessed chunk {i}:")
            print(f"  Tokens: {processed_chunk['token_count']}")
            print(f"  Words: {processed_chunk['word_count']}")
            print(f"  Has math: {processed_chunk['has_math']}")
            print(f"  Preview: {chunk[:100]}...")
        
        if i >= 4:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Pipeline processed {len(processed_chunks)} chunks")
    
    # Show summary statistics
    total_tokens = sum(chunk['token_count'] for chunk in processed_chunks)
    avg_tokens = total_tokens / len(processed_chunks)
    math_chunks = sum(1 for chunk in processed_chunks if chunk['has_math'])
    
    print(f"📈 Average tokens per chunk: {avg_tokens:.1f}")
    print(f"🔢 Chunks with math content: {math_chunks}/{len(processed_chunks)}")


def example_physics_papers():
    """Example focusing on physics papers."""
    print("\n📚 Example 5: Physics papers only")
    print("=" * 60)
    
    chunk_count = 0
    
    # Physics categories
    physics_categories = ['hep-ph', 'hep-th', 'astro-ph', 'cond-mat', 'quant-ph', 'nucl-th']
    
    for chunk in stream_arxiv_categories(token_length=700, categories=physics_categories):
        chunk_count += 1
        
        if chunk_count <= 2:  # Show first 2 chunks
            print(f"\n--- Physics Chunk {chunk_count} ({estimate_tokens(chunk)} tokens) ---")
            print(f"{chunk[:250]}...")
        
        if chunk_count >= 5:  # Stop after 5 chunks for demo
            break
    
    print(f"\n📊 Processed {chunk_count} physics chunks")


if __name__ == "__main__":
    print("🎬 Arxiv Abstracts 2021 Streaming Examples")
    print("=" * 80)
    
    try:
        example_basic_streaming()
        example_category_filtering()
        example_small_chunks()
        example_pipeline_integration()
        example_physics_papers()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you've downloaded the Arxiv dataset first with:")
        print("  ./download_arxiv_simple.sh")