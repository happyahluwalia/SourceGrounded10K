"""
    Retrieval Augmented Generation (RAG) Chain

    Combines semantic search with LLM Generation to answer questions about financial documents

    Pipeline:
    1. Query -> Semantic Search in Vector DB -> Retrieve relevant chunks
    2. Take Chunks -> Format context -> Build a prompt
    3. Take Prompt -> Feed to LLM -> Generate Answer
    4. Take Answer -> Add citations -> Return to User

"""

from typing import List, Dict, Optional
import logging
from datetime import datetime
from langchain_core.tools import tool
from app.services.vector_store import VectorStore
from app.core.config import settings 

logger = logging.getLogger(__name__)

# Suppress noisy HTTP logs from this module
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class RAGSearchTool:
    """
        RAG Search Tool for financial document Q&A

        Answers questions by:
        1. Finding relevant chunks via semantic search
        2. Passing chunks as context to llm
        3. Generating grounded answers with citations
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client = None,      # initially use Ollama Client
        model_name: str = None,
        db_storage = None,      # For checking if filing exists
        data_prep_tool = None   # For auto-downloading missing filings
    ):

        """
            Initialize RAG Chain

            Args:
                vector_store : Vector Store instance for retrieval
                llm_ client : Ollama client
                model_name : LLM model to use
        
        """

        self.vector_store = vector_store
        self.model_name = model_name or settings.synthesizer_model
        self.db_storage = db_storage
        self.data_prep_tool = data_prep_tool

        if llm_client is None:
                try:
                    import ollama
                    # Initialize client with explicit host from settings
                    self.llm_client = ollama.Client(host=settings.ollama_base_url)
                    logger.info(f"Initialized Ollama client at {settings.ollama_base_url} with model: {self.model_name}")
                except ImportError:
                    self.llm_client = None
                    raise ImportError("Please install ollama to use Ollama client")
        else:
            self.llm_client = llm_client
        

    def retrieve(
        self,
        query: str,
        ticker: Optional[str] = None,
        section: Optional[str]= None,
        filing_type: Optional[str] = None,
        top_k: int = None,
        score_threshold: float = None
    )-> List[Dict]:
        """
            Retrieve relevant chunks for query.

            Args:
                query: User's query
                ticker: Filter by company ticker
                section: Filter by section
                filing_type: Filter by filing type
                top_k: Number of chunks to retrieve
                score_threshold: Minimum similarity score (0-1)

            Returns:
                List of retrieved chunks
        """

        # Use settings if not provided
        top_k = top_k or settings.top_k
        score_threshold = score_threshold or settings.score_threshold
        
        logger.info(f"Retrieving chunks for query: {query[:100]}...")

        results = self.vector_store.search(
            query = query,
            ticker = ticker,
            section = section,
            filing_type = filing_type,
            limit = top_k,
        )

        # Filter by score threshold
        filtered_results = [
            r for r in results
            if r['score'] >= score_threshold
        ]
        logger.info(
            f"Retrieved {len(results)} chunks, "
            f"{len(filtered_results)} above threshold {score_threshold}"
        )
        
        return filtered_results
    
    def build_context(self, chunks: List[Dict]) -> str:
        """
            Build context string from retrieved chunks
            Format:
                Context from SEC Filing
                [Document 1]
                Company: AAPL
                Filing: 10-k (2024-09-30)
                Section: Item 7
                <chunk_text>

                [Document 2]
                ...

            Args:
                chunks: Retrieved chunks with metada
            
            Returns:
                Formatted context string
        """
        if not chunks:
            return "No relevant information found in database"
        
        context_parts = ["Context from SEC Filings: \n"]

        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"\n[Document {i}]")
            context_parts.append(f"Company: {chunk.get('ticker', 'Unknown')}")
            context_parts.append(f"Filing: {chunk.get('filing_type', 'Unknown')} ({chunk.get('report_date', 'Unknown')})")
            context_parts.append(f"Section: {chunk.get('section', 'Unknown')}")
            context_parts.append(f"Relevance Score: {chunk.get('score',0):.2f}")
            context_parts.append(f"\n{chunk['text']}")
            context_parts.append("-"*10)
        
        return "\n".join(context_parts)

    def build_prompt(self, query: str, context: str) -> str:
        """
        Build LLM prompt with query and context from an external file.
        """
        try:
            from pathlib import Path
            prompt_path = Path(__file__).parent.parent / "prompts" / "synthesizer.txt"
            prompt_template = prompt_path.read_text()
        except FileNotFoundError:
            print("ERROR: Synthesizer prompt file not found. Using fallback prompt.")
            prompt_template = """As a financial analyst, answer the following question using ONLY the provided SEC filing context.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"""
        
        return prompt_template.format(context=context, query=query)

    def generate(self, prompt:str, max_tokens: int = None) -> str:
        """
            Generate answer using LLM

            Args:
                prompt: Complete prompt with context
                max_tokens: Maximum tokens in response
            
            Returns:
                Generated answer
        """
        if self.llm_client is None:
            logger.error("LLM client not initialized")
            return "Error: LLM client not initialized. Please install Ollama"
        
        try:
            # Use settings if not provided
            max_tokens = max_tokens or settings.max_tokens
            
            logger.info(f" Generating answer with {self.model_name}...")

            # Call Ollama
            response = self.llm_client.generate(
                model = self.model_name,
                prompt = prompt,
                options = {
                    "num_predict": max_tokens,
                    "temperature": 0.1,          # Low temperature for factual answers
                }
            )
            answer = response['response'].strip()
            logger.info(f"Generated answer ({len(answer)} chars)")

            return answer
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error: Unable to generate answer. {str(e)}"


    def answer(
        self,
        query: str,
        ticker: Optional[str] = None,
        section: Optional[str] = None,
        filing_type: Optional[str] = None,
        top_k: int = None,
        score_threshold: float = None,
        include_sources:bool = True
    )-> Dict:
        """
            Complete RAG pipeline starting from query, to retrieving chunks from vector db
            to creating context, build the prompt, generate answer and finally return with citations

            Args:
                query: User's question
                ticker: Filter by company ticker
                section: Filter by section
                filing_type: Filter by filing type
                top_k: Number of chunks to retrieve
                score_threshold: Minimum similarity score (0-1)
                include_sources: Include source citations in answer

            Returns:
                Dict with answer and metadata:
                {
                    "query": "What were Apple's revenues?",
                    "answer": "Apple's total net sales...",
                    "sources": [...],  # Retrieved chunks
                    "num_sources": 3,
                    "tokens_used": 450,
                    "timestamp": "2024-01-15T10:30:00"
                }
        """
        start_time = datetime.now()

        logger.info(f" Processing query: {query[:100]}...")

        # Step 0: Auto-download filing if missing (only if ticker provided)
        if ticker and self.db_storage and self.data_prep_tool:
            filing_type = filing_type or "10-K"
            
            # Check if any filing exists for this ticker/type
            from app.models.database import SECFiling
            session = self.db_storage._get_session()
            filing = session.query(SECFiling).filter_by(
                ticker=ticker,
                filing_type=filing_type
            ).first()
            
            if not filing:
                logger.info(f"📥 Filing not found for {ticker} {filing_type}, downloading from EDGAR...")
                result = self.data_prep_tool.get_or_process_filing(ticker, filing_type)
                if result['status'] in ['success', 'exists']:
                    logger.info(f"✅ Filing ready for {ticker}")
                else:
                    logger.warning(f"⚠️ Failed to download {ticker}: {result.get('message')}")

        # Step 1: Retrieve relevant chunks
        chunks = self.retrieve(
            query= query,
            ticker= ticker,
            section=section,
            filing_type = filing_type,
            top_k = top_k,
            score_threshold = score_threshold
        )

        if not chunks:
            return {
                "query":query,
                "answer": (
                    "I couldn't find relevant information to answer your question. "
                    "Try:\n"
                    "- Making your query more specific\n"
                    "- Checking if the company/filing is in the database\n"
                    "- Lowering the score threshold"
                ),
                "sources": [],
                "num_sources": 0,
                "timestamp": datetime.now().isoformat(),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }

            # Step 2 build the context
        context= self.build_context(chunks)

        # Step 3: Build the prompt
        prompt = self.build_prompt(query, context)

        # Step 4: Generate Answer
        answer = self.generate(prompt)

        # Step 5: Format Answer
        response = {
            "query":query,
            "answer":answer,
            "num_sources" : len(chunks),
            "timestamp":datetime.now().isoformat(),
            "processing_time":(datetime.now()-start_time).total_seconds(),
        }

        # Optionally include sources
        if include_sources:
            response["sources"] = [
                {
                    "ticker": chunk.get('ticker'),
                    "filing_type": chunk.get('filing_type'),
                    "report_date": chunk.get('report_date'),
                    "section": chunk.get('section'),
                    "score": chunk.get('score'),
                    "text": chunk.get('text')[:200] + "..."  # Preview only
                }
                for chunk in chunks
            ]
        
        logger.info(
            f"Completed in {response['processing_time']:.2f}s "
            f"using {response['num_sources']} sources"
        )
        logger.info("=" * 80)
        logger.info("✅ QUERY COMPLETED")
        logger.info("=" * 80)
        
        return response
