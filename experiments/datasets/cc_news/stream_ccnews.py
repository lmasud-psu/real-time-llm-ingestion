#!/usr/bin/env python3
"""
CC News Dataset Streaming Module

Provides functionality to stream the CC News dataset with configurable chunk sizes.
"""

import os
import glob
from typing import Iterator, Optional
import pandas as pd
import pyarrow.parquet as pq


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


def stream_cc_news(token_length: int = 1000) -> Iterator[str]:
    """
    Stream CC News dataset with configurable chunk size.
    
    This function reads all parquet files in the ccnews_data/pair/ directory
    and streams the text content (both title and article) in chunks of 
    approximately the specified token length.
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        
    Yields:
        str: Text chunks from the CC News dataset
        
    Raises:
        FileNotFoundError: If ccnews_data directory doesn't exist
        ValueError: If token_length is not positive
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "ccnews_data", "pair")
    
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"CC News data directory not found: {data_dir}")
    
    # Find all parquet files
    parquet_files = glob.glob(os.path.join(data_dir, "*.parquet"))
    parquet_files.sort()  # Process files in consistent order
    
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
    
    print(f"🚀 Streaming CC News dataset from {len(parquet_files)} files...")
    print(f"📏 Target chunk size: {token_length} tokens")
    
    total_chunks = 0
    
    for file_path in parquet_files:
        file_name = os.path.basename(file_path)
        print(f"📖 Processing: {file_name}")
        
        # Read parquet file
        table = pq.read_table(file_path)
        df = table.to_pandas()
        
        # Process each row
        for idx, row in df.iterrows():
            title = str(row.get('title', ''))
            article = str(row.get('article', ''))
            
            # Combine title and article with separator
            if title and article:
                full_text = f"{title}\n\n{article}"
            elif title:
                full_text = title
            elif article:
                full_text = article
            else:
                continue  # Skip empty rows
            
            # Chunk the text and yield chunks
            for chunk in chunk_text_by_tokens(full_text, token_length):
                if chunk.strip():  # Only yield non-empty chunks
                    total_chunks += 1
                    yield chunk.strip()
    
    print(f"✅ Streaming complete! Generated {total_chunks} chunks total.")


def stream_cc_news_files(token_length: int = 1000, file_indices: Optional[list] = None) -> Iterator[str]:
    """
    Stream specific CC News files by index.
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        file_indices: List of file indices to process (0-3). If None, processes all files.
        
    Yields:
        str: Text chunks from the specified CC News files
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "ccnews_data", "pair")
    
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"CC News data directory not found: {data_dir}")
    
    # Get all parquet files sorted
    parquet_files = sorted(glob.glob(os.path.join(data_dir, "*.parquet")))
    
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
    
    # Filter by indices if specified
    if file_indices is not None:
        selected_files = []
        for idx in file_indices:
            if 0 <= idx < len(parquet_files):
                selected_files.append(parquet_files[idx])
            else:
                print(f"⚠️  Warning: File index {idx} out of range (0-{len(parquet_files)-1})")
        parquet_files = selected_files
    
    if not parquet_files:
        print("❌ No valid files to process")
        return
    
    print(f"🚀 Streaming from {len(parquet_files)} selected files...")
    print(f"📏 Target chunk size: {token_length} tokens")
    
    total_chunks = 0
    
    for file_path in parquet_files:
        file_name = os.path.basename(file_path)
        print(f"📖 Processing: {file_name}")
        
        # Read parquet file
        table = pq.read_table(file_path)
        df = table.to_pandas()
        
        # Process each row
        for idx, row in df.iterrows():
            title = str(row.get('title', ''))
            article = str(row.get('article', ''))
            
            # Combine title and article with separator
            if title and article:
                full_text = f"{title}\n\n{article}"
            elif title:
                full_text = title
            elif article:
                full_text = article
            else:
                continue  # Skip empty rows
            
            # Chunk the text and yield chunks
            for chunk in chunk_text_by_tokens(full_text, token_length):
                if chunk.strip():  # Only yield non-empty chunks
                    total_chunks += 1
                    yield chunk.strip()
    
    print(f"✅ Streaming complete! Generated {total_chunks} chunks total.")


if __name__ == "__main__":
    # Example usage
    print("🧪 Testing CC News streaming...")
    
    chunk_count = 0
    for chunk in stream_cc_news(token_length=500):
        chunk_count += 1
        if chunk_count <= 3:  # Show first 3 chunks
            print(f"\n--- Chunk {chunk_count} ---")
            print(f"Estimated tokens: {estimate_tokens(chunk)}")
            print(f"Text preview: {chunk[:200]}...")
        
        if chunk_count >= 10:  # Stop after 10 chunks for demo
            break
    
    print(f"\n🎯 Demo complete: Processed {chunk_count} chunks")