"""
Test semantic search functionality

This script demonstrates:
1. How embeddings capture semantic meaning
2. Similarity scores (cosine similarity 0-1)
3. How different queries retrieve different chunks

We are not testing keyword/metadata search of Qdrant yet
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_results(result: dict, rank: int):
    """Pretty print a search result."""
    print(f"\n{'='*80}")
    print(f"Rank {rank} | Score: {result['score']:.4f} (higher = more similar)")
    print(f"{'='*80}")
    print(f"Company: {result['ticker']}")
    print(f"Filing: {result['filing_type']} | Date: {result['report_date']}")
    print(f"Section: {result['section']}")
    print(f"\nText Preview:")
    print(f"{result['text'][:400]}...")
    print(f"{'='*80}")

def test_basic_search():
    """Test basic semantic search without filters"""

    vector_store = VectorStore()

    # Test queries with different semantic meanings
    test_queries = [
        "What were the company's total revenues?",
        "How much profit did the company make?",
        "What are the main risk factors?",
        "What are the company's top 3 competitors?",
        "Who are the executive officers?",
        "What is the compensation of the C Suite?",
    ]

    for query in test_queries:
        print(f"\n\n{'#'*80}")
        print(f"Query: {query}")
        print(f"{'#'*80}")

        # search without filters
        results = vector_store.search(
            query = query,
            limit =3   # top 3 results
        )

        if not results:
            print("No results found!")
            continue

        # Print results
        for i, result in enumerate(results, 1):
            print_results(result, i)
        
        # Explain what happened
        print(f"\n{'~'*80}")
        print("💡 What just happened:")
        print(f"   1. Your query was converted to a 1024-dim vector")
        print(f"   2. Qdrant compared it to all {len(results)} stored vectors")
        print(f"   3. Returned the {len(results)} most semantically similar chunks")
        print(f"   4. Scores show cosine similarity (1.0 = identical, 0.0 = unrelated)")
        print(f"{'~'*80}")

if __name__ == "__main__":
    test_basic_search()