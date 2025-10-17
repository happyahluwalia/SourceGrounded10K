"""
Test filtered semantic search

Demonstrates:
1. Metadata filtering (ticker, section, filing_type)
2. How filtering improves precesion
3. Performance comparison (filtered vs unfiltered)

"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_store import VectorStore
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_filtered_search():
    """
        Test search with metadata filters
    """

    vector_store = VectorStore()

    query = "What were the total revenues?"

    print(f"\n{'#'*80}")
    print(f"QUERY: {query}")
    print(f"{'#'*80}\n")
    
    # Test 1: No filters (search all companies)
    print("="*80)
    print("TEST 1: Unfiltered Search (all companies)")
    print("="*80)
    
    start = time.time()
    results_unfiltered = vector_store.search(
        query = query,
        limit =5
    )
    time_unfiltered = time.time() - start

    print(f"\nFound {len(results_unfiltered)} results in {time_unfiltered*1000:.2f}ms")
    print("\nTop 3 results:")
    for i, result in enumerate(results_unfiltered[:3], 1):
        print(f"  {i}. {result['ticker']} | {result['section']} | Score: {result['score']:.4f}")
        print(f"     {result['text'][:100]}...")
    
    # Test 2: Filter by ticker (Apple only)
    print("\n" + "="*80)
    print("TEST 2: Filtered by Ticker (AAPL only)")
    print("="*80)
    
    start = time.time()
    results_ticker = vector_store.search(
        query = query, 
        ticker="AAPL",
        limit = 5
    )
    time_ticker = time.time() - start
    
    print(f"\nFound {len(results_ticker)} results in {time_ticker*1000:.2f}ms")
    print("\nTop 3 results:")
    for i, result in enumerate(results_ticker[:3], 1):
        print(f"  {i}. {result['ticker']} | {result['section']} | Score: {result['score']:.4f}")
        print(f"     {result['text'][:100]}...")
    
    # Test 3 Filter by ticker + section
    print("\n" + "="*80)
    print("TEST 3: Filtered by Ticker + Section (AAPL + Item 7)")
    print("="*80)
    
    start = time.time()
    results_section = vector_store.search(
        query=query,
        ticker="AAPL",
        section="IteM 7",
        limit=5
    )
    time_section = time.time() - start
    
    print(f"\nFound {len(results_section)} results in {time_section*1000:.2f}ms")
    print("\nTop 3 results:")
    for i, result in enumerate(results_section[:3], 1):
        print(f"  {i}. {result['ticker']} | {result['section']} | Score: {result['score']:.4f}")
        print(f"     {result['text'][:100]}...")
    
    # Test 4: Filter by ticker + filing type
    print("\n" + "="*80)
    print("TEST 4: Filtered by Ticker + Filing Type (AAPL + 10-K)")
    print("="*80)
    
    start = time.time()
    results_filing = vector_store.search(
        query=query,
        ticker="AAPL",
        filing_type="10-K",
        limit=5
    )
    time_filing = time.time() - start
    
    print(f"\nFound {len(results_filing)} results in {time_filing*1000:.2f}ms")
    print("\nTop 3 results:")
    for i, result in enumerate(results_filing[:3], 1):
        print(f"  {i}. {result['ticker']} | {result['section']} | Score: {result['score']:.4f}")
        print(f"     {result['text'][:100]}...")
    
    # Performance comparison
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"Unfiltered:           {time_unfiltered*1000:.2f}ms")
    print(f"Ticker filter:        {time_ticker*1000:.2f}ms")
    print(f"Ticker + Section:     {time_section*1000:.2f}ms")
    print(f"Ticker + Filing Type: {time_filing*1000:.2f}ms")
    
    print("\n💡 Key Insights:")
    print("   - Filtering happens BEFORE vector search (very fast)")
    print("   - More specific filters = higher quality results")
    print("   - Speed difference minimal with small dataset")
    print("   - With 1M+ chunks, filters provide massive speedup")


def test_comparison_queries():
    """Test how filtering helps with comparative queries."""
    
    vector_store = VectorStore()
    
    print("\n\n" + "#"*80)
    print("COMPARATIVE QUERY TEST")
    print("#"*80)
    
    query = "How did iPhone sales perform?"
    
    # Get results for Apple
    print("\n" + "="*80)
    print(f"Apple's Answer to: {query}")
    print("="*80)
    
    apple_results = vector_store.search(
        query=query,
        ticker="AAPL",
        limit=2
    )
    
    for result in apple_results:
        print(f"\nScore: {result['score']:.4f}")
        print(f"{result['text'][:300]}...")
    
    # Get results for Microsoft
    print("\n" + "="*80)
    print(f"Microsoft's Answer to: {query}")
    print("="*80)
    
    msft_results = vector_store.search(
        query=query,
        ticker="MSFT",
        limit=2
    )
    
    for result in msft_results:
        print(f"\nScore: {result['score']:.4f}")
        print(f"{result['text'][:300]}...")
    
    print("\n💡 This enables comparative analysis:")
    print("   - Same query, different company filters")
    print("   - Build side-by-side comparisons")
    print("   - Track metrics across competitors")


if __name__ == "__main__":
    test_filtered_search()
    print("\n\n")
    test_comparison_queries()