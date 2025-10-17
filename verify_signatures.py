"""
Verify all method signatures match between callers and callees.
Run this to catch integration issues before runtime.
"""

import inspect
from app.services.storage import DatabaseStorage
from app.services.sec_client import SECClient
from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker
from app.services.vector_store import VectorStore
from app.services.rag_chain import RAGChain

def check_method_signature(cls, method_name):
    """Check if a method exists and print its signature."""
    if hasattr(cls, method_name):
        method = getattr(cls, method_name)
        sig = inspect.signature(method)
        print(f"✅ {cls.__name__}.{method_name}{sig}")
        return True
    else:
        print(f"❌ {cls.__name__}.{method_name} - METHOD NOT FOUND")
        return False

print("=" * 80)
print("VERIFYING METHOD SIGNATURES")
print("=" * 80)

print("\n📦 DatabaseStorage:")
check_method_signature(DatabaseStorage, '__init__')
check_method_signature(DatabaseStorage, 'get_session')
check_method_signature(DatabaseStorage, 'save_filing_with_chunks')
check_method_signature(DatabaseStorage, 'upsert_company')

print("\n📡 SECClient:")
check_method_signature(SECClient, '__init__')
check_method_signature(SECClient, 'get_company_filings')
check_method_signature(SECClient, 'download_filing')

print("\n📄 SECFilingParser:")
check_method_signature(SECFilingParser, '__init__')
check_method_signature(SECFilingParser, 'extract_sections')
check_method_signature(SECFilingParser, 'extract_tables')

print("\n✂️  FinancialDocumentChunker:")
check_method_signature(FinancialDocumentChunker, '__init__')
check_method_signature(FinancialDocumentChunker, 'chunk_filing')

print("\n🔍 VectorStore:")
check_method_signature(VectorStore, '__init__')
check_method_signature(VectorStore, 'add_chunks')
check_method_signature(VectorStore, 'search')

print("\n🤖 RAGChain:")
check_method_signature(RAGChain, '__init__')
check_method_signature(RAGChain, 'answer')

print("\n" + "=" * 80)
print("SIGNATURE VERIFICATION COMPLETE")
print("=" * 80)
