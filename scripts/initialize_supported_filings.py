#!/usr/bin/env python3
"""
Script to initialize and pre-process SEC filings for supported companies.

This script reads the `supported_companies.json` file, and for each company,
ensures that its latest 10-K filing is downloaded, parsed, chunked,
embedded, and stored in the vector database.
"""

import sys
import json
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.storage import DatabaseStorage
from app.services.vector_store import VectorStore
from app.tools.data_prep_service import DataPrepTool

def initialize_filings():
    print("\n" + "#"*80)
    print("Initializing Supported Company Filings")
    print("#"*80)

    # Load supported companies list
    try:
        supported_companies_path = Path(__file__).parent.parent / "app" / "core" / "supported_companies.json"
        with open(supported_companies_path, 'r') as f:
            supported_companies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not load or parse supported_companies.json: {e}")
        return

    if not supported_companies:
        print("WARNING: No supported companies found in supported_companies.json. Nothing to initialize.")
        return

    # Initialize services
    db_storage = DatabaseStorage()
    vector_store = VectorStore()
    data_prep = DataPrepTool(db_storage=db_storage, vector_store=vector_store)

    print(f"Found {len(supported_companies)} companies to initialize.")
    print("This may take some time if filings need to be downloaded and processed.")
    print("-"*80)

    for i, company in enumerate(supported_companies):
        ticker = company['ticker']
        name = company['name']
        print(f"[{i+1}/{len(supported_companies)}] Processing {name} ({ticker})...")
        
        start_time = time.time()
        try:
            # We use process_filing with force_reprocess=True to ensure that the vector store
            # is in sync with our current embedding model and code, solving potential mismatches.
            result = data_prep.process_filing(ticker, "10-K", force_reprocess=True)
            end_time = time.time()
            
            if result['status'] in ['exists', 'success']:
                print(f"  ✅ SUCCESS: Filing for {ticker} is ready. Status: {result['status']}. ({end_time - start_time:.1f}s)")
            else:
                print(f"  ❌ ERROR: Failed to process filing for {ticker}. Status: {result.get('status')}, Message: {result.get('message', 'Unknown error')}. ({end_time - start_time:.1f}s)")
        except Exception as e:
            end_time = time.time()
            print(f"  💥 CRITICAL ERROR: An unexpected exception occurred while processing {ticker}. ({end_time - start_time:.1f}s)")
            print(f"     Exception: {e}")
        
        print("-"*80)

    print("\n" + "#"*80)
    print("Initialization Complete")
    print("#"*80)

if __name__ == "__main__":
    initialize_filings()
