"""
Finance Agent CLI Client

A command-line interface for interacting with the Finance Agent API.
Provides an easy way to query financial data, manage filings, and monitor
the system without writing code or using curl.

Features:
--------
- **Natural Language Queries**: Ask questions about companies in plain English
- **Filing Management**: List, view, and process SEC filings
- **Health Monitoring**: Check API and service status
- **Rich Output**: Beautiful tables, panels, and formatted text
- **Error Handling**: Clear error messages and recovery suggestions

Commands:
--------
Query & Analysis:
  ask              Ask a question about a company
  
Company Management:
  list-companies   List all available companies
  filings          Show filings for a specific company
  process          Manually process a filing
  
System:
  health           Check API server health

Quick Start:
-----------
1. Start the API server:
   uvicorn app.api.main:app --reload

2. Ask a question:
   python -m app.cli.client ask "What were the revenues?" --ticker AAPL

3. Check health:
   python -m app.cli.client health

Examples:
--------
Basic query:
  $ python -m app.cli.client ask "What were Apple's revenues?" --ticker AAPL

Query specific section:
  $ python -m app.cli.client ask "What are the risks?" --ticker AAPL --section "Item 1A"

List companies:
  $ python -m app.cli.client list-companies

View filings:
  $ python -m app.cli.client filings AAPL

Process a filing:
  $ python -m app.cli.client process MSFT --filing-type 10-K

Force reprocess:
  $ python -m app.cli.client process AAPL --filing-type 10-K --force

Configuration:
-------------
API URL can be set via environment variable:
  export FINANCE_AGENT_API_URL=http://localhost:8000/api

Default: http://localhost:8000/api

Output:
------
The CLI uses Rich library for beautiful terminal output:
- Color-coded messages (green=success, red=error, yellow=warning)
- Formatted tables for data display
- Panels for answers
- Progress indicators for long operations

Error Handling:
--------------
The CLI provides clear error messages and suggestions:
- Connection errors: Reminds you to start the server
- Timeout errors: Suggests checking server logs
- HTTP errors: Shows detailed error messages from API

Requirements:
------------
- click: Command-line interface framework
- requests: HTTP client
- rich: Terminal formatting

See Also:
--------
- app.api.main: API server implementation
- API docs: http://localhost:8000/docs (when server running)
"""

import click
import requests
from typing import Optional
import json
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Initialize Rich console for pretty printing
console = Console()

# API base URL (configurable via environment variable)
API_BASE_URL = os.getenv("FINANCE_AGENT_API_URL", "http://localhost:8000/api")


@click.group()
def cli():
    """Finance Agent CLI - Ask questions about companies using SEC filings."""
    pass


@cli.command()
@click.argument('query')
@click.option('--ticker', required=True, help='Company ticker symbol (e.g., AAPL)')
@click.option('--filing-type', default='10-K', help='Type of filing (default: 10-K)')
@click.option('--section', help='Specific section to search (e.g., Item 7)')
@click.option('--top-k', default=5, help='Number of sources to retrieve')
@click.option('--threshold', default=0.5, help='Minimum similarity score (0-1, default: 0.5)')
@click.option('--show-sources/--no-sources', default=True, help='Show source documents')
def ask(query: str, ticker: str, filing_type: str, section: Optional[str], 
        top_k: int, threshold: float, show_sources: bool):
    """
    Ask a natural language question about a company's SEC filings.
    
    This command sends your question to the Finance Agent API, which:
    1. Fetches the filing from SEC if not already cached
    2. Searches for relevant sections using semantic search
    3. Generates an answer using an LLM with retrieved context
    4. Returns the answer with source citations
    
    The first query for a company may take 30-60 seconds as it fetches
    and processes the filing. Subsequent queries are much faster.
    
    Examples:
        Ask about revenues:
        $ python -m app.cli.client ask "What were the revenues?" --ticker AAPL
        
        Query specific section:
        $ python -m app.cli.client ask "What are the risks?" --ticker AAPL --section "Item 1A"
        
        Adjust retrieval parameters:
        $ python -m app.cli.client ask "Who are the executives?" --ticker MSFT --top-k 10 --threshold 0.6
    """
    # Validate ticker format
    ticker = ticker.upper().strip()
    if not ticker or len(ticker) > 5 or not ticker.isalpha():
        console.print("[bold red]Error:[/bold red] Invalid ticker format")
        console.print("Ticker should be 1-5 letters (e.g., AAPL, MSFT)")
        return
    
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")
    console.print(f"[bold cyan]Company:[/bold cyan] {ticker}")
    
    with console.status("[bold green]Fetching data and generating answer..."):
        try:
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={
                    "query": query,
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "section": section,
                    "top_k": top_k,
                    "score_threshold": threshold
                },
                timeout=120  # 2 minutes (fetching can take time)
            )
            
            response.raise_for_status()
            data = response.json()
        
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Error:[/bold red] Could not connect to API server")
            console.print("Make sure the server is running: uvicorn app.api.main:app --reload")
            return
        
        except requests.exceptions.Timeout:
            console.print("[bold red]Error:[/bold red] Request timed out")
            console.print("The filing might be large. Try again or check server logs.")
            return
        
        except requests.exceptions.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            try:
                if response.status_code == 500:
                    error_detail = response.json().get('detail', 'Unknown error')
                    console.print(f"Server error: {error_detail}")
                elif response.status_code == 404:
                    console.print(f"Filing not found for {ticker}")
            except json.JSONDecodeError:
                console.print("Could not parse error response")
            return
    
    # Display answer
    console.print("\n")
    answer_panel = Panel(
        data['answer'],
        title="[bold green]Answer",
        border_style="green"
    )
    console.print(answer_panel)
    
    # Display metadata
    console.print(f"\n[dim]Sources used: {data['num_sources']} | Processing time: {data['processing_time']:.2f}s[/dim]")
    
    # Display sources if requested
    if show_sources and data.get('sources'):
        console.print("\n[bold]Sources:[/bold]")
        
        for i, source in enumerate(data['sources'], 1):
            console.print(f"\n[cyan]  [{i}] {source['ticker']} - {source['filing_type']} ({source['report_date']})[/cyan]")
            console.print(f"      Section: {source['section']} | Score: {source['score']:.3f}")
            console.print(f"      {source['text']}")


@cli.command()
def list_companies():
    """
    List all companies available in the database.
    
    Shows a table with:
    - Ticker symbol
    - Company name
    - Number of filings available
    - Processing status
    
    Example:
        $ python -m app.cli.client list-companies
    """
    
    try:
        response = requests.get(f"{API_BASE_URL}/companies")
        response.raise_for_status()
        data = response.json()
    
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Error:[/bold red] Could not connect to API server")
        return
    
    if not data['companies']:
        console.print("[yellow]No companies found in database[/yellow]")
        return
    
    # Create table
    table = Table(title="Available Companies")
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Filings", justify="right")
    table.add_column("Status")
    
    for company in data['companies']:
        status = "✓ Ready" if company['num_filings'] > 0 else "No filings"
        table.add_row(
            company['ticker'],
            company['name'] or "N/A",
            str(company['num_filings']),
            status
        )
    
    console.print(table)


@cli.command()
@click.argument('ticker')
def filings(ticker: str):
    """
    List all SEC filings available for a specific company.
    
    Shows a table with:
    - Filing type (10-K, 10-Q, etc.)
    - Report date (fiscal period end)
    - Number of chunks created
    - Processing status (ready or processing)
    
    Example:
        $ python -m app.cli.client filings AAPL
        $ python -m app.cli.client filings MSFT
    
    Args:
        ticker: Company ticker symbol (e.g., AAPL, MSFT)
    """
    
    try:
        response = requests.get(f"{API_BASE_URL}/companies/{ticker}/filings")
        response.raise_for_status()
        data = response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[yellow]No filings found for {ticker}[/yellow]")
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        return
    
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Error:[/bold red] Could not connect to API server")
        return
    
    # Create table
    table = Table(title=f"Filings for {ticker}")
    table.add_column("Type", style="cyan")
    table.add_column("Report Date", style="green")
    table.add_column("Chunks", justify="right")
    table.add_column("Status")
    
    for filing in data['filings']:
        status = "✓ Ready" if filing['status'] == 'ready' else "⏳ Processing"
        table.add_row(
            filing['filing_type'],
            filing['report_date'],
            str(filing['num_chunks']),
            status
        )
    
    console.print(table)


@cli.command()
@click.argument('ticker')
@click.option('--filing-type', default='10-K', help='Type of filing (default: 10-K)')
@click.option('--force', is_flag=True, help='Force reprocess if already exists')
def process(ticker: str, filing_type: str, force: bool):
    """
    Manually process a company's SEC filing.
    
    This command:
    1. Fetches the filing from SEC EDGAR
    2. Parses the HTML to extract sections and tables
    3. Chunks the document into searchable pieces
    4. Generates embeddings using BGE-large model
    5. Stores everything in Postgres and Qdrant
    
    Use this to pre-fetch filings before asking questions, or to
    update existing filings with the --force flag.
    
    Processing typically takes 30-60 seconds per filing.
    
    Examples:
        Process a 10-K:
        $ python -m app.cli.client process AAPL --filing-type 10-K
        
        Process a 10-Q:
        $ python -m app.cli.client process MSFT --filing-type 10-Q
        
        Force reprocess:
        $ python -m app.cli.client process AAPL --filing-type 10-K --force
    
    Args:
        ticker: Company ticker symbol (e.g., AAPL, MSFT)
        filing_type: SEC filing type (10-K, 10-Q, 8-K, etc.)
        force: Force reprocessing even if filing already exists
    """
    console.print(f"\n[bold cyan]Processing {ticker} {filing_type}...[/bold cyan]")
    
    with console.status("[bold green]Fetching from SEC and processing..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/companies/{ticker}/process",
                json={
                    "filing_type": filing_type,
                    "force_reprocess": force
                },
                timeout=300  # 5 minutes
            )
            
            response.raise_for_status()
            data = response.json()
        
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Error:[/bold red] Could not connect to API server")
            return
        
        except requests.exceptions.Timeout:
            console.print("[bold red]Error:[/bold red] Request timed out")
            return
        
        except requests.exceptions.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            return
    
    # Display result
    if data['status'] == 'success':
        console.print(f"\n[bold green]✓ Success![/bold green]")
        console.print(f"Created {data['chunks_created']} chunks")
        console.print(f"Generated {data['embeddings_generated']} embeddings")
    
    elif data['status'] == 'already_exists':
        console.print(f"\n[yellow]Filing already exists[/yellow]")
        console.print(f"Use --force to reprocess")
    
    else:
        console.print(f"\n[bold red]Error:[/bold red] {data['message']}")


@cli.command()
def health():
    """
    Check the health status of the API server and all services.
    
    Verifies connectivity to:
    - PostgreSQL database
    - Qdrant vector store
    - Ollama LLM service
    
    Returns a table showing the status of each service.
    
    Example:
        $ python -m app.cli.client health
    
    Status values:
        - connected: Service is healthy
        - error: Service is unavailable
    """
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        console.print("\n[bold green]✓ Server is healthy[/bold green]")
        console.print(f"Status: {data['status']}")
        
        # Show services status
        table = Table(title="Services Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        
        for service, status in data['services'].items():
            table.add_row(service, status)
        
        console.print(table)
    
    except requests.exceptions.ConnectionError:
        console.print("[bold red]✗ Server is not running[/bold red]")
        console.print("Start it with: uvicorn app.api.main:app --reload")


if __name__ == '__main__':
    cli()