#!/usr/bin/env python3
"""
This module defines the FilingQATool, a comprehensive tool that encapsulates
the entire Plan-Execute-Synthesize pipeline for answering questions based on
financial filings.
"""

import sys
import re
import json
import time
import logging
import ollama
from pathlib import Path

# Ensure the app root is in the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.storage import DatabaseStorage
from app.services.vector_store import VectorStore
from app.tools.data_prep_service import DataPrepTool
from app.tools.rag_search_service import RAGSearchTool
from app.services.ticker_service import get_ticker_service # Needed for comprehensive company detection

# Special message to indicate an unsupported company was found
UNSUPPORTED_COMPANY_MSG = "UNSUPPORTED_COMPANY"

# ============================================================================
# 0. QUERY PRE-PROCESSING
# ============================================================================

def preprocess_query_with_ticker(query: str) -> str:
    """
    Identifies a company name from our supported list in the query and injects the verified ticker.
    If a company is found that is not supported, returns a special message.
    """
    # print("\n" + "-"*80) # Removed print statements for cleaner tool output
    # print("Step 0: Pre-processing query... [Deterministic Function Call]")
    
    try:
        supported_companies_path = Path(__file__).parent.parent.parent / "app" / "core" / "supported_companies.json"
        with open(supported_companies_path, 'r') as f:
            supported_companies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not load or parse supported_companies.json: {e}")
        return query # Proceed without verification

    # Create a mapping from lowercase name to ticker for easy lookup
    name_to_ticker_map = {item['name'].lower(): item['ticker'] for item in supported_companies}
    supported_tickers_set = {item['ticker'].upper() for item in supported_companies}
    
    # Build regex from the supported names, sorted by length descending
    supported_names = sorted(name_to_ticker_map.keys(), key=len, reverse=True)
    pattern = r'\b(' + '|'.join([re.escape(name) for name in supported_names]) + r')\b'
    
    # Attempt 1: Match supported company name via regex
    match = re.search(pattern, query, re.IGNORECASE)
    if match:
        company_name = match.group(1).lower()
        found_ticker = name_to_ticker_map.get(company_name)
        if found_ticker:
            # print(f"SUCCESS: Found supported company '{company_name}' and verified ticker: {found_ticker}")
            return f"{query}\n(Verified Ticker: {found_ticker})"
    
    # Attempt 2: Match supported ticker directly in query
    for word in query.split():
        if word.upper() in supported_tickers_set:
             # print(f"SUCCESS: Found supported ticker '{word.upper()}' directly in query.")
             return f"{query}\n(Verified Ticker: {word.upper()})"

    # If we reach here, no *supported* company was found. Now, check if it's *any* company.
    # Use the full TickerService's map to detect *any* company name, even if unsupported.
    full_ticker_service = get_ticker_service()
    if not full_ticker_service._ticker_map:
        print("WARNING: Full TickerService map not available for comprehensive company detection.")
        # Fallback to simple suffix check if full map isn't loaded
        company_suffix_pattern = r'\b(inc|corp|ltd|llc|co|group|holdings|sa|plc|ag)\b'
        if re.search(company_suffix_pattern, query, re.IGNORECASE):
            # print(f"INFO: Query contains a company name (via suffix) not in the supported list.")
            return UNSUPPORTED_COMPANY_MSG
        # print("INFO: No company name detected (via suffix) in query, proceeding without verification.")
        return query

    # Build a comprehensive regex from all company names in the full TickerService map
    # Exclude already supported names to avoid redundant checks and keep pattern smaller
    all_company_names_from_full_map = sorted(
        [re.escape(name) for name in full_ticker_service._ticker_map.keys() if name.lower() not in name_to_ticker_map], # Exclude already supported names
        key=len, reverse=True
    )
    if all_company_names_from_full_map:
        comprehensive_pattern = r'\b(' + '|'.join(all_company_names_from_full_map) + r')\b'
        if re.search(comprehensive_pattern, query, re.IGNORECASE):
            # print(f"INFO: Query contains an unsupported company name detected from full map.")
            return UNSUPPORTED_COMPANY_MSG

    # print("INFO: No company name detected in query, proceeding without verification.")
    # If no company name is detected at all, it's likely a general query, so proceed.
    return query

# ============================================================================
# 1. PLANNER AGENT
# ============================================================================

def get_plan(query: str) -> dict:
    """
    Generates a structured JSON plan from a user query using an LLM.
    """
    # print("\n" + "-"*80)
    # print("Step 1: Generating execution plan... [Model Call]")
    
    try:
        prompt_path = Path(__file__).parent.parent.parent / "app" / "prompts" / "planner.txt"
        system_prompt = prompt_path.read_text()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found at {prompt_path}")
        return None

    ollama_client = ollama.Client(host=settings.ollama_base_url)

    try:
        response = ollama_client.chat(
            model=settings.planner_model, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            options={"temperature": 0.0}
        )
        response_content = response['message']['content']
        
        try:
            json_start_index = response_content.find('{')
            json_end_index = response_content.rfind('}') + 1
            if json_start_index != -1 and json_end_index != 0:
                json_str = response_content[json_start_index:json_end_index]
                plan = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in the response.")
        except (ValueError, json.JSONDecodeError) as e:
            raise json.JSONDecodeError(f"Failed to decode JSON: {e}", response_content, 0)

        # print(f"SUCCESS: Plan generated.")
        # print(json.dumps(plan, indent=2))
        return plan

    except Exception as e:
        print(f"ERROR: Failed to generate or parse plan: {e}")
        return None

# ============================================================================
# 2. EXECUTOR AGENT
# ============================================================================

def execute_plan(plan: dict) -> list:
    """
    Executes the structured plan using deterministic tools.
    """
    # print("\n" + "-"*80)
    # print("Step 2: Executing plan... [Deterministic Function Call]")
    
    db_storage = DatabaseStorage()
    vector_store = VectorStore()
    data_prep = DataPrepTool(db_storage=db_storage, vector_store=vector_store)
    
    all_chunks = []
    if not plan or 'tasks' not in plan:
        print("ERROR: Invalid plan provided.")
        return []

    for i, task in enumerate(plan['tasks']):
        # print(f"  - Executing Task {i+1}/{len(plan['tasks'])}: {task.get('search_query', 'N/A')} for {task.get('ticker', 'N/A')}")
        
        ticker = task.get('ticker')
        filing_type = task.get('filing_type')
        if not ticker or not filing_type:
            print(f"    > ERROR: Task is missing ticker or filing_type.")
            continue

        # print(f"    > Checking/processing filing: {ticker} {filing_type}...")
        prep_result = data_prep.get_or_process_filing(ticker, filing_type)
        
        if prep_result['status'] not in ['exists', 'success']:
            print(f"    > ERROR: Failed to prepare filing. Status: {prep_result.get('status')}")
            continue
        
        # print(f"    > Filing is ready. Status: {prep_result['status']}")

        # print(f"    > Searching for: \"{task['search_query']}\"")
        chunks = vector_store.search(
            query=task['search_query'],
            ticker=task['ticker'],
            filing_type=task['filing_type']
        )
        # print(f"    > Found {len(chunks)} relevant chunks.")
        all_chunks.extend(chunks)

    unique_chunks = list({chunk['id']: chunk for chunk in all_chunks}.values())
    # print(f"\nSUCCESS: Execution complete. Found {len(unique_chunks)} unique chunks in total.")
    return unique_chunks

# ============================================================================
# 3. SYNTHESIZER
# ============================================================================

def synthesize_answer(query: str, chunks: list) -> str:
    """
    Generates a final answer from the retrieved context chunks.
    """
    # print("\n" + "-"*80)
    # print("Step 3: Synthesizing final answer... [Model Call]")

    if not chunks:
        return "I could not find any relevant information to answer your question."

    rag_tool = RAGSearchTool(vector_store=None)
    context = rag_tool.build_context(chunks)
    prompt = rag_tool.build_prompt(query, context)
    answer = rag_tool.generate(prompt)
    
    # print("SUCCESS: Answer synthesized.")
    return answer


@tool
def answer_filing_question(query: str) -> str:
    """Use this tool to answer any questions about a company's financial filings.
    
    This tool is a complete pipeline that performs the following steps:
    1. Pre-processes the query to identify and verify a supported company ticker.
    2. Creates a detailed execution plan using a Planner LLM.
    3. Executes the plan by fetching data from financial documents.
    4. Synthesizes a final, comprehensive answer using a Synthesizer LLM.

    Args:
        query: The user's natural language question.
        
    Returns:
        A complete, final answer to the user's question.
    """
    
    total_start_time = time.time()
    timings = {}

    # Step 0: Pre-process the query
    preprocess_start_time = time.time()
    processed_query = preprocess_query_with_ticker(query)
    timings['0. Pre-processing'] = time.time() - preprocess_start_time

    # Handle unsupported company case
    if processed_query == UNSUPPORTED_COMPANY_MSG:
        return "This company is not in the list of supported companies. Please ask about a supported company."

    # Step 1: Generate the plan
    plan_start_time = time.time()
    plan = get_plan(processed_query)
    timings['1. Planning (Model Call)'] = time.time() - plan_start_time

    if not plan:
        return "I was unable to create a plan to answer your question. Please try rephrasing it."

    # Step 2: Execute the plan to get context
    exec_start_time = time.time()
    context_chunks = execute_plan(plan)
    timings['2. Execution (Deterministic)'] = time.time() - exec_start_time
    
    # Step 3: Synthesize the final answer
    synth_start_time = time.time()
    final_answer = synthesize_answer(query, context_chunks)
    timings['3. Synthesis (Model Call)'] = time.time() - synth_start_time
    
    total_time = time.time() - total_start_time
    timings['Total Tool Time'] = total_time

    # Log performance summary
    logger.info("\n" + "="*80)
    logger.info("FILING QA TOOL: PERFORMANCE SUMMARY")
    logger.info("="*80)
    for step, duration in timings.items():
        logger.info(f"- {step}: {duration:.1f}s")
    logger.info("="*80 + "\n")

    return final_answer
