import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# test_normalization.py
from app.services.sec_parser import SECFilingParser

# Test cases
test_cases = [
    "Item 1A : Risk Factors",
    "Item  7  -  MD&A",
    "ITEM 1A. Risk Factors",
    "Item 1: Business",
    "ITEM 1A:Risk Factors",  # No space after colon
]

print("Testing section name normalization:")
print("="*60)

for test in test_cases:
    normalized = SECFilingParser.normalize_section_name(test)
    print(f"'{test}'")
    print(f"  → '{normalized}'")
    print()