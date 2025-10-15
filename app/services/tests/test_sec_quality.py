import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_section_quality.py
from app.services.sec_parser import SECFilingParser
import os

filepath = "data/filings/AAPL/2024-10-K-2024-09-28.html"
parser = SECFilingParser(filepath)
sections = parser.extract_sections()

# Print all section names we found
print("="*60)
print("Found Sections:")
print("="*60)
for section_name in sections.keys():
    print(f"  • {section_name}")

# Now look for Item 1A (will work regardless of spacing in HTML)
print("\n" + "="*60)
print("Looking for Item 1A: Risk Factors")
print("="*60)

# Try exact match first
if "Item 1A: Risk Factors" in sections:
    print("✅ Found exact match!")
    risk_section = sections["Item 1A: Risk Factors"]
else:
    # Try fuzzy match (any section starting with "Item 1A:")
    matching = [s for s in sections.keys() if s.startswith("Item 1A:")]
    if matching:
        print(f"✅ Found match: '{matching[0]}'")
        risk_section = sections[matching[0]]
    else:
        print("❌ Section not found")
        exit(1)

print(f"Length: {len(risk_section):,} characters")
print(f"\nFirst 500 characters:\n")
print(risk_section[:500])