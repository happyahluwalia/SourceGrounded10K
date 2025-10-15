import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_chunk_quality.py

from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker

filepath = "data/filings/AAPL/2024-10-K-2024-09-28.html"
parser = SECFilingParser(filepath)

sections = parser.extract_sections()
tables = parser.extract_tables()

filing_metadata = {
    "ticker": "AAPL",
    "filing_date": "2024-11-01",
    "form": "10-K"
}

chunker = FinancialDocumentChunker(chunk_size=512, chunk_overlap=75)
chunks = chunker.chunk_filing(sections, tables, filing_metadata)

print("="*60)
print("CHUNK QUALITY ANALYSIS")
print("="*60)

# 1. Check for very small chunks (might be artifacts)
print("\n1. Size Distribution:")
print("-"*60)
small_chunks = [c for c in chunks if c["char_count"] < 100]
medium_chunks = [c for c in chunks if 100 <= c["char_count"] < 500]
large_chunks = [c for c in chunks if c["char_count"] >= 500]

print(f"   Small (<100 chars): {len(small_chunks)} ({len(small_chunks)/len(chunks)*100:.1f}%)")
print(f"   Medium (100-500): {len(medium_chunks)} ({len(medium_chunks)/len(chunks)*100:.1f}%)")
print(f"   Large (500+): {len(large_chunks)} ({len(large_chunks)/len(chunks)*100:.1f}%)")

# 2. Check if tables are intact
print("\n2. Table Integrity:")
print("-"*60)
table_chunks = [c for c in chunks if c["chunk_type"] == "table"]
oversized_tables = [c for c in table_chunks if c["char_count"] > 1536]  # 3x chunk_size

print(f"   Total tables: {len(table_chunks)}")
print(f"   Oversized tables: {len(oversized_tables)}")
if oversized_tables:
    print("   ⚠️  Some tables exceed 3x chunk size - may need special handling")
else:
    print("   ✅ All tables fit reasonably")

# 3. Check section boundary preservation
print("\n3. Section Boundary Check:")
print("-"*60)
sections_in_chunks = set(c["section"] for c in chunks if c["chunk_type"] == "section")
original_sections = set(sections.keys())

print(f"   Original sections: {len(original_sections)}")
print(f"   Sections in chunks: {len(sections_in_chunks)}")
print(f"   ✅ All sections preserved: {sections_in_chunks == original_sections}")

# 4. Sample a few chunks to verify they're coherent
print("\n4. Coherence Check (Sample Chunks):")
print("-"*60)

sample_chunks = [c for c in chunks if c["chunk_type"] == "section"][:3]
for i, chunk in enumerate(sample_chunks, 1):
    text = chunk["text"]
    
    # Check if chunk starts/ends mid-sentence
    starts_clean = text[0].isupper() or text.startswith("(")
    ends_clean = text.rstrip()[-1] in ".!?)"
    
    print(f"\n   Chunk {i}:")
    print(f"   Section: {chunk['section']}")
    print(f"   Starts cleanly: {'✅' if starts_clean else '⚠️'}")
    print(f"   Ends cleanly: {'✅' if ends_clean else '⚠️'}")
    print(f"   First 80 chars: {text[:80]}...")
    print(f"   Last 80 chars: ...{text[-80:]}")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)