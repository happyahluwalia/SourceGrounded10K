"""
Test script for SSE log streaming endpoint
"""

import requests
import json
import time

def test_sse_stream():
    """Test the SSE log streaming endpoint"""
    
    url = "http://localhost:8000/api/logs/stream"
    
    print("🔌 Connecting to SSE endpoint...")
    print(f"   URL: {url}")
    print()
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        print("✅ Connected! Listening for logs...")
        print("   (Press Ctrl+C to stop)")
        print()
        print("-" * 80)
        
        # Read SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                # SSE format: "data: {...}"
                if line.startswith('data: '):
                    data = line[6:]  # Remove "data: " prefix
                    try:
                        log = json.loads(data)
                        timestamp = log.get('timestamp', '')[:19]  # Trim microseconds
                        level = log.get('level', 'INFO')
                        logger = log.get('logger', 'unknown')
                        message = log.get('message', '')
                        
                        # Format like the debug panel
                        print(f"{timestamp} [{level:7}] {logger:30} {message}")
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse: {data}")
                        
                elif line.startswith(':'):
                    # Keepalive ping
                    print("💓 keepalive")
                    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print("👋 Disconnected")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
        print("   Start with: uvicorn app.api.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_sse_stream()
