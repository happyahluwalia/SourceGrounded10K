"""
Test if the log streaming handler is working
"""

import logging
import time
from app.services.log_streamer import get_log_stream_handler, subscribe_to_logs

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize the log stream handler
handler = get_log_stream_handler()
print("✅ Log stream handler initialized")

# Subscribe to logs
log_queue = subscribe_to_logs()
print("✅ Subscribed to logs")

# Create a test logger
logger = logging.getLogger('test')
logger.setLevel(logging.INFO)

print("\n📝 Sending test logs...")
print("-" * 60)

# Send some test logs
logger.info("Test log 1")
logger.warning("Test warning")
logger.error("Test error")

# Check if logs were captured
print("\n📥 Checking if logs were captured...")
print("-" * 60)

captured_logs = []
try:
    while not log_queue.empty():
        log = log_queue.get_nowait()
        captured_logs.append(log)
        print(f"✅ Captured: [{log['level']}] {log['message']}")
except:
    pass

if captured_logs:
    print(f"\n✅ SUCCESS! Captured {len(captured_logs)} logs")
else:
    print("\n❌ FAILED! No logs captured")
    print("   The log handler might not be attached properly")
