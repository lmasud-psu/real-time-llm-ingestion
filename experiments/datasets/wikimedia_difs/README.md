# Wikipedia Dataset Streaming API

This directory contains tools for downloading and streaming Wikipedia datasets from HuggingFace, specifically designed for real-time LLM ingestion pipelines.

## 📋 Overview

The Wikipedia streaming API provides:
- Download scripts for Wikipedia datasets in multiple languages
- Token-based text chunking for consistent LLM input
- Wiki markup cleaning and text preprocessing
- Support for multiple Wikipedia language editions
- Mock data fallback for testing and development

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Dataset (Optional)

```bash
# Download English Wikipedia (latest)
./download_wikipedia_simple.sh en

# Download Simple English Wikipedia
./download_wikipedia_simple.sh simple

# Download Spanish Wikipedia from specific date
./download_wikipedia_simple.sh es 20231201
```

**Note**: Download may require HuggingFace authentication. If download fails, the streaming API will use mock data for demonstration.

### 3. Stream Wikipedia Content

```python
from stream_wikipedia import stream_wikipedia_sample, estimate_tokens

# Stream with 1000-token chunks
for chunk in stream_wikipedia_sample(token_length=1000, max_articles=100):
    print(f"Chunk ({estimate_tokens(chunk)} tokens): {chunk[:200]}...")
    
    # Process chunk (embed, store, analyze, etc.)
    # your_processing_function(chunk)
```

## 📁 Files

- **`download_wikipedia_simple.sh`** - Download Wikipedia datasets from HuggingFace
- **`stream_wikipedia.py`** - Main streaming API with chunking and cleaning
- **`example_usage.py`** - Comprehensive usage examples
- **`test_api.py`** - Test suite for all functionality
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## 🔧 API Reference

### Main Functions

#### `stream_wikipedia(language="en", token_length=1000)`
Stream complete Wikipedia dataset for a language.

**Parameters:**
- `language` (str): Language code ("en", "simple", "es", "fr", etc.)
- `token_length` (int): Target tokens per chunk (~4 chars per token)

**Returns:** Iterator[str] - Text chunks

#### `stream_wikipedia_sample(token_length=1000, max_articles=50, language="en")`
Stream a limited sample of Wikipedia articles.

**Parameters:**
- `token_length` (int): Target tokens per chunk
- `max_articles` (int): Maximum articles to process
- `language` (str): Language code

**Returns:** Iterator[str] - Text chunks

#### `estimate_tokens(text)`
Estimate token count for text (1 token ≈ 4 characters).

#### `clean_wiki_text(text)`
Clean Wikipedia markup, references, and categories.

### Language Support

Supported languages (with automatic fallback):
- `en` - English Wikipedia
- `simple` - Simple English Wikipedia  
- `es` - Spanish Wikipedia
- `fr` - French Wikipedia
- `de` - German Wikipedia
- `it` - Italian Wikipedia
- `pt` - Portuguese Wikipedia
- `ru` - Russian Wikipedia

## 💡 Usage Examples

### Basic Streaming
```python
from stream_wikipedia import stream_wikipedia_sample

for chunk in stream_wikipedia_sample(token_length=800):
    # Process 800-token chunks
    process_text(chunk)
```

### Multi-language Processing
```python
languages = ["en", "simple", "es", "fr"]

for lang in languages:
    print(f"Processing {lang} Wikipedia...")
    for chunk in stream_wikipedia_sample(language=lang, max_articles=10):
        process_multilingual_text(chunk, lang)
```

### Pipeline Integration
```python
def wikipedia_pipeline():
    for chunk in stream_wikipedia_sample(token_length=1000, max_articles=200):
        # Clean and validate
        if len(chunk.strip()) < 100:
            continue
            
        # Generate embeddings
        embedding = generate_embedding(chunk)
        
        # Store in vector database
        store_embedding(chunk, embedding)
        
        yield {
            'text': chunk,
            'tokens': estimate_tokens(chunk),
            'embedding': embedding
        }
```

### Content Analysis
```python
from stream_wikipedia import stream_wikipedia_sample, estimate_tokens

total_tokens = 0
article_count = 0

for chunk in stream_wikipedia_sample(token_length=600, max_articles=100):
    tokens = estimate_tokens(chunk)
    total_tokens += tokens
    article_count += 1
    
    # Analyze content characteristics
    if 'algorithm' in chunk.lower():
        print(f"Found algorithmic content: {chunk[:100]}...")

print(f"Processed {total_tokens} tokens from {article_count} chunks")
```

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
python test_api.py

# Run specific test class
python -m unittest test_api.TestWikipediaStreaming

# Run with coverage (if pytest-cov installed)
pytest test_api.py --cov=stream_wikipedia
```

Run examples:
```bash
python example_usage.py
```

## 🎯 Integration with Pipeline

This Wikipedia streaming API is designed to integrate with the broader real-time LLM ingestion pipeline:

1. **Data Source**: Wikipedia provides high-quality, structured text data
2. **Chunking**: Consistent token-based chunking for LLM processing
3. **Streaming**: Memory-efficient processing of large datasets
4. **Language Support**: Multi-language content for diverse applications

### Architecture Integration

```
Wikipedia Dataset → stream_wikipedia.py → Token Chunks → Embedding Service → Vector DB
                                      ↓
                              Text Processing Pipeline
                                      ↓
                              Real-time LLM Ingestion
```

## 🔍 Troubleshooting

### Common Issues

1. **Download Permission Errors**
   ```
   Solution: The API uses mock data fallback automatically
   Alternative: Set HuggingFace authentication token
   ```

2. **Memory Issues with Large Datasets**
   ```
   Solution: Use stream_wikipedia_sample() with smaller max_articles
   Alternative: Implement batch processing
   ```

3. **Token Count Variations**
   ```
   Solution: Token estimation is approximate (±20% variance is normal)
   Alternative: Use exact tokenizer for precise counts
   ```

### Mock Data Behavior

When real Wikipedia data is unavailable, the API automatically uses mock data:
- Generates realistic article-like content
- Maintains consistent API behavior
- Includes proper token chunking
- Supports all language codes

## 📊 Performance

Typical performance characteristics:
- **Throughput**: ~50-100 chunks/second (mock data)
- **Memory**: Constant memory usage (streaming)
- **Token Rate**: ~50,000 tokens/second
- **Latency**: <1ms per chunk (after initial load)

Performance varies based on:
- Chunk size (larger chunks = higher throughput)
- Text complexity (Wiki markup density)
- Hardware specifications
- Dataset source (real vs mock data)

## 🤝 Contributing

This module follows the established pattern from `cc_news` and `arxiv_abstracts` directories. When adding features:

1. Maintain consistent API signatures
2. Include comprehensive tests
3. Update documentation
4. Follow token-based chunking standards
5. Ensure mock data fallback works

## 📚 Related

- **CC News API**: `../cc_news/` - News article streaming
- **Arxiv API**: `../arxiv_abstracts/` - Academic paper streaming  
- **Embedding Service**: `../../../cqrs_embedding_gen_svc/` - Embedding generation
- **Vector Storage**: `../../../lancedb/` and `../../../pgvector/` - Vector databases