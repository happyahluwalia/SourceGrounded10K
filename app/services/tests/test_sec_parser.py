import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_sec_parser.py
from app.services.sec_parser import SECFilingParser
import os

print("="*60)
print("TEST: Parse SEC Filing")
print("="*60)

# Find the downloaded file
filing_dir = "data/filings/AAPL"
files = os.listdir(filing_dir)
html_files = [f for f in files if f.endswith('.html')]

if not html_files:
    print("❌ No HTML files found. Run test_sec_download.py first.")
    exit(1)

filepath = os.path.join(filing_dir, html_files[0])
print(f"\nParsing: {filepath}")

# Initialize parser
parser = SECFilingParser(filepath)

# Test 1: Get full text
print("\n" + "="*60)
print("TEST 1: Extract Full Text")
print("="*60)

full_text = parser.get_full_text()
print(f"✅ Extracted {len(full_text):,} characters")
print(f"\nFirst 500 characters:")
print("-"*60)
print(full_text[:500])
print("-"*60)

# Test 2: Extract sections
print("\n" + "="*60)
print("TEST 2: Extract Sections")
print("="*60)

sections = parser.extract_sections()
print(f"✅ Found {len(sections)} sections\n")

for section_name in list(sections.keys())[:5]:  # Show first 5
    section_text = sections[section_name]
    print(f"📄 {section_name}")
    print(f"   Length: {len(section_text):,} characters")
    print(f"   Preview: {section_text[:150]}...")
    print()

# Test 3: Extract tables
print("\n" + "="*60)
print("TEST 3: Extract Tables")
print("="*60)

tables = parser.extract_tables()
print(f"✅ Found {len(tables)} tables\n")

for i, table in enumerate(tables[:3], 1):  # Show first 3
    print(f"📊 Table {i}")
    print(f"   Rows: {table['num_rows']}, Columns: {table['num_cols']}")
    print(f"   First 2 rows:")
    for row in table['data'][:2]:
        print(f"      {row}")
    print()

# Test 4: Get metadata
print("\n" + "="*60)
print("TEST 4: Extract Metadata")
print("="*60)

metadata = parser.get_metadata()
print(f"✅ Extracted metadata:")
for key, value in metadata.items():
    print(f"   {key}: {value}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Total characters: {len(full_text):,}")
print(f"Total sections: {len(sections)}")
print(f"Total tables: {len(tables)}")
print(f"File parsed: {filepath}")
print("="*60)