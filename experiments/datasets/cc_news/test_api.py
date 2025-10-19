#!/usr/bin/env python3
"""
Test the exact API requested by the user.
"""

from stream_ccnews import stream_cc_news
from typing import Iterator

def test_exact_api():
    """Test the exact API: stream_cc_news(token_length: int = 1000) -> Iterator[str]"""
    
    print("🧪 Testing exact API specification...")
    print("Function signature: stream_cc_news(token_length: int = 1000) -> Iterator[str]")
    print("=" * 70)
    
    # Test 1: Default parameter
    print("\n✅ Test 1: Default parameter (1000 tokens)")
    count = 0
    for chunk in stream_cc_news():  # No parameters - should default to 1000
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
    for chunk in stream_cc_news(token_length=500):
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
    stream = stream_cc_news(token_length=200)
    assert hasattr(stream, '__iter__'), "Return value should be iterable"
    assert hasattr(stream, '__next__'), "Return value should be an iterator"
    print("   ✓ Return type is Iterator[str]")
    
    # Test 4: Iterator behavior
    print("\n✅ Test 4: Iterator behavior")
    iterator = stream_cc_news(token_length=100)
    chunk1 = next(iterator)
    chunk2 = next(iterator)
    assert isinstance(chunk1, str), "First chunk should be string"
    assert isinstance(chunk2, str), "Second chunk should be string"
    assert chunk1 != chunk2, "Chunks should be different"
    print("   ✓ Iterator returns different string chunks")
    
    print("\n🎉 All API tests passed!")
    print("✅ Function matches exact specification:")
    print("   stream_cc_news(token_length: int = 1000) -> Iterator[str]")


if __name__ == "__main__":
    test_exact_api()