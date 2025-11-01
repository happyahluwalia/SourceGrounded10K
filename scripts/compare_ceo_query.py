#!/usr/bin/env python3
"""
Compare RAG Chain vs Orchestrator for CEO query
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from app.services.vector_store import VectorStore
from app.services.storage import DatabaseStorage
from app.tools.rag_search_service import RAGSearchTool
from app.tools.data_prep_service import DataPrepTool
from app.agents.orchestrator import FinanceOrchestrator
from app.tools.finance_tool import initialize_tools

query = "Who is the Chief Executive officer of Robinhood?"

print("\n" + "#"*80)
print(f"QUERY: {query}")
print("#"*80)

# ============================================================================
# TEST 1: Direct RAG Chain
# ============================================================================
print("\n" + "="*80)
print("APPROACH 1: Direct RAG Chain")
print("="*80)

vector_store = VectorStore()
db_storage = DatabaseStorage()
data_prep = DataPrepTool(db_storage=db_storage, vector_store=vector_store)
rag_tool = RAGSearchTool(
    vector_store=vector_store,
    db_storage=db_storage,
    data_prep_tool=data_prep
)

start = time.time()
rag_result = rag_tool.answer(
    query=query,
    ticker="HOOD",
    filing_type="10-K",
    top_k=5,
    score_threshold=0.5,
    include_sources=True
)
rag_time = time.time() - start

print(f"\n⏱️  Time: {rag_time:.1f}s")
print(f"\n📝 Answer:")
print("-" * 80)
print(rag_result['answer'])
print("-" * 80)
print(f"\n📚 Sources used: {rag_result['num_sources']} chunks")

if 'sources' in rag_result and rag_result['sources']:
    print("\n🔍 Top 3 source chunks:")
    for i, source in enumerate(rag_result['sources'][:3], 1):
        print(f"\n  [{i}] Score: {source['score']:.3f} | Section: {source['section']}")
        print(f"      {source['text'][:200]}...")

# ============================================================================
# TEST 2: Orchestrator
# ============================================================================
print("\n\n" + "="*80)
print("APPROACH 2: Orchestrator with Tools")
print("="*80)

# Initialize services for tools
from app.tools.data_prep_service import DataPrepTool
from app.tools.rag_search_service import RAGSearchTool
from app.services.storage import DatabaseStorage

db_storage = DatabaseStorage()
data_prep = DataPrepTool(db_storage=db_storage, vector_store=vector_store)
rag_search = RAGSearchTool(vector_store=vector_store)

initialize_tools(data_prep, rag_search)

# Import the tools
from app.tools.finance_tool import ensure_filing_available, search_sec_filings

orchestrator = FinanceOrchestrator(
    db_storage=db_storage,
    vector_store=vector_store,
    tools=[ensure_filing_available, search_sec_filings]
)

start = time.time()
orch_result = orchestrator.invoke(query)
orch_time = time.time() - start

print(f"\n⏱️  Time: {orch_time:.1f}s")
print(f"\n📝 Answer:")
print("-" * 80)
print(orch_result['answer'])
print("-" * 80)

# ============================================================================
# COMPARISON
# ============================================================================
print("\n\n" + "="*80)
print("COMPARISON SUMMARY")
print("="*80)

print(f"\n1. Direct RAG Chain:")
print(f"   ⏱️  Time: {rag_time:.1f}s")
print(f"   📏 Answer length: {len(rag_result['answer'])} chars")
print(f"   📚 Sources: {rag_result['num_sources']} chunks")

print(f"\n2. Orchestrator:")
print(f"   ⏱️  Time: {orch_time:.1f}s")
print(f"   📏 Answer length: {len(str(orch_result['answer']))} chars")

print(f"\n⚡ Speed:")
if orch_time < rag_time:
    speedup = ((rag_time - orch_time) / rag_time * 100)
    print(f"   → Orchestrator is {speedup:.1f}% faster ({rag_time - orch_time:.1f}s saved)")
else:
    slowdown = ((orch_time - rag_time) / orch_time * 100)
    print(f"   → Direct RAG is {slowdown:.1f}% faster ({orch_time - rag_time:.1f}s saved)")

print("\n💡 Quality Check:")
print("   - Compare answer accuracy above")
print("   - Check if both found the CEO name")
print("   - Verify source citations in RAG approach")
print("\n")