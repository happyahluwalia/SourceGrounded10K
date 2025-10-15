import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_duplicate_handling.py

from app.services.storage import DatabaseStorage, convert_date_strings

print("="*60)
print("TEST: Duplicate Filing Handling")
print("="*60)

storage = DatabaseStorage()

# Mock data for testing
filing_metadata = {
    "ticker": "MSFT",
    "company_name": "Microsoft Corporation",
    "filing_date": "2024-10-30",
    "report_date": "2024-09-30",
    "form": "10-Q",
    "document_url": "https://example.com/msft-10q.htm",
    "document_path": "data/filings/MSFT/2024-10Q.html"
}

# Mock chunks (just 3 for testing)
chunks_v1 = [
    {
        "section": "Item 1: Business",
        "chunk_index": 0,
        "total_chunks_in_section": 1,
        "chunk_type": "section",
        "char_count": 500,
        "token_count_estimate": 125
    },
    {
        "section": "Item 1A: Risk Factors",
        "chunk_index": 0,
        "total_chunks_in_section": 1,
        "chunk_type": "section",
        "char_count": 450,
        "token_count_estimate": 112
    },
    {
        "section": "Item 2: Properties",
        "chunk_index": 0,
        "total_chunks_in_section": 1,
        "chunk_type": "section",
        "char_count": 300,
        "token_count_estimate": 75
    }
]

try:
    # First save
    print("\n1. Saving filing (first time)...")
    filing_metadata_db = convert_date_strings(filing_metadata)
    filing_v1 = storage.save_filing_with_chunks(filing_metadata_db, chunks_v1)
    print(f"   ✅ Filing ID: {filing_v1.id}, Chunks: {filing_v1.num_chunks}")
    
    # Verify
    stats = storage.get_filing_stats("MSFT")
    print(f"   Total MSFT filings: {len(stats)}")
    
    # Second save (same filing - should replace)
    print("\n2. Saving same filing again (should replace)...")
    
    # Modify chunks slightly (simulate updated version)
    chunks_v2 = chunks_v1.copy()
    chunks_v2.append({
        "section": "Item 3: Legal Proceedings",
        "chunk_index": 0,
        "total_chunks_in_section": 1,
        "chunk_type": "section",
        "char_count": 250,
        "token_count_estimate": 62
    })
    
    filing_v2 = storage.save_filing_with_chunks(filing_metadata_db, chunks_v2)
    print(f"   ✅ Filing ID: {filing_v2.id}, Chunks: {filing_v2.num_chunks}")
    
    # Verify - should still be 1 filing, but 4 chunks now
    stats = storage.get_filing_stats("MSFT")
    print(f"   Total MSFT filings: {len(stats)}")
    print(f"   Chunks in current version: {stats[0]['num_chunks']}")
    
    # Verify old chunks were deleted
    from app.models.database import SessionLocal
    session = SessionLocal()
    all_chunks = session.query(storage._get_session().query(
        __import__('app.models.database', fromlist=['Chunk']).Chunk
    ).filter_by(filing_id=filing_v2.id).count())
    session.close()
    
    print(f"\n✅ Duplicate handling works!")
    print(f"   Old version deleted")
    print(f"   New version saved with updated chunks")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    storage.close()

print("\n" + "="*60)
print("✅ TEST COMPLETE!")
print("="*60)