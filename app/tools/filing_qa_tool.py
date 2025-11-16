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
from app.models.database import SECFiling
from app.services.ticker_service import get_ticker_service  # Needed for comprehensive company detection

# Special message to indicate an unsupported company was found
UNSUPPORTED_COMPANY_MSG = "UNSUPPORTED_COMPANY"

# Cache service instances to avoid repeated initialization
_db_storage_instance = None
_vector_store_instance = None

def _get_db_storage():
    """Get or create cached DatabaseStorage instance."""
    global _db_storage_instance
    if _db_storage_instance is None:
        _db_storage_instance = DatabaseStorage()
    return _db_storage_instance

def _get_vector_store():
    """Get or create cached VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance

# ============================================================================
# FILING URL LOOKUP - Simple ticker-based approach
# ============================================================================

def get_filing_urls_by_tickers(tickers: list) -> dict:
    """
    Get filing URLs for given tickers from PostgreSQL.
    
    Simple approach: We know the tickers from the query, so just fetch
    the latest filing URL for each ticker directly.
    
    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT'])
    
    Returns:
        Dict mapping ticker to filing info:
        {
            'AAPL': {
                'ticker': 'AAPL',
                'filing_type': '10-K',
                'report_date': '2024-09-28',
                'document_url': 'https://www.sec.gov/...',
                'display_name': 'Apple 10-K (FY 2024)'
            }
        }
    """
    if not tickers:
        return {}
    
    logger.info(f"📄 Fetching filing URLs for tickers: {tickers}")
    
    # Use cached instance
    db_storage = _get_db_storage()
    filing_info = {}
    
    with db_storage.get_session() as session:
        for ticker in tickers:
            # Get the most recent 10-K filing for this ticker
            filing = session.query(SECFiling).filter(
                SECFiling.ticker == ticker,
                SECFiling.filing_type == '10-K'
            ).order_by(SECFiling.report_date.desc()).first()
            
            if filing:
                # Get company name for display
                from app.models.database import Company
                company = session.query(Company).filter(Company.ticker == ticker).first()
                company_name = company.name if company else ticker
                
                filing_info[ticker] = {
                    'ticker': ticker,
                    'filing_type': filing.filing_type,
                    'report_date': filing.report_date.strftime('%Y-%m-%d') if filing.report_date else None,
                    'document_url': filing.document_url,
                    'display_name': f"{company_name} {filing.filing_type} (FY {filing.report_date.year if filing.report_date else 'N/A'})"
                }
                logger.info(f"  ✓ {ticker}: {filing.document_url[:80] if filing.document_url else 'NULL'}")
            else:
                logger.warning(f"  ✗ {ticker}: No 10-K filing found")
    
    return filing_info

# ============================================================================
# RESPONSE FORMATTER - Converts structured LLM output to UI-ready format
# ============================================================================

def format_answer_for_ui(synthesis_result: dict, sources: list) -> dict:
    """
    Convert structured LLM output into UI-ready format.
    Follows principle: LLM provides semantic data, code handles presentation.
    
    Args:
        synthesis_result: Parsed JSON from synthesizer with sections
        sources: List of source chunks
    
    Returns:
        UI-ready format with components and props
    """
    answer_data = synthesis_result.get("answer", {})
    sections_raw = answer_data.get("sections", [])
    
    # Convert each section to UI component format
    formatted_sections = []
    for section in sections_raw:
        section_type = section.get("type", "paragraph")
        
        if section_type == "paragraph":
            formatted_sections.append(_format_paragraph(section, sources))
        elif section_type == "table":
            formatted_sections.append(_format_table(section, sources))
        elif section_type == "key_findings":
            formatted_sections.append(_format_key_findings(section, sources))
        elif section_type == "comparison_summary":
            formatted_sections.append(_format_comparison_summary(section, sources))
        else:
            logger.warning(f"Unknown section type: {section_type}, treating as paragraph")
            formatted_sections.append(_format_paragraph(section, sources))
    
    # Check if comparison data exists and add as section if not already present
    structured_data = synthesis_result.get("structured", {})
    companies_data = structured_data.get("companies", {})
    comparison_data = structured_data.get("comparison", {})
    if comparison_data and comparison_data.get("summary"):
        # Check if comparison_summary section already exists
        has_comparison_section = any(s.get("type") == "comparison_summary" for s in sections_raw)
        if not has_comparison_section:
            formatted_sections.append({
                "component": "ComparisonSummary",
                "props": {
                    "text": comparison_data.get("summary", ""),  # Frontend expects 'text', not 'summary'
                    "winner": comparison_data.get("winner"),
                    "metric": comparison_data.get("metric"),
                    "citations": []
                }
            })
    
    return {
        "sections": formatted_sections,
        "metadata": {
            "companies": companies_data,
            "comparison": comparison_data,
            "confidence": structured_data.get("confidence", "medium"),
            "missing_data": structured_data.get("missing_data", [])
        },
        "visualization": {
            "type": structured_data.get("visualization_hint", "none")
        }
    }

def _format_paragraph(section: dict, sources: list) -> dict:
    """Format paragraph section with inline citations."""
    return {
        "component": "Paragraph",
        "props": {
            "text": section.get("content", ""),
            "citations": _build_citations(section.get("citations", []), sources)
        }
    }

def _format_table(section: dict, sources: list) -> dict:
    """Format comparison table section."""
    data = section.get("data", {})
    
    # Handle case where content might be an object instead of string
    content = section.get("content", "Comparison")
    if isinstance(content, dict):
        # If content is a dict, it might have the table data
        # Use it as data if data is empty
        if not data or (not data.get("headers") and not data.get("rows")):
            data = content
        # Use a default title
        title = "Comparison"
    else:
        title = str(content)
    
    # Flatten rows if they contain objects (LLM sometimes generates this)
    rows = data.get("rows", [])
    flattened_rows = []
    for row in rows:
        if isinstance(row, list):
            flattened_row = []
            for cell in row:
                if isinstance(cell, dict):
                    # Extract values from dict and flatten
                    # e.g., {"company": "AAPL", "growth_rate": "2%"} -> ["AAPL", "2%"]
                    flattened_row.extend(cell.values())
                else:
                    flattened_row.append(str(cell))
            flattened_rows.append(flattened_row)
        else:
            # Single value row (shouldn't happen, but handle it)
            flattened_rows.append([str(row)])
    
    return {
        "component": "Table",
        "props": {
            "title": title,
            "headers": data.get("headers", []),
            "rows": flattened_rows,
            "citations": _build_citations(section.get("citations", []), sources)
        }
    }

def _format_key_findings(section: dict, sources: list) -> dict:
    """Format key findings as a list."""
    content = section.get("content", "")
    items = [content] if isinstance(content, str) else content
    return {
        "component": "KeyFindings",
        "props": {
            "items": items,
            "citations": _build_citations(section.get("citations", []), sources)
        }
    }

def _format_comparison_summary(section: dict, sources: list) -> dict:
    """Format comparison summary section."""
    return {
        "component": "ComparisonSummary",
        "props": {
            "text": section.get("content", ""),
            "citations": _build_citations(section.get("citations", []), sources)
        }
    }

def _build_citations(citation_indices: list, sources: list) -> list:
    """
    Build citation objects with hyperlinks from source indices.
    
    Args:
        citation_indices: List of 0-based indices into sources array
        sources: List of source chunks
    
    Returns:
        List of citation objects with text, url, ticker, etc.
    """
    citations = []
    for idx in citation_indices:
        if 0 <= idx < len(sources):
            source = sources[idx]
            # Use section_full if available, otherwise fall back to section
            section_display = source.get('section_full') or source.get('section', '')
            citations.append({
                "id": idx,
                "text": f"{source.get('filing_type', 'Filing')} {section_display}".strip(),
                "url": f"#source-{idx}",  # For scrolling to source in UI
                "document_url": source.get("document_url"),  # SEC.gov URL for external link
                "ticker": source.get("ticker", ""),
                "filing_type": source.get("filing_type", ""),
                "section": section_display,
                "report_date": source.get("report_date", "")
            })
        else:
            logger.warning(f"Citation index {idx} out of range (sources: {len(sources)})")
    return citations

# ============================================================================
# 0. QUERY PRE-PROCESSING
# ============================================================================

def preprocess_query_with_ticker(query: str) -> str:
    """
    Identifies a company name from our supported list in the query and injects the verified ticker.
    If a company is found that is not supported, returns a special message.
    """
    logger.info("Step 0: Pre-processing query... [Deterministic Function Call]")
    
    try:
        supported_companies_path = Path(__file__).parent.parent.parent / "app" / "core" / "supported_companies.json"
        with open(supported_companies_path, 'r') as f:
            supported_companies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not load or parse supported_companies.json: {e}")
        return query # Proceed without verification

    # Create a mapping from lowercase name to ticker for easy lookup
    name_to_ticker_map = {item['name'].lower(): item['ticker'] for item in supported_companies}
    supported_tickers_set = {item['ticker'].upper() for item in supported_companies}
    
    # Build regex from the supported names, sorted by length descending
    supported_names = sorted(name_to_ticker_map.keys(), key=len, reverse=True)
    pattern = r'\b(' + '|'.join([re.escape(name) for name in supported_names]) + r')\b'
    
    # Attempt 1: Match ALL supported company names via regex
    matches = re.findall(pattern, query, re.IGNORECASE)
    if matches:
        found_tickers = []
        for company_name in matches:
            ticker = name_to_ticker_map.get(company_name.lower())
            if ticker and ticker not in found_tickers:
                found_tickers.append(ticker)
        
        if found_tickers:
            # print(f"SUCCESS: Found supported companies and verified tickers: {found_tickers}")
            tickers_str = ", ".join(found_tickers)
            return f"{query}\n(Verified Tickers: {tickers_str})"
    
    # Attempt 2: Match supported ticker directly in query
    for word in query.split():
        if word.upper() in supported_tickers_set:
             # print(f"SUCCESS: Found supported ticker '{word.upper()}' directly in query.")
             return f"{query}\n(Verified Ticker: {word.upper()})"

    # If we reach here, no *supported* company was found. Now, check if it's *any* company.
    # Use the full TickerService's map to detect *any* company name, even if unsupported.
    full_ticker_service = get_ticker_service()
    if not full_ticker_service._ticker_map:
        logger.warning("Full TickerService map not available for comprehensive company detection.")
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
    Uses ChatOllama for consistency with the rest of the codebase.
    """
    # print("\n" + "-"*80)
    # print("Step 1: Generating execution plan... [Model Call]")
    
    try:
        prompt_path = Path(__file__).parent.parent.parent / "app" / "prompts" / "planner.txt"
        system_prompt = prompt_path.read_text()
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {prompt_path}")
        return None

    # Use LLM factory (supports both vLLM and Ollama)
    # NOTE: Structured outputs removed for planner - the schema was too complex
    # for small models (llama3.2:3b) and caused it to miss companies in comparisons
    from langchain_core.messages import SystemMessage, HumanMessage
    from app.utils.llm_factory import get_llm
    
    llm = get_llm(
        model_name=settings.planner_model,
        temperature=0.0
        # No format_schema parameter - let the model generate freely based on prompt examples
    )

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        # Token metrics: log before and after call
        from app.utils.token_metrics import current_token_metrics
        token_metrics = current_token_metrics.get()
        start_time = time.time()
        
        response = llm.invoke(messages)
        response_content = response.content
        
        # Log token metrics
        if token_metrics:
            token_metrics.log_call(
                stage="planner",
                model=settings.planner_model,
                input_messages=messages,
                output=response_content,
                start_time=start_time,
                end_time=time.time()
            )
        
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
        logger.error(f"Failed to generate or parse plan: {e}")
        return None

# ============================================================================
# 2. EXECUTOR AGENT
# ============================================================================

def execute_plan(plan: dict) -> dict:
    """
    Executes the structured plan using deterministic tools.
    
    Returns:
        dict: Results organized by company ticker
        {
            "AAPL": [chunk1, chunk2, ...],  # 5 chunks per company
            "MSFT": [chunk1, chunk2, ...]
        }
        
    Note: Changed from returning list to dict to maintain per-company
          separation for multi-company comparisons. This ensures equal
          data retrieval (5 chunks per company) instead of pooling all
          chunks together (which caused unbalanced comparisons).
    """
    # print("\n" + "-"*80)
    # print("Step 2: Executing plan... [Deterministic Function Call]")
    
    # Use cached instances to avoid repeated initialization
    db_storage = _get_db_storage()
    vector_store = _get_vector_store()
    data_prep = DataPrepTool(db_storage=db_storage, vector_store=vector_store)
    
    results_by_company = {}  # Maintain per-company separation
    
    if not plan or 'tasks' not in plan:
        logger.error("ERROR: Invalid plan provided.")
        return {}

    for i, task in enumerate(plan['tasks']):
        # print(f"  - Executing Task {i+1}/{len(plan['tasks'])}: {task.get('search_query', 'N/A')} for {task.get('ticker', 'N/A')}")
        
        ticker = task.get('ticker')
        filing_type = task.get('filing_type', '10-K')  # Default to 10-K if not provided
        if not ticker:
            logger.error(f"    > ERROR: Task {i+1} is missing ticker.")
            continue

        # print(f"    > Checking/processing filing: {ticker} {filing_type}...")
        prep_result = data_prep.get_or_process_filing(ticker, filing_type)
        
        if prep_result['status'] not in ['exists', 'success']:
            logger.error(f"    > ERROR: Failed to prepare filing. Status: {prep_result.get('status')}")
            continue
        
        # print(f"    > Filing is ready. Status: {prep_result['status']}")

        # print(f"    > Searching for: \"{task['search_query']}\"")
        chunks = vector_store.search(
            query=task['search_query'],
            ticker=ticker,
            filing_type=filing_type  # Use the variable with default applied
            # Uses settings.top_k as default (configured in .env)
        )
        logger.info(f"    > Found {len(chunks)} relevant chunks for {ticker}.")
        
        # Debug: Log first chunk content for CFO queries
        if chunks and 'cfo' in task['search_query'].lower():
            logger.info(f"    > First chunk preview (first 200 chars): {chunks[0].get('content', '')[:200]}...")
        
        # Store chunks by company ticker
        if ticker not in results_by_company:
            results_by_company[ticker] = []
        
        results_by_company[ticker].extend(chunks)
    
    # Deduplicate per company and limit to top 5
    for ticker in results_by_company:
        unique_chunks = list({chunk['id']: chunk for chunk in results_by_company[ticker]}.values())
        results_by_company[ticker] = unique_chunks[:5]  # Top 5 per company
        logger.info(f"    > Company {ticker}: {len(results_by_company[ticker])} unique chunks")
    
    total_chunks = sum(len(chunks) for chunks in results_by_company.values())
    logger.info(f"\nSUCCESS: Execution complete. Found {total_chunks} unique chunks across {len(results_by_company)} companies.")
    
    return results_by_company

# ============================================================================
# 3. SYNTHESIZER
# ============================================================================

def synthesize_answer(query: str, chunks_by_company: dict) -> dict:
    """
    Generates a final answer from the retrieved context chunks.
    
    Args:
        query: User's question
        chunks_by_company: Dict of chunks organized by ticker
                          {"AAPL": [chunks], "MSFT": [chunks]}
    
    Returns:
        dict: Parsed response with 'answer' and 'structured' data
        {
            "answer": str,  # Plain text answer for display
            "structured": dict  # Structured data (companies, comparison, etc.)
        }
    """
    # print("\n" + "-"*80)
    # print("Step 3: Synthesizing final answer... [Model Call]")

    if not chunks_by_company:
        return {
            "answer": {
                "sections": [{
                    "type": "paragraph",
                    "content": "I could not find any relevant information to answer your question.",
                    "citations": []
                }]
            },
            "structured": {}
        }

    rag_tool = RAGSearchTool(vector_store=None)
    
    # Build context maintaining company separation
    # chunks_by_company is a dict: {"AAPL": [chunks], "MSFT": [chunks]}
    context_parts = []
    for ticker, chunks in chunks_by_company.items():
        if chunks:
            context_parts.append(f"\n{'='*80}")
            context_parts.append(f"Context for {ticker}:")
            context_parts.append('='*80)
            context_parts.append(rag_tool.build_context(chunks))
    context = "\n".join(context_parts)
    
    # Log what we're sending to the LLM
    logger.info("="*80)
    logger.info(f"📝 QUERY: '{query}'")
    logger.info(f"📊 COMPANIES IN CONTEXT: {list(chunks_by_company.keys())}")
    logger.info(f"📦 CHUNK COUNTS: {{{', '.join([f'{k}: {len(v)} chunks' for k, v in chunks_by_company.items()])}}}")
    logger.info("="*80)
    
    prompt = rag_tool.build_prompt(query, context)
    
    # Token metrics: log before and after call
    from app.utils.token_metrics import current_token_metrics
    token_metrics = current_token_metrics.get()
    start_time = time.time()
    
    raw_answer = rag_tool.generate(prompt)
    
    # Log token metrics for synthesizer
    if token_metrics:
        # Convert prompt tuple to messages list for token counting
        if isinstance(prompt, tuple):
            from langchain_core.messages import SystemMessage, HumanMessage
            system_prompt, user_prompt = prompt
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        else:
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
        
        token_metrics.log_call(
            stage="synthesizer",
            model=settings.synthesizer_model,
            input_messages=messages,
            output=raw_answer,
            start_time=start_time,
            end_time=time.time()
        )
    
    # Parse JSON response from LLM
    import json
    import re
    
    try:
        # With structured outputs, response should be clean JSON
        # But handle legacy responses with markdown code blocks too
        raw_answer_stripped = raw_answer.strip()
        
        # Check if it's already valid JSON (structured outputs)
        if raw_answer_stripped.startswith('{'):
            parsed_result = json.loads(raw_answer_stripped)
        else:
            # Legacy: Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', raw_answer, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON object
                json_match = re.search(r'{.*}', raw_answer, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            parsed_result = json.loads(json_str)
        
        # Check if LLM double-nested the JSON (common bug with small models)
        # Pattern: {"answer": {"sections": [{"content": "{\n  \"answer\": {...}}"}]}}
        answer = parsed_result.get("answer", raw_answer)
        if isinstance(answer, dict) and "sections" in answer:
            first_section = answer["sections"][0] if answer["sections"] else None
            if first_section and isinstance(first_section.get("content"), str):
                content_str = first_section["content"]
                # Check if content looks like JSON (starts with { and contains "answer")
                if content_str.strip().startswith('{') and '"answer"' in content_str:
                    try:
                        # Try to parse the nested JSON
                        nested_json = json.loads(content_str)
                        if isinstance(nested_json, dict) and "answer" in nested_json:
                            # Replace with the inner structure
                            parsed_result = nested_json
                            answer = nested_json["answer"]
                    except json.JSONDecodeError as e:
                        # Try to fix truncated JSON by adding closing braces
                        # Count open vs close braces
                        open_braces = content_str.count('{')
                        close_braces = content_str.count('}')
                        missing_braces = open_braces - close_braces
                        
                        if missing_braces > 0:
                            fixed_json = content_str + ('}' * missing_braces)
                            try:
                                nested_json = json.loads(fixed_json)
                                if isinstance(nested_json, dict) and "answer" in nested_json:
                                    parsed_result = nested_json
                                    answer = nested_json["answer"]
                            except json.JSONDecodeError:
                                # Try to find the longest valid JSON prefix
                                for i in range(len(content_str), 0, -1):
                                    try:
                                        nested_json = json.loads(content_str[:i])
                                        if isinstance(nested_json, dict) and "answer" in nested_json:
                                            parsed_result = nested_json
                                            answer = nested_json["answer"]
                                            break
                                    except json.JSONDecodeError:
                                        continue
                        else:
                            # No missing braces, try prefix extraction
                            for i in range(len(content_str), 0, -1):
                                try:
                                    nested_json = json.loads(content_str[:i])
                                    if isinstance(nested_json, dict) and "answer" in nested_json:
                                        parsed_result = nested_json
                                        answer = nested_json["answer"]
                                        break
                                except json.JSONDecodeError:
                                    continue
        
        # Ensure answer is properly formatted
        if isinstance(answer, dict):
            answer_content = answer
        else:
            # If answer is a string, create a simple paragraph section
            answer_content = {
                "sections": [{
                    "type": "paragraph",
                    "content": str(answer),
                    "citations": []
                }]
            }
        
        companies = parsed_result.get("companies", {})
        comparison = parsed_result.get("comparison", {})
        
        return {
            "answer": answer_content,
            "structured": {
                "companies": companies,
                "comparison": comparison,
                "confidence": parsed_result.get("confidence", "medium"),
                "missing_data": parsed_result.get("missing_data", [])
            }
        }
        
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: Try to repair and extract content from malformed JSON
        logger.warning(f"Failed to parse JSON from synthesizer: {e}")
        logger.error(f"Malformed JSON (first 500 chars): {raw_answer[:500]}")
        
        # Attempt 1: Try to fix common JSON errors (unterminated strings, missing quotes)
        try:
            # Add closing quotes and braces if missing
            repaired = raw_answer.rstrip()
            if not repaired.endswith('}'):
                # Count open braces
                open_braces = repaired.count('{') - repaired.count('}')
                repaired += '}' * open_braces
            
            parsed_result = json.loads(repaired)
            logger.info("✓ Successfully repaired malformed JSON")
            
            # Process the repaired JSON normally
            answer = parsed_result.get("answer", {})
            if isinstance(answer, dict):
                answer_content = answer
            else:
                answer_content = {
                    "sections": [{
                        "type": "paragraph",
                        "content": str(answer),
                        "citations": []
                    }]
                }
            
            companies = parsed_result.get("companies", {})
            comparison = parsed_result.get("comparison", {})
            
            return {
                "answer": answer_content,
                "structured": {
                    "companies": companies,
                    "comparison": comparison,
                    "confidence": parsed_result.get("confidence", "low"),
                    "missing_data": parsed_result.get("missing_data", [])
                }
            }
            
        except (json.JSONDecodeError, ValueError):
            logger.warning("Could not repair JSON, extracting readable text")
        
        # Attempt 2: Extract any readable content fields
        content_matches = re.findall(r'"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', raw_answer, re.DOTALL)
        if content_matches:
            # Combine all content fields found
            clean_content = "\n\n".join(content_matches[:3])  # Take first 3 content blocks
            logger.info(f"Extracted {len(content_matches)} content blocks from malformed JSON")
        else:
            # Last resort: generic error message
            clean_content = "I apologize, but I encountered an error processing the response. The LLM generated malformed JSON. Please try rephrasing your question or try again."
            logger.error(f"Could not extract any readable content from malformed JSON")
        
        return {
            "answer": {
                "sections": [{
                    "type": "paragraph",
                    "content": clean_content,
                    "citations": []
                }]
            },
            "structured": {}
        }


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

    # Step 2: Execute the plan to get context (returns dict by company)
    exec_start_time = time.time()
    chunks_by_company = execute_plan(plan)
    timings['2. Execution (Deterministic)'] = time.time() - exec_start_time
    
    # Step 3: Synthesize the final answer
    synth_start_time = time.time()
    final_answer = synthesize_answer(query, chunks_by_company)
    timings['3. Synthesis (Model Call)'] = time.time() - synth_start_time
    
    total_time = time.time() - total_start_time
    timings['Total Tool Time'] = total_time

    # Performance timings will be included in token_metrics JSON

    # Extract sources from all companies (flatten dict to list)
    all_chunks = []
    tickers = list(chunks_by_company.keys())
    for ticker, chunks in chunks_by_company.items():
        all_chunks.extend(chunks)

    # FILTER OUT HALLUCINATED COMPANIES
    # Only keep companies that were actually in the context (chunks_by_company)
    valid_tickers = set(tickers)
    structured_data = final_answer.get("structured", {})
    companies_data = structured_data.get("companies", {})
    
    # Remove companies that weren't in the original context
    hallucinated_companies = set(companies_data.keys()) - valid_tickers
    if hallucinated_companies:
        for hallucinated in hallucinated_companies:
            del companies_data[hallucinated]
    
    # If only 1 company remains, clear comparison data (shouldn't compare with itself)
    if len(companies_data) <= 1:
        comparison_data = structured_data.get("comparison", {})
        if comparison_data and any(comparison_data.values()):
            structured_data["comparison"] = {"summary": None, "winner": None, "metric": None}

    # Get filing URLs for all tickers (simple approach!)
    filing_urls = get_filing_urls_by_tickers(tickers)

    # Format the structured answer for UI presentation
    # The `final_answer` from `synthesize_answer` is already structured
    ui_ready_answer = format_answer_for_ui(final_answer, all_chunks)
    
    # Add filing URLs to metadata
    if 'metadata' not in ui_ready_answer:
        ui_ready_answer['metadata'] = {}
    ui_ready_answer['metadata']['filing_urls'] = filing_urls
    
    # Combine UI-ready answer and sources into a single payload
    result = {
        "answer": ui_ready_answer,
        "sources": [
            {
                "id": i,
                "section": chunk.get("section_full") or chunk.get("section", "Unknown"),
                "section_full": chunk.get("section_full"),
                "text": chunk.get("text", ""),
                "score": float(chunk.get("score", 0.0)),
                "ticker": str(chunk.get("ticker", "")),
                "filing_type": str(chunk.get("filing_type", "")),
                "report_date": str(chunk.get("report_date", "")),
                "document_url": chunk.get("document_url")  # SEC.gov URL for external link
            }
            for i, chunk in enumerate(all_chunks)
        ]
    }
    
    # Return the dict directly - supervisor will handle JSON serialization
    # Note: token_metrics are tracked separately by the API layer
    return result
