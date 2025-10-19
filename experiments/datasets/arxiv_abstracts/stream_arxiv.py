#!/usr/bin/env python3
"""
Arxiv Abstracts 2021 Dataset Streaming Module

Provides functionality to stream the Arxiv Abstracts 2021 dataset with configurable chunk sizes.
"""

import os
import gzip
import json
from typing import Iterator, Optional
import re


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text.
    Uses a simple approximation: ~4 characters per token (GPT-like tokenization).
    
    Args:
        text: Input text string
        
    Returns:
        Estimated number of tokens
    """
    return len(text) // 4


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove LaTeX-style escape characters that are common in academic papers
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)  # \command{text} -> text
    text = re.sub(r'\\([a-zA-Z])', r'\1', text)  # \a -> a
    
    return text.strip()


def chunk_text_by_tokens(text: str, max_tokens: int) -> Iterator[str]:
    """
    Split text into chunks based on estimated token count.
    
    Args:
        text: Input text to chunk
        max_tokens: Maximum tokens per chunk
        
    Yields:
        Text chunks with approximately max_tokens each
    """
    if not text or max_tokens <= 0:
        return
    
    words = text.split()
    current_chunk = []
    current_tokens = 0
    
    for word in words:
        word_tokens = estimate_tokens(word + " ")
        
        # If adding this word would exceed the limit, yield current chunk
        if current_tokens + word_tokens > max_tokens and current_chunk:
            yield " ".join(current_chunk)
            current_chunk = [word]
            current_tokens = word_tokens
        else:
            current_chunk.append(word)
            current_tokens += word_tokens
    
    # Yield the last chunk if it has content
    if current_chunk:
        yield " ".join(current_chunk)


def stream_arxiv(token_length: int = 1000) -> Iterator[str]:
    """
    Stream Arxiv Abstracts 2021 dataset with configurable chunk size.
    
    This function reads the JSONL.gz file and streams the text content 
    (both title and abstract) in chunks of approximately the specified token length.
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        
    Yields:
        str: Text chunks from the Arxiv dataset
        
    Raises:
        FileNotFoundError: If arxiv_data directory doesn't exist
        ValueError: If token_length is not positive
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "arxiv_data", "arxiv-abstracts.jsonl.gz")
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Arxiv data file not found: {data_file}")
    
    print(f"🚀 Streaming Arxiv Abstracts 2021 dataset...")
    print(f"📏 Target chunk size: {token_length} tokens")
    print(f"📖 Processing: {os.path.basename(data_file)}")
    
    total_chunks = 0
    total_papers = 0
    
    try:
        with gzip.open(data_file, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parse JSON record
                    record = json.loads(line.strip())
                    total_papers += 1
                    
                    # Extract title and abstract
                    title = record.get('title', '')
                    abstract = record.get('abstract', '')
                    
                    # Clean the text
                    title = clean_text(title)
                    abstract = clean_text(abstract)
                    
                    # Combine title and abstract with separator
                    if title and abstract:
                        full_text = f"{title}\n\n{abstract}"
                    elif title:
                        full_text = title
                    elif abstract:
                        full_text = abstract
                    else:
                        continue  # Skip empty records
                    
                    # Chunk the text and yield chunks
                    for chunk in chunk_text_by_tokens(full_text, token_length):
                        if chunk.strip():  # Only yield non-empty chunks
                            total_chunks += 1
                            yield chunk.strip()
                    
                    # Progress indication every 10k papers
                    if total_papers % 10000 == 0:
                        print(f"📄 Processed {total_papers:,} papers, generated {total_chunks:,} chunks so far...")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️  Warning: Invalid JSON on line {line_num}: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️  Warning: Error processing line {line_num}: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise
    
    print(f"✅ Streaming complete! Processed {total_papers:,} papers, generated {total_chunks:,} chunks total.")


def stream_arxiv_categories(token_length: int = 1000, categories: Optional[list] = None) -> Iterator[str]:
    """
    Stream Arxiv papers filtered by categories.
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        categories: List of categories to filter by (e.g., ['cs.AI', 'cs.LG']). If None, all categories.
        
    Yields:
        str: Text chunks from papers matching the specified categories
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "arxiv_data", "arxiv-abstracts.jsonl.gz")
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Arxiv data file not found: {data_file}")
    
    # Convert categories to set for faster lookup
    category_filter = set(categories) if categories else None
    
    print(f"🚀 Streaming Arxiv dataset with category filter...")
    print(f"📏 Target chunk size: {token_length} tokens")
    if category_filter:
        print(f"🏷️  Filtering categories: {sorted(category_filter)}")
    else:
        print(f"🏷️  Processing all categories")
    
    total_chunks = 0
    total_papers = 0
    filtered_papers = 0
    
    try:
        with gzip.open(data_file, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                    total_papers += 1
                    
                    # Check category filter
                    if category_filter:
                        paper_categories = record.get('categories', [])
                        if not any(cat in category_filter for cat in paper_categories):
                            continue
                    
                    filtered_papers += 1
                    
                    # Extract and process text
                    title = clean_text(record.get('title', ''))
                    abstract = clean_text(record.get('abstract', ''))
                    
                    if title and abstract:
                        full_text = f"{title}\n\n{abstract}"
                    elif title:
                        full_text = title
                    elif abstract:
                        full_text = abstract
                    else:
                        continue
                    
                    # Chunk and yield
                    for chunk in chunk_text_by_tokens(full_text, token_length):
                        if chunk.strip():
                            total_chunks += 1
                            yield chunk.strip()
                    
                    # Progress indication
                    if filtered_papers % 1000 == 0:
                        print(f"📄 Processed {total_papers:,} papers ({filtered_papers:,} matched filter), generated {total_chunks:,} chunks...")
                        
                except (json.JSONDecodeError, Exception) as e:
                    continue
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise
    
    print(f"✅ Streaming complete! Processed {total_papers:,} papers ({filtered_papers:,} matched), generated {total_chunks:,} chunks.")


def stream_arxiv_sample(token_length: int = 1000, max_papers: int = 1000) -> Iterator[str]:
    """
    Stream a sample of the Arxiv dataset (useful for testing).
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        max_papers: Maximum number of papers to process (default: 1000)
        
    Yields:
        str: Text chunks from the sampled papers
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    if max_papers <= 0:
        raise ValueError("max_papers must be positive")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "arxiv_data", "arxiv-abstracts.jsonl.gz")
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Arxiv data file not found: {data_file}")
    
    print(f"🚀 Streaming Arxiv sample ({max_papers:,} papers max)...")
    print(f"📏 Target chunk size: {token_length} tokens")
    
    total_chunks = 0
    papers_processed = 0
    
    try:
        with gzip.open(data_file, 'rt', encoding='utf-8') as f:
            for line in f:
                if papers_processed >= max_papers:
                    break
                
                try:
                    record = json.loads(line.strip())
                    papers_processed += 1
                    
                    title = clean_text(record.get('title', ''))
                    abstract = clean_text(record.get('abstract', ''))
                    
                    if title and abstract:
                        full_text = f"{title}\n\n{abstract}"
                    elif title:
                        full_text = title
                    elif abstract:
                        full_text = abstract
                    else:
                        continue
                    
                    for chunk in chunk_text_by_tokens(full_text, token_length):
                        if chunk.strip():
                            total_chunks += 1
                            yield chunk.strip()
                            
                except (json.JSONDecodeError, Exception):
                    continue
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise
    
    print(f"✅ Sample complete! Processed {papers_processed:,} papers, generated {total_chunks:,} chunks.")


if __name__ == "__main__":
    # Example usage
    print("🧪 Testing Arxiv streaming...")
    
    chunk_count = 0
    for chunk in stream_arxiv_sample(token_length=500, max_papers=10):
        chunk_count += 1
        if chunk_count <= 3:  # Show first 3 chunks
            print(f"\n--- Chunk {chunk_count} ---")
            print(f"Estimated tokens: {estimate_tokens(chunk)}")
            print(f"Text preview: {chunk[:200]}...")
        
        if chunk_count >= 10:  # Stop after 10 chunks for demo
            break
    
    print(f"\n🎯 Demo complete: Processed {chunk_count} chunks")