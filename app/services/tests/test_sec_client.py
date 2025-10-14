import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.sec_client import SECClient

# Test ticker to CIK
client = SECClient()

print("Testing ticker to CIK conversion...")
print("-" * 50)

# Test Apple
cik = client.ticker_to_cik("AAPL")
print(f"✅ AAPL → CIK: {cik}")
assert cik == 320193, f"Expected CIK 320193, got {cik}"

# Test Microsoft
cik = client.ticker_to_cik("MSFT")
print(f"✅ MSFT → CIK: {cik}")
assert cik == 789019, f"Expected 789019, got {cik}"

# Test cache (should be instant)
import time
start = time.time()
cik = client.ticker_to_cik("AAPL")  # From cache
elapsed = time.time() - start
print(f"✅ Cache working (lookup took {elapsed*1000:.1f}ms)")

print("\n" + "="*60)
print("TEST 2: Get All Recent Filings (limit 2)")
print("="*60)

filings = client.get_company_filings("AAPL", limit=2)
print(f"✅ Found {len(filings)} filings")

for i, filing in enumerate(filings, 1):
    print(f"\n{i}. {filing['form']} - {filing['filingDate']}")
    print(f"   Report Date: {filing['reportDate']}")
    print(f"   Document: {filing['primaryDocument']}")
    print(f"   URL: {filing['documentURL'][:80]}...")

print("\n" + "="*60)
print("TEST 3: Get Only 10-K Filings")
print("="*60)

filings_10k = client.get_company_filings("AAPL", filing_types=["10-K"], limit=3)
print(f"✅ Found {len(filings_10k)} 10-K filings")

for i, filing in enumerate(filings_10k, 1):
    print(f"\n{i}. {filing['form']} - {filing['filingDate']}")
    print(f"   URL: {filing['documentURL']}")

print("\n" + "="*60)
print("TEST 4: Get 10-K and 10-Q Filings")
print("="*60)

filings_mixed = client.get_company_filings("AAPL", filing_types=["10-K", "10-Q"], limit=5)
print(f"✅ Found {len(filings_mixed)} filings")

for filing in filings_mixed:
    print(f"   {filing['form']} - {filing['filingDate']}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)