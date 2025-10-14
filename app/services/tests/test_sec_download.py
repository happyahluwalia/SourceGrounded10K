import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_sec_download.py
from app.services.sec_client import SECClient

client = SECClient()

print("="*60)
print("TEST: Download Filing")
print("="*60)

# Get Apple's most recent 10-K
print("\n1. Fetching AAPL's latest 10-K...")
filings = client.get_company_filings("AAPL", filing_types=["10-K"], limit=1)

if not filings:
    print("❌ No 10-K filings found")
    exit(1)

filing = filings[0]
print(f"   Found: {filing['form']} from {filing['filingDate']}")
print(f"   Report Date: {filing['reportDate']}")
print(f"   Document: {filing['primaryDocument']}")

# Download it
print("\n2. Downloading filing...")
filepath = client.download_filing(filing)

# Verify it exists and check size
print("\n3. Verifying download...")
import os
if os.path.exists(filepath):
    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"   ✅ File exists: {filepath}")
    print(f"   Size: {size_mb:.2f} MB")
    
    # Read first 500 chars
    with open(filepath, 'r') as f:
        preview = f.read(500)
    print(f"\n   First 500 characters:")
    print(f"   {'-'*50}")
    print(f"   {preview}...")
    print(f"   {'-'*50}")
else:
    print(f"   ❌ File not found: {filepath}")

print("\n" + "="*60)
print("✅ TEST PASSED!")
print("="*60)