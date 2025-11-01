#!/usr/bin/env python3
"""
A simple script to check the status of the Qdrant vector store collection.
"""

import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_store import VectorStore


def check_status():
    print("Connecting to Qdrant to check collection status...")
    try:
        vector_store = VectorStore('localhost', '6333', 'financial_filings')
        info = vector_store.get_collection_info()
        
        print("\n--- Qdrant Collection Info ---")
        print(json.dumps(info, indent=2))
        print("------------------------------\n")
        
        vectors_count = info.get("vectors_count", 0)
        if vectors_count > 0:
            print(f"✅  SUCCESS: The collection '{vector_store.collection_name}' contains {vectors_count} vectors.")
            print("This indicates that the data has been loaded correctly.")
        else:
            print(f"❌  FAILURE: The collection '{vector_store.collection_name}' contains 0 vectors.")
            print("This is the likely cause of the 'no result found' error.")
            print("Please re-run the `scripts/initialize_supported_filings.py` script to load the data.")

    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"Failed to connect to Qdrant or get collection info: {e}")
        print("Please ensure your Qdrant Docker container is running and accessible.")
        print("-------------")

if __name__ == "__main__":
    check_status()
