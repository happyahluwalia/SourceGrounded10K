"""
Finance Agent FastAPI Application

A production-ready REST API for AI-powered financial analysis using SEC filings.
This application provides endpoints for querying financial data, managing filings,
and performing semantic search over SEC documents using RAG (Retrieval Augmented Generation).

Architecture:
------------
The API follows a layered architecture:
1. **API Layer** (this file): FastAPI endpoints and request/response models
2. **Service Layer**: Business logic (FilingService, RAGChain, VectorStore)
3. **Data Layer**: Database (Postgres) and Vector Store (Qdrant)

Key Features:
------------
- **Semantic Search**: Ask natural language questions about companies
- **Lazy Loading**: Automatically fetches missing filings from SEC EDGAR
- **RAG Pipeline**: Combines retrieval with LLM generation for accurate answers
- **Health Monitoring**: Real-time service health checks
- **CORS Support**: Ready for web UI integration

API Endpoints:
-------------
Query & Analysis:
  POST   /api/query                        Ask questions about companies
  
Company Management:
  GET    /api/companies                    List all available companies
  GET    /api/companies/{ticker}/filings   Get filings for a company
  POST   /api/companies/{ticker}/process   Manually process a filing
  
System:
  GET    /api/health                       Health check with service status

Request Flow Example:
--------------------
1. Client sends question: "What were Apple's revenues?"
2. API checks if AAPL 10-K exists in database
3. If missing, fetches from SEC and processes (30-60s)
4. Runs semantic search to find relevant chunks
5. Passes chunks to LLM for answer generation
6. Returns answer with source citations

Technology Stack:
----------------
- **Framework**: FastAPI 0.119+ (async, type hints, auto docs)
- **Database**: PostgreSQL (filing metadata, chunks)
- **Vector DB**: Qdrant (embeddings for semantic search)
- **LLM**: Ollama (local inference, gemma3:1b)
- **Embeddings**: BGE-large-en-v1.5 (1024-dim vectors)

Configuration:
-------------
All settings are loaded from environment variables via app.core.config.
Required variables:
- DATABASE_URL: PostgreSQL connection string
- SEC_USER_AGENT: Email for SEC API compliance

Optional variables (have defaults):
- QDRANT_HOST, QDRANT_PORT: Qdrant connection
- OLLAMA_BASE_URL: Ollama API endpoint
- REDIS_HOST, REDIS_PORT: Redis cache

Running the Application:
-----------------------
Development:
    python -m app.api.main
    # or
    uvicorn app.api.main:app --reload

Production:
    uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4

Docker:
    docker-compose up

API Documentation:
-----------------
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

Error Handling:
--------------
All endpoints follow consistent error responses:
- 200: Success
- 404: Resource not found
- 500: Internal server error
- 503: Service unavailable (health check failed)

Errors include detailed messages in the response body.

Performance Considerations:
--------------------------
- First query for a company: 30-60s (fetches filing)
- Subsequent queries: 1-3s (cached in vector DB)
- Health checks: <100ms
- Concurrent requests: Supported (async endpoints)

Security Notes:
--------------
- CORS: Currently allows all origins (change for production)
- Rate limiting: Not implemented (add for production)
- Authentication: Not implemented (add for production)
- Input validation: Pydantic models validate all inputs

Monitoring:
----------
- Logs: Structured logging to stdout
- Health: /api/health endpoint checks all services
- Metrics: Not implemented (add Prometheus for production)

See Also:
--------
- app.services.rag_chain: RAG implementation
- app.services.filing_service: Filing processing pipeline
- app.services.vector_store: Qdrant operations
- app.core.config: Configuration management
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from sqlalchemy import text
import requests
import json
import asyncio
import queue
import re

from app.services.vector_store import VectorStore
from app.services.rag_chain import RAGChain
from app.services.filing_service import FilingService
from app.services.storage import DatabaseStorage
from app.services.log_streamer import subscribe_to_logs, unsubscribe_from_logs, get_log_stream_handler
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress noisy HTTP request logs (only show warnings/errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)

# Initialize log streaming handler
get_log_stream_handler()

# ============================================================================
# Initialize Services (before app creation)
# ============================================================================

db_storage = DatabaseStorage()
vector_store = VectorStore()
rag_chain = RAGChain(vector_store=vector_store)
filing_service = FilingService(
    db_storage=db_storage,
    vector_store=vector_store
)


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event() decorators.
    Code before yield runs on startup, code after runs on shutdown.
    """
    # Startup
    logger.info("Starting Finance Agent API...")
    # Mask sensitive database URL (hide password)
    db_host = settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else 'configured'
    logger.info(f"Database: {db_host}")
    logger.info(f"Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"Ollama: {settings.ollama_base_url}")
    logger.info(f"Debug logs streaming: {'enabled' if settings.enable_debug_logs else 'disabled'}")
    
    # Verify critical services
    try:
        from app.models.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection verified")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise
    
    try:
        vector_store.client.get_collections()
        logger.info("✓ Qdrant connection verified")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        raise
    
    logger.info("Services initialized successfully")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Finance Agent API...")
    logger.info("Cleanup complete")


# ============================================================================
# Initialize FastAPI App
# ============================================================================

app = FastAPI(
    title="Finance Agent API",
    description="AI-powered financial analysis using SEC filings",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan instead of deprecated on_event
)

# Add CORS middleware
# Configure via CORS_ORIGINS environment variable
# Examples: 
#   Development: CORS_ORIGINS=*
#   Production: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for /api/query endpoint."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Question to ask about the company")
    ticker: str = Field(..., min_length=1, max_length=10, description="Company ticker symbol (e.g., AAPL)")
    filing_type: str = Field(default="10-K", description="Type of SEC filing")
    section: Optional[str] = Field(None, description="Specific section to search (e.g., 'Item 7')")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        """Validate ticker is alphanumeric and uppercase."""
        v = v.upper().strip()
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Ticker must be 1-10 uppercase letters')
        return v
    
    @validator('query')
    def validate_query(cls, v):
        """Sanitize query to prevent SQL injection."""
        v = v.strip()
        # Check for dangerous SQL keywords (as whole words, not substrings)
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'EXEC', 'UNION', '--', ';', '/*', '*/']
        v_upper = v.upper()
        for word in dangerous:
            # Use word boundaries for alphanumeric keywords, exact match for symbols
            if word.isalnum():
                # Match as whole word (e.g., "EXEC" but not "EXECUTIVES")
                if re.search(r'\b' + re.escape(word) + r'\b', v_upper):
                    raise ValueError(f'Query contains forbidden keyword: {word}')
            else:
                # For symbols like '--', ';', '/*', '*/': exact substring match
                if word in v_upper:
                    raise ValueError(f'Query contains forbidden keyword: {word}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What were the total revenues in 2024?",
                "ticker": "AAPL",
                "filing_type": "10-K",
                "top_k": 5,
                "score_threshold": 0.5
            }
        }


class QueryResponse(BaseModel):
    """Response model for /api/query endpoint."""
    
    query: str
    answer: str
    ticker: str
    num_sources: int
    processing_time: float
    sources: Optional[List[dict]] = None


class ProcessFilingRequest(BaseModel):
    """Request model for /api/companies/{ticker}/process endpoint."""
    
    filing_type: str = Field(default="10-K", description="Type of filing to process")
    force_reprocess: bool = Field(default=False, description="Force reprocess if already exists")


class FilingInfo(BaseModel):
    """Filing information model."""
    
    filing_id: str
    ticker: str
    filing_type: str
    report_date: str
    num_chunks: int
    status: str


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint - verifies all service connections.
    
    Checks:
    - PostgreSQL database connectivity
    - Qdrant vector store connectivity  
    - Ollama LLM service availability
    
    Returns:
        Dict with overall status and individual service statuses
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check PostgreSQL
    try:
        from app.models.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Qdrant
    try:
        vector_store.client.get_collections()
        health_status["services"]["vector_store"] = "connected"
    except Exception as e:
        health_status["services"]["vector_store"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Ollama
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            health_status["services"]["llm"] = "connected"
        else:
            health_status["services"]["llm"] = f"error: status {response.status_code}"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["llm"] = f"error: {str(e)}"
        health_status["status"] = "degraded"  # LLM is optional, so degraded not unhealthy
    
    return health_status


@app.post("/api/query", response_model=QueryResponse)
async def query_company(request: QueryRequest):
    """
    Ask a question about a company.
    
    This endpoint:
    1. Checks if the filing exists locally
    2. Fetches and processes it if missing (lazy loading)
    3. Runs RAG chain to answer the question
    4. Returns answer with sources
    
    Example:
        POST /api/query
        {
            "query": "What were Apple's revenues?",
            "ticker": "AAPL",
            "filing_type": "10-K"
        }
    """
    try:
        # Log delimiter for new query
        logger.info("=" * 80)
        logger.info(f"🔍 NEW QUERY: {request.ticker} - {request.query[:50]}...")
        logger.info("=" * 80)
        
        # Step 1: Ensure filing exists (fetch if missing)
        filing_result = filing_service.get_or_process_filing(
            ticker=request.ticker,
            filing_type=request.filing_type
        )
        
        if filing_result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=filing_result['message']
            )
        
        # Log if we had to fetch the filing
        if filing_result['status'] == 'success':
            logger.info(f"Fetched and processed {request.ticker} {request.filing_type}")
        
        # Step 2: Run RAG chain
        response = rag_chain.answer(
            query=request.query,
            ticker=request.ticker,
            section=request.section,
            filing_type=request.filing_type,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            include_sources=True
        )
        
        # Step 3: Format response
        return QueryResponse(
            query=request.query,
            answer=response['answer'],
            ticker=request.ticker,
            num_sources=response['num_sources'],
            processing_time=response['processing_time'],
            sources=response.get('sources', [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/companies")
async def list_companies():
    """
    List all companies in the database.
    
    Returns:
        List of companies with their available filings
    """
    try:
        with db_storage.get_session() as session:
            from app.models.database import Company, SECFiling
            
            companies = session.query(Company).all()
            
            result = []
            for company in companies:
                filings = session.query(SECFiling).filter(
                    SECFiling.ticker == company.ticker
                ).all()
                
                result.append({
                    "ticker": company.ticker,
                    "name": company.name,
                    "sector": company.sector,
                    "num_filings": len(filings),
                    "filings": [
                        {
                            "filing_type": f.filing_type,
                            "report_date": f.report_date.isoformat(),
                            "status": "ready" if f.embeddings_generated else "processing"
                        }
                        for f in filings
                    ]
                })
            
            return {"companies": result}
    
    except Exception as e:
        logger.error(f"Error listing companies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing companies: {str(e)}"
        )


@app.get("/api/companies/{ticker}/filings")
async def get_company_filings(ticker: str):
    """
    Get all filings for a specific company.
    
    Args:
        ticker: Company ticker symbol
    
    Returns:
        List of filings with metadata
    """
    try:
        ticker = ticker.upper()
        
        with db_storage.get_session() as session:
            from app.models.database import SECFiling
            
            filings = session.query(SECFiling).filter(
                SECFiling.ticker == ticker
            ).order_by(SECFiling.report_date.desc()).all()
            
            if not filings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No filings found for {ticker}"
                )
            
            return {
                "ticker": ticker,
                "filings": [
                    {
                        "filing_id": str(f.id),
                        "filing_type": f.filing_type,
                        "report_date": f.report_date.isoformat(),
                        "filing_date": f.filing_date.isoformat() if f.filing_date else None,
                        "num_chunks": f.num_chunks,
                        "status": "ready" if f.embeddings_generated else "processing"
                    }
                    for f in filings
                ]
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting filings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting filings: {str(e)}"
        )


@app.post("/api/companies/{ticker}/process")
async def process_company_filing(ticker: str, request: ProcessFilingRequest):
    """
    Manually trigger processing of a company's filing.
    
    Use this to pre-fetch filings before they're needed for queries.
    
    Args:
        ticker: Company ticker symbol
        request: Processing options
    
    Returns:
        Processing result
    """
    try:
        ticker = ticker.upper()
        
        logger.info(f"Manual processing request: {ticker} {request.filing_type}")
        
        result = filing_service.process_filing(
            ticker=ticker,
            filing_type=request.filing_type,
            force_reprocess=request.force_reprocess
        )
        
        if result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing filing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing filing: {str(e)}"
        )


@app.get("/api/logs/stream")
async def stream_logs(session_id: Optional[str] = None):
    """
    Server-Sent Events endpoint for real-time log streaming.
    
    This endpoint streams application logs to connected clients in real-time.
    Perfect for the debug panel in the frontend to show actual backend logs.
    
    Can be disabled via ENABLE_DEBUG_LOGS=False environment variable.
    
    Query Parameters:
        session_id: Optional session ID to filter logs for a specific session.
                   If not provided, shows all application logs (useful for monitoring).
    
    Usage:
        // All logs (monitoring mode)
        const eventSource = new EventSource('/api/logs/stream');
        
        // Session-specific logs
        const eventSource = new EventSource('/api/logs/stream?session_id=abc123');
        
        eventSource.onmessage = (event) => {
            const log = JSON.parse(event.data);
            console.log(log);
        };
    """
    # Check if debug logs are enabled
    if not settings.enable_debug_logs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug log streaming is disabled. Set ENABLE_DEBUG_LOGS=True to enable."
        )
    async def event_generator():
        log_queue = subscribe_to_logs()
        
        # Log to backend
        logger.info("New log stream client connected")
        
        try:
            # Send initial connection message
            mode = "session-specific" if session_id else "global monitoring"
            initial_msg = {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'logger': 'log_stream',
                'message': f'🔌 Connected to real-time log stream ({mode})'
            }
            yield f"data: {json.dumps(initial_msg)}\n\n"
            
            # Send a test log to verify streaming works
            test_msg = {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'logger': 'log_stream',
                'message': '✅ Log streaming is active - ask a question to see the RAG pipeline!'
            }
            yield f"data: {json.dumps(test_msg)}\n\n"
            
            keepalive_counter = 0
            while True:
                try:
                    # Check queue without blocking - check multiple times per iteration
                    has_logs = False
                    for _ in range(10):  # Check up to 10 times per iteration
                        try:
                            log_entry = log_queue.get_nowait()
                            # Format as SSE and yield immediately
                            yield f"data: {json.dumps(log_entry)}\n\n"
                            has_logs = True
                        except queue.Empty:
                            break
                    
                    if not has_logs:
                        # No logs available, sleep briefly
                        await asyncio.sleep(0.1)  # Check every 100ms for responsiveness
                        keepalive_counter += 1
                        # Send keepalive every 300 iterations (30 seconds)
                        if keepalive_counter >= 300:
                            yield f": keepalive\n\n"
                            keepalive_counter = 0
                    
                except GeneratorExit:
                    # Client disconnected
                    logger.info("Log stream client disconnected")
                    break
                    
                except Exception as e:
                    logger.error(f"Error in log stream: {e}", exc_info=True)
                    break
        finally:
            unsubscribe_from_logs(log_queue)
            logger.info("Log stream client cleanup complete")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )