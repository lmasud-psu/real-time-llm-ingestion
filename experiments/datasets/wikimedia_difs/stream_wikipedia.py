#!/usr/bin/env python3
"""
Wikipedia Dataset Streaming Module (Wikimedia)

Provides functionality to stream the Wikipedia dataset with configurable chunk sizes.
"""

import os
import json
from typing import Iterator, Optional, Dict, Any
from datasets import load_dataset
import re


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.
    Uses a simple heuristic: 1 token ≈ 4 characters.
    
    Args:
        text: Input text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def get_language_code(language: str) -> str:
    """
    Convert language name or code to standardized language code.
    
    Args:
        language: Language name or code
        
    Returns:
        Standardized language code (fallback to 'en' if unknown)
    """
    language = language.lower().strip()
    
    # Language code mappings
    language_map = {
        'en': 'en',
        'english': 'en',
        'simple': 'simple',
        'es': 'es',
        'spanish': 'es',
        'fr': 'fr',
        'french': 'fr',
        'de': 'de',
        'german': 'de',
        'it': 'it',
        'italian': 'it',
        'pt': 'pt',
        'portuguese': 'pt',
        'ru': 'ru',
        'russian': 'ru',
        'ja': 'ja',
        'japanese': 'ja',
        'zh': 'zh',
        'chinese': 'zh',
    }
    
    return language_map.get(language, 'en')  # Default to English


def clean_wikipedia_text(text: str) -> str:
    """
    Clean and normalize Wikipedia text content.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove Wikipedia-specific markup that might remain
    text = re.sub(r'\{\{[^}]*\}\}', '', text)  # Remove templates
    text = re.sub(r'\[\[([^|\]]*\|)?([^\]]*)\]\]', r'\2', text)  # Remove wiki links, keep text
    text = re.sub(r'\[http[^\s\]]*\s*([^\]]*)\]', r'\1', text)  # Remove external links, keep text
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)  # Remove comments
    
    # Clean up leftover markup
    text = re.sub(r'[\']{2,}', '', text)  # Remove wiki bold/italic markup
    text = re.sub(r'^\s*=+\s*(.+?)\s*=+\s*$', r'\1', text, flags=re.MULTILINE)  # Clean headers
    
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
    
    # Try to split by paragraphs first (double newline)
    paragraphs = text.split('\n\n')
    
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        paragraph_tokens = estimate_tokens(paragraph + " ")
        
        # If this paragraph would exceed the limit, yield current chunk and start new one
        if current_tokens + paragraph_tokens > max_tokens and current_chunk:
            yield " ".join(current_chunk)
            current_chunk = [paragraph]
            current_tokens = paragraph_tokens
        else:
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
    
    # Yield the last chunk if it has content
    if current_chunk:
        yield " ".join(current_chunk)


def stream_wikipedia(token_length: int = 1000, language: str = "en", date: str = "20231101") -> Iterator[str]:
    """
    Stream Wikipedia dataset with configurable chunk size.
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        language: Wikipedia language code (default: "en")
        date: Dataset date (default: "20231101")
        
    Yields:
        str: Text chunks from the Wikipedia dataset
        
    Raises:
        FileNotFoundError: If dataset subset doesn't exist
        ValueError: If token_length is not positive
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subset_name = f"{date}.{language}"
    data_path = os.path.join(script_dir, "wikipedia_data", subset_name)
    
    print(f"🚀 Streaming Wikipedia dataset...")
    print(f"📏 Target chunk size: {token_length} tokens")
    print(f"🏷️  Language: {language}")
    print(f"📅 Date: {date}")
    print(f"📖 Processing: {subset_name}")
    
    total_chunks = 0
    total_articles = 0
    
    try:
        # Check if local dataset exists
        if os.path.exists(data_path):
            print(f"📁 Loading from local cache: {data_path}")
            from datasets import load_from_disk
            dataset = load_from_disk(data_path)
        else:
            print(f"🌐 Downloading from HuggingFace...")
            # Set custom cache directory to avoid permission issues
            cache_dir = os.path.join(script_dir, '.cache')
            os.makedirs(cache_dir, exist_ok=True)
            os.environ['HF_HOME'] = cache_dir
            
            dataset = load_dataset(
                'wikimedia/wikipedia', 
                subset_name, 
                split='train',
                cache_dir=cache_dir
            )
            
            # Save for future use
            os.makedirs(os.path.dirname(data_path), exist_ok=True)
            dataset.save_to_disk(data_path)
            
        print(f"📊 Total articles available: {len(dataset):,}")
        
        for article in dataset:
            total_articles += 1
            
            # Extract title and text
            title = article.get('title', '').strip()
            text = article.get('text', '').strip()
            
            # Clean the text
            title = clean_wikipedia_text(title)
            text = clean_wikipedia_text(text)
            
            # Combine title and text with separator
            if title and text:
                full_text = f"{title}\n\n{text}"
            elif title:
                full_text = title
            elif text:
                full_text = text
            else:
                continue  # Skip empty articles
            
            # Chunk the text and yield chunks
            for chunk in chunk_text_by_tokens(full_text, token_length):
                if chunk.strip():  # Only yield non-empty chunks
                    total_chunks += 1
                    yield chunk.strip()
            
            # Progress indication every 1k articles
            if total_articles % 1000 == 0:
                print(f"📄 Processed {total_articles:,} articles, generated {total_chunks:,} chunks so far...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure the language code '{language}' and date '{date}' are valid.")
        print("   Check: https://huggingface.co/datasets/wikimedia/wikipedia")
        raise
    
    print(f"✅ Streaming complete! Processed {total_articles:,} articles, generated {total_chunks:,} chunks total.")


def stream_wikipedia_sample(token_length: int = 1000, max_articles: int = 100, language: str = "en", date: str = "20231101") -> Iterator[str]:
    """
    Stream a sample of the Wikipedia dataset (useful for testing).
    
    Args:
        token_length: Target number of tokens per chunk (default: 1000)
        max_articles: Maximum number of articles to process (default: 100)
        language: Wikipedia language code (default: "en")
        date: Dataset date (default: "20231101")
        
    Yields:
        str: Text chunks from the sampled articles
    """
    if token_length <= 0:
        raise ValueError("token_length must be positive")
    if max_articles <= 0:
        raise ValueError("max_articles must be positive")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subset_name = f"{date}.{language}"
    data_path = os.path.join(script_dir, "wikipedia_data", subset_name)
    
    print(f"🚀 Streaming Wikipedia sample ({max_articles:,} articles max)...")
    print(f"📏 Target chunk size: {token_length} tokens")
    print(f"🏷️  Language: {language}")
    
    total_chunks = 0
    articles_processed = 0
    
    try:
        # Check if local dataset exists
        if os.path.exists(data_path):
            from datasets import load_from_disk
            dataset = load_from_disk(data_path)
        else:
            # For sample, we might create some mock data if the real dataset isn't available
            print("⚠️  Local dataset not found. Creating mock sample data...")
            yield from _create_mock_wikipedia_sample(token_length, max_articles, language)
            return
        
        for article in dataset:
            if articles_processed >= max_articles:
                break
            
            articles_processed += 1
            
            title = clean_wikipedia_text(article.get('title', ''))
            text = clean_wikipedia_text(article.get('text', ''))
            
            if title and text:
                full_text = f"{title}\n\n{text}"
            elif title:
                full_text = title
            elif text:
                full_text = text
            else:
                continue
            
            for chunk in chunk_text_by_tokens(full_text, token_length):
                if chunk.strip():
                    total_chunks += 1
                    yield chunk.strip()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        # Fall back to mock data for demo purposes
        print("🔄 Falling back to mock sample data...")
        yield from _create_mock_wikipedia_sample(token_length, max_articles, language)
        return
    
    print(f"✅ Sample complete! Processed {articles_processed:,} articles, generated {total_chunks:,} chunks.")


def _create_mock_wikipedia_sample(token_length: int, max_articles: int, language: str) -> Iterator[str]:
    """Create mock Wikipedia data for demonstration when real data isn't available."""
    
    mock_articles = [
        {
            "title": "Artificial Intelligence",
            "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of \"intelligent agents\": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term \"artificial intelligence\" is often used to describe machines that mimic \"cognitive\" functions that humans associate with the human mind, such as \"learning\" and \"problem solving\". The field of AI research was born at a workshop at Dartmouth College in 1956, where the term \"artificial intelligence\" was coined. The field went through multiple cycles of optimism, followed by disappointment and the loss of funding, followed by new approaches, success and renewed funding."
        },
        {
            "title": "Machine Learning", 
            "text": "Machine learning (ML) is the study of computer algorithms that improve automatically through experience and by the use of data. It is seen as a part of artificial intelligence. Machine learning algorithms build a model based on sample data, known as training data, in order to make predictions or decisions without being explicitly programmed to do so. Machine learning algorithms are used in a wide variety of applications, such as in medicine, email filtering, speech recognition, and computer vision, where it is difficult or unfeasible to develop conventional algorithms to perform the needed tasks. Machine learning is closely related to computational statistics, which focuses on making predictions using computers. The study of mathematical optimization delivers methods, theory and application domains to the field of machine learning."
        },
        {
            "title": "Deep Learning",
            "text": "Deep learning (also known as deep structured learning) is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised. Deep learning architectures such as deep neural networks, deep belief networks, recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, speech recognition, natural language processing, machine translation, bioinformatics, drug design, medical image analysis, material inspection and board game programs, where they have produced results comparable to and in some cases surpassing human expert performance. The term deep learning was introduced to the machine learning community by Rina Dechter in 1986, and to artificial neural networks by Igor Aizenberg and colleagues in 2000."
        },
        {
            "title": "Neural Networks",
            "text": "A neural network is a computing system vaguely inspired by the biological neural networks that constitute animal brains. Such systems \"learn\" to perform tasks by considering examples, generally without being programmed with task-specific rules. For example, in image recognition, they might learn to identify images that contain cats by analyzing example images that have been manually labeled as \"cat\" or \"no cat\" and using the results to identify cats in other images. They do this without any prior knowledge of cats, for example, that they have fur, tails, whiskers and cat-like faces. Instead, they automatically generate identifying characteristics from the examples that they process. An artificial neural network is an interconnected group of nodes, inspired by a simplification of neurons in a brain."
        },
        {
            "title": "Natural Language Processing",
            "text": "Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data. The result is a computer capable of \"understanding\" the contents of documents, including the contextual nuances of the language within them. The technology can then accurately extract information and insights contained in the documents as well as categorize and organize the documents themselves. Challenges in natural language processing frequently involve speech recognition, natural language understanding, and natural language generation. The history of natural language processing generally started in the 1950s, although work can be found from earlier periods."
        }
    ]
    
    total_chunks = 0
    articles_processed = 0
    
    print(f"📄 Using mock Wikipedia articles for demonstration...")
    
    for i, article in enumerate(mock_articles):
        if articles_processed >= max_articles:
            break
            
        articles_processed += 1
        title = article["title"]
        text = article["text"]
        full_text = f"{title}\n\n{text}"
        
        for chunk in chunk_text_by_tokens(full_text, token_length):
            if chunk.strip():
                total_chunks += 1
                yield chunk.strip()
    
    print(f"✅ Mock sample complete! Generated {total_chunks} chunks from {articles_processed} mock articles.")


if __name__ == "__main__":
    # Example usage
    print("🧪 Testing Wikipedia streaming...")
    
    chunk_count = 0
    for chunk in stream_wikipedia_sample(token_length=500, max_articles=5, language="simple"):
        chunk_count += 1
        if chunk_count <= 3:  # Show first 3 chunks
            print(f"\n--- Chunk {chunk_count} ---")
            print(f"Estimated tokens: {estimate_tokens(chunk)}")
            print(f"Text preview: {chunk[:200]}...")
        
        if chunk_count >= 10:  # Stop after 10 chunks for demo
            break
    
    print(f"\n🎯 Demo complete: Processed {chunk_count} chunks")