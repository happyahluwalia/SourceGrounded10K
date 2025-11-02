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
- app.tools.annual_financial_report_tool: Filing processing pipeline
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
import uuid

from app.services.vector_store import VectorStore
from app.services.log_streamer import subscribe_to_logs, unsubscribe_from_logs, get_log_stream_handler
from app.agents.supervisor import SupervisorAgent


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

# All services are now encapsulated within the SupervisorAgent and its tools.
# We only need to instantiate the SupervisorAgent here.
supervisor = SupervisorAgent()


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
        VectorStore().client.get_collections()
        logger.info("✓ Qdrant connection verified")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        raise
    
    # Initialize checkpointer for conversation persistence
    try:
        await SupervisorAgent.initialize_checkpointer()
        logger.info("✓ Checkpointer initialized")
    except Exception as e:
        logger.error(f"✗ Checkpointer initialization failed: {e}")
        raise
    
    logger.info("Services initialized successfully")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Finance Agent API...")
    
    # Cleanup checkpointer resources
    try:
        await SupervisorAgent.cleanup_checkpointer()
    except Exception as e:
        logger.error(f"✗ Checkpointer cleanup failed: {e}", exc_info=True)
    
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

class ChatRequest(BaseModel):
    """Request model for /api/v2/chat endpoint."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language question about company financials")
    user_id: Optional[str] = Field(None, description="Optional user ID for session management")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation history")


class ChatResponse(BaseModel):
    """Response model for /api/v2/chat endpoint."""
    
    query: str
    answer: str
    session_id: str = Field(..., description="Session ID for conversation continuity")
    metadata: Optional[dict] = None




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
        VectorStore().client.get_collections()
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


@app.post("/api/v2/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Natural language chat endpoint for the v2 Supervisor Agent.

    This is the main endpoint for the agentic architecture. The supervisor
    analyzes the query and delegates to appropriate specialist tools.
    
    Supports conversation continuity through session_id:
    - Frontend should store session_id in localStorage
    - Send same session_id for follow-up questions
    - Omit session_id to start a new conversation
    
    Example:
        POST /api/v2/chat
        {
            "query": "What are the risks of investing in Apple?",
            "session_id": "abc-123-def"  // Optional, for conversation history
        }
    
    Response includes session_id for frontend to persist.
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🔍 NEW QUERY: {request.query[:100]}...")
        if request.session_id:
            logger.info(f"📝 Session ID: {request.session_id}")
        logger.info("=" * 80)
        
        # Process query with checkpointing
        result = await supervisor.ainvoke(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id  # Can be None, will be generated
        )
        
        return {
            "query": result['query'],
            "answer": result['answer'],
            "session_id": result['session_id']  # Return for frontend to store
        }
    except RuntimeError as e:
        # Checkpointer not initialized
        logger.error(f"Checkpointer error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation persistence service unavailable"
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
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