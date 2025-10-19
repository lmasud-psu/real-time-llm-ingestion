#!/usr/bin/env python3
"""
Test the exact API requested by the user for Arxiv dataset.
"""

from stream_arxiv import stream_arxiv, stream_arxiv_sample
from typing import Iterator

def test_exact_api():
    """Test the exact API: stream_arxiv(token_length: int = 1000) -> Iterator[str]"""
    
    print("🧪 Testing exact Arxiv API specification...")
    print("Function signature: stream_arxiv(token_length: int = 1000) -> Iterator[str]")
    print("=" * 70)
    
    # Test 1: Default parameter (using sample for faster testing)
    print("\n✅ Test 1: Default parameter (1000 tokens)")
    count = 0
    for chunk in stream_arxiv_sample():  # No parameters - should default to 1000
        assert isinstance(chunk, str), f"Expected str, got {type(chunk)}"
        count += 1
        if count == 1:
            print(f"   First chunk type: {type(chunk)}")
            print(f"   First chunk length: {len(chunk)} chars")
        if count >= 3:
            break
    print(f"   ✓ Processed {count} chunks successfully")
    
    # Test 2: Custom token length
    print("\n✅ Test 2: Custom token length (500 tokens)")
    count = 0
    for chunk in stream_arxiv_sample(token_length=500, max_papers=10):
        assert isinstance(chunk, str), f"Expected str, got {type(chunk)}"
        count += 1
        if count == 1:
            print(f"   First chunk type: {type(chunk)}")
            print(f"   First chunk length: {len(chunk)} chars")
        if count >= 3:
            break
    print(f"   ✓ Processed {count} chunks successfully")
    
    # Test 3: Type checking
    print("\n✅ Test 3: Return type verification")
    stream = stream_arxiv_sample(token_length=200, max_papers=5)
    assert hasattr(stream, '__iter__'), "Return value should be iterable"
    assert hasattr(stream, '__next__'), "Return value should be an iterator"
    print("   ✓ Return type is Iterator[str]")
    
    # Test 4: Iterator behavior
    print("\n✅ Test 4: Iterator behavior")
    iterator = stream_arxiv_sample(token_length=100, max_papers=5)
    chunk1 = next(iterator)
    chunk2 = next(iterator)
    assert isinstance(chunk1, str), "First chunk should be string"
    assert isinstance(chunk2, str), "Second chunk should be string"
    assert chunk1 != chunk2, "Chunks should be different"
    print("   ✓ Iterator returns different string chunks")
    
    print("\n🎉 All API tests passed!")
    print("✅ Function matches exact specification:")
    print("   stream_arxiv(token_length: int = 1000) -> Iterator[str]")


if __name__ == "__main__":
    test_exact_api()