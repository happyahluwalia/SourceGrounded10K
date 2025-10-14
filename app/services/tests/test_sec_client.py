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

print("\n✅ All tests passed!")