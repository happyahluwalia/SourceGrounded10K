"""
Test RAG chain end-to-end.

Tests:
1. Basic Q&A
2. Filtered Q&A (specific company/section)
3. Comparative questions
4. No-answer scenarios
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_store import VectorStore
from app.services.rag_chain import RAGChain
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_response(response: dict):
    """Pretty print RAG response."""
    print("\n" + "="*80)
    print(f"QUERY: {response['query']}")
    print("="*80)
    print(f"\nANSWER:\n{response['answer']}")
    print(f"\n{'~'*80}")
    print(f"Sources used: {response['num_sources']}")
    print(f"Processing time: {response['processing_time']:.2f}s")
    
    if 'sources' in response and response['sources']:
        print(f"\nSOURCES:")
        for i, source in enumerate(response['sources'], 1):
            print(f"\n  [{i}] {source['ticker']} - {source['filing_type']} ({source['report_date']})")
            print(f"      Section: {source['section']} | Score: {source['score']:.3f}")
            print(f"      Preview: {source['text'][:150]}...")
    
    print("="*80)


def test_basic_qa():
    """Test basic question answering."""
    
    print("\n" + "#"*80)
    print("TEST 1: BASIC QUESTION ANSWERING")
    print("#"*80)
    
    # Initialize RAG chain
    vector_store = VectorStore()
    rag_chain = RAGChain(vector_store=vector_store)
    
    # Test queries
    queries = [
        "What were Apple's total revenues in 2024?",
        "What are the main risk factors for Apple?",
        "Who are Apple's executive officers?",
    ]
    
    for query in queries:
        response = rag_chain.answer(
            query=query,
            ticker="AAPL",  # Filter to Apple only
            top_k=3,
            score_threshold=0.5  # Lower threshold to catch more results
        )
        
        # Exit gracefully if LLM error occurs
        if response['answer'].startswith('Error:'):
            print("\n❌ LLM error detected. Please check:")
            print("   1. Ollama is running: ollama serve")
            print("   2. Model is available: ollama list")
            print(f"   3. Model name matches: {rag_chain.model_name}")
            print("\nExiting tests...")
            exit(1)
        
        print_response(response)


def test_comparative_qa():
    """Test comparative questions across companies."""
    
    print("\n\n" + "#"*80)
    print("TEST 2: COMPARATIVE ANALYSIS")
    print("#"*80)
    
    vector_store = VectorStore()
    rag_chain = RAGChain(vector_store=vector_store)
    
    # Ask same question for different companies
    query = "What were the company's total revenues?"
    
    companies = ["AAPL", "MSFT"]
    
    results = {}
    for ticker in companies:
        print(f"\n{'~'*80}")
        print(f"Asking about: {ticker}")
        print(f"{'~'*80}")
        
        response = rag_chain.answer(
            query=query,
            ticker=ticker,
            top_k=2,
            include_sources=False  # Don't clutter output
        )
        
        results[ticker] = response['answer']
        print(f"\n{response['answer']}")
    
    # Side-by-side comparison
    print("\n\n" + "="*80)
    print("SIDE-BY-SIDE COMPARISON")
    print("="*80)
    for ticker, answer in results.items():
        print(f"\n{ticker}:")
        print(answer)


def test_section_specific():
    """Test section-specific queries."""
    
    print("\n\n" + "#"*80)
    print("TEST 3: SECTION-SPECIFIC QUERIES")
    print("#"*80)
    
    vector_store = VectorStore()
    rag_chain = RAGChain(vector_store=vector_store)
    
    # Ask about risks (should pull from Item 1A)
    response = rag_chain.answer(
        query="What are the main business risks?",
        ticker="AAPL",
        section="Item 1A",  # Risk Factors section
        top_k=3
    )
    
    print_response(response)


def test_no_answer():
    """Test when no relevant info is found."""
    
    print("\n\n" + "#"*80)
    print("TEST 4: NO ANSWER SCENARIO")
    print("#"*80)
    
    vector_store = VectorStore()
    rag_chain = RAGChain(vector_store=vector_store)
    
    # Ask about something not in the filings
    response = rag_chain.answer(
        query="What is Apple's strategy for quantum computing?",
        ticker="AAPL",
        top_k=3,
        score_threshold=0.8  # High threshold
    )
    
    print_response(response)


if __name__ == "__main__":
    print("\nStarting RAG Chain Tests...")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    try:
        test_basic_qa()
        test_comparative_qa()
        test_section_specific()
        test_no_answer()
        
        print("\n✓ All tests completed!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(0)