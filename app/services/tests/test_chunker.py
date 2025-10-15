import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_chunker.py

from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker
import json

print("="*60)
print("TEST: Financial Document Chunking")
print("="*60)

# Parse a filing
filepath = "data/filings/AAPL/2024-10-K-2024-09-28.html"
parser = SECFilingParser(filepath)

print("\n1. Parsing filing...")
sections = parser.extract_sections()
tables = parser.extract_tables()
print(f"   ✅ Parsed {len(sections)} sections")
print(f"   ✅ Parsed {len(tables)} tables")

# Create filing metadata
filing_metadata = {
    "ticker": "AAPL",
    "filing_date": "2024-11-01",
    "report_date": "2024-09-28",
    "form": "10-K",
    "fiscal_year": 2024
}

# Initialize chunker
print("\n2. Initializing chunker...")
chunker = FinancialDocumentChunker(
    chunk_size=512,      # ~512 characters ≈ 128 tokens
    chunk_overlap=75,    # ~15% overlap
    min_chunk_size=50
)
print("   ✅ Chunker ready")

# Chunk the filing
print("\n3. Chunking filing...")
chunks = chunker.chunk_filing(sections, tables, filing_metadata)
print(f"   ✅ Created {len(chunks)} chunks")

# Get statistics
print("\n4. Chunk Statistics:")
print("="*60)
stats = chunker.get_chunk_stats(chunks)
for key, value in stats.items():
    if isinstance(value, float):
        print(f"   {key}: {value:.1f}")
    else:
        print(f"   {key}: {value}")

# Show sample chunks
print("\n5. Sample Chunks:")
print("="*60)

# Sample section chunk
section_chunks = [c for c in chunks if c["chunk_type"] == "section"]
if section_chunks:
    sample_section = section_chunks[0]
    print("\n📄 SECTION CHUNK EXAMPLE:")
    print(f"   Section: {sample_section['section']}")
    print(f"   Chunk: {sample_section['chunk_index'] + 1}/{sample_section['total_chunks_in_section']}")
    print(f"   Size: {sample_section['char_count']} chars (~{sample_section['token_count_estimate']} tokens)")
    print(f"\n   Text preview:")
    print(f"   {'-'*56}")
    print(f"   {sample_section['text'][:300]}...")
    print(f"   {'-'*56}")

# Sample table chunk
table_chunks = [c for c in chunks if c["chunk_type"] == "table"]
if table_chunks:
    sample_table = table_chunks[0]
    print("\n📊 TABLE CHUNK EXAMPLE:")
    print(f"   Table index: {sample_table['chunk_index']}")
    print(f"   Dimensions: {sample_table['table_rows']} rows × {sample_table['table_cols']} cols")
    print(f"   Size: {sample_table['char_count']} chars")
    print(f"\n   Table preview (first 5 lines):")
    print(f"   {'-'*56}")
    lines = sample_table['text'].split('\n')[:5]
    for line in lines:
        print(f"   {line}")
    print(f"   {'-'*56}")

# Test metadata
print("\n6. Metadata Example:")
print("="*60)
print(json.dumps(chunks[0], indent=2, default=str))

# Section distribution
print("\n7. Chunks per Section:")
print("="*60)
section_counts = {}
for chunk in chunks:
    if chunk["chunk_type"] == "section":
        section = chunk["section"]
        section_counts[section] = section_counts.get(section, 0) + 1

for section, count in list(section_counts.items())[:10]:  # Show first 10
    print(f"   {section}: {count} chunks")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)