"""
Vector store service using Qdrant for semantic search.

This module provides the "brain" for finding relevant financial information:
- Converts text to embeddings (semantic vectors) using transformer models
- Stores embeddings in Qdrant vector database
- Performs similarity search to find relevant chunks

Key Concepts:
- Embedding: Converting text to a 1024-dimensional vector that captures meaning
- Similarity: Vectors close together = similar meaning (cosine similarity)
- Metadata filtering: Like SQL WHERE clauses but applied before vector search

Architecture:
- Postgres: Stores chunk metadata (filing_id, section, etc.)
- Qdrant: Stores embeddings + metadata for fast similarity search
- UUID: Links chunks between both databases
"""

# Standard library imports
from typing import List, Dict, Optional
from uuid import UUID
import logging

# Qdrant client and models for vector database operations
from qdrant_client import QdrantClient
from qdrant_client.models import (
   Distance,        # Similarity metric (cosine, dot, euclidean)
   VectorParams,    # Vector configuration (dimensions, metric)
   PointStruct,     # Individual Vector + metadata (like a row in SQL)
   Filter,          # Metadata filters (like WHERE clauses)
   FieldCondition,  # Individual filter conditions (like ticker='AAPL')
   MatchValue,      # Exact Match filter
   Range,           # Range filter (dates, numbers)
)

# Ollama client for embeddings
import ollama

# Import settings for configuration
from app.core.config import settings

logger = logging.getLogger(__name__)

# Suppress noisy HTTP logs from this module
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class VectorStore:
    """
        Manages vector embeddings and similarity search
        
        Think of this as a specialized database for "finding similar things"
        While Postgres finds exact matches (WHERE ticker = 'AAPL'),
        Qdrant finds similar meanings (WHERE meaning ~ 'company earnings')

    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None
    ):
        """
            Initialize connection to Qdrant and configure embedding model.

            Args:
                host: Qdrant server address (default: from settings)
                port: Qdrant server port (default: from settings)
                collection_name: Collection name (default: from settings)

        """
        # Use settings if not provided
        host = host or settings.qdrant_host
        port = port or settings.qdrant_port
        collection_name = collection_name or settings.qdrant_collection_name

        # Connect to Qdrant vector database
        # This is like connecting to Postgres, but for vectors
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

        # Configure embedding model from settings
        # nomic-embed-text-v1.5 via Ollama:
        # - 768-dimensional vectors (vs BGE's 1024)
        # - 8K context window (vs BGE's 512 tokens)
        # - Better for long financial documents
        self.embedding_model = settings.embedding_model
        self.vector_size = settings.embedding_dimension
        
        # Initialize Ollama client
        # Parse base URL to get host for Ollama client
        ollama_host = settings.ollama_base_url
        self.ollama_client = ollama.Client(host=ollama_host)
        
        logger.info(f"✓ Using embedding model: {self.embedding_model}")
        logger.info(f"✓ Embedding dimension: {self.vector_size}")

    def create_collection(self, recreate: bool = False) -> None:
        """
            Create a collection (like CREATE TABLE for postgress)

            This setups up:
            1. Vector dimensions (1024 for bge-large-en-v1.5)
            2. Similarity metric (Cosine measures angle between vectors)
            3. Index type (HNSW - Fase approximate search)

            Args:
                recreate: If True, delete existing collection first
        """

        # Check if collection already exists
        # Like checking if a table exists in Postgres
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists:
            if recreate:
                # Drop and recreate (useful for testing or schema changes)
                logger.info(f"Deleteing existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            else:
                # Collection already exists, skip creation
                logger.info(f" Collection alread exists: {self.collection_name}")
                return
        
        logger.info(f" Creating collection: {self.collection_name}")

        # Create collection with vector configuration
        # This is like CREATE TABLE but for vectors
        self.client.create_collection(
            collection_name = self.collection_name,
            vectors_config = VectorParams(
                size = self.vector_size,        # 1024 dimensions (must match model)
                distance = Distance.COSINE,     # Cosine similarity (measures angle between vectors)
                # HNSW (Hierarchical Navigable Small World) index:
                # - Fast approximate nearest neighbor search
                # - Trade-off: speed vs accuracy
                # - m: connections per node (16 = good default)
                # - ef_construct: build-time accuracy (100 = good default)
                # Higher values = better recall, slower build/search
            )
        )

        logger.info(f"Collection created with {self.vector_size}-dim vectors")

    def embed_texts(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """
            Converts text to embedding vectors using Ollama.
            This is where the magic happens:
            Input: ["Revenue increased 15%", "Net income rose"]
            Output: [[0.23, -0.45, ...], [0.19, -0.41, ...]]

            The model encodes semantic meaning into numbers
            Similar texts -> similar vectors

            Args:
                texts: List of text chunks to embed
                batch_size: Process N texts at once (currently processes sequentially)

            Returns:
                List of embedding vectors (each vector = 768 floats for nomic)
        """

        # Use settings if not provided
        batch_size = batch_size or settings.embedding_batch_size
        
        logger.info(f"Embedding {len(texts)} texts using {self.embedding_model}...")

        embeddings = []
        
        # Process texts (Ollama embeddings API processes one at a time)
        for i, text in enumerate(texts):
            if i % 50 == 0 and i > 0:
                logger.info(f"  Embedded {i}/{len(texts)} texts...")
            
            try:
                # Call Ollama embeddings API
                response = self.ollama_client.embeddings(
                    model=self.embedding_model,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for model not found error (404)
                if "not found" in error_msg or "404" in error_msg:
                    logger.error(
                        f"Embedding model '{self.embedding_model}' not found. "
                        f"Please run: ollama pull {self.embedding_model}"
                    )
                    raise RuntimeError(
                        f"Embedding model '{self.embedding_model}' not available. "
                        f"Run: ollama pull {self.embedding_model}"
                    ) from e
                
                # Other errors - log and fail fast
                logger.error(f"Error embedding text {i}: {e}")
                raise RuntimeError(f"Embedding failed for text {i}: {e}") from e
        
        logger.info(f"✓ Embedded {len(texts)} texts")
        return embeddings


    def _normalize_section_name(self, section: str) -> str:
        """
        Normalize section names for consistent filtering.

        Examples:
            "Item 7: Management's Discussion..." → "Item 7"
            "Item 1A: Risk Factors" → "Item 1A"
            "Item 8 - Financial Statements" → "Item 8"

        Args:
            section: Original section name from SEC filing

        Returns:
            Normalized section name (e.g., "Item 7")
        """
        import re
        
        # Extract "Item X" or "Item XA" pattern
        match = re.match(r'(Item\s+\d+[A-Z]?)', section, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # If no "Item X" pattern, return first part before colon/dash
        if ':' in section:
            return section.split(':')[0].strip()
        elif '-' in section:
            return section.split('-')[0].strip()
        
        # Fallback: return as-is
        return section


    def add_chunks(
    self, 
    chunks: List[Dict],
    batch_size: int = None
    ) -> None:
        """
        Add chunks with embeddings to Qdrant.
        
        Deduplicates automatically - skips chunks already in Qdrant.
        
        Process:
        1. Check which chunk IDs already exist in Qdrant
        2. Filter to only new chunks (skip duplicates)
        3. Generate embeddings for new chunks only
        4. Upload vectors + metadata to Qdrant
        
        Args:
            chunks: List of chunk dicts from Postgres
                Each chunk must have: id, text, ticker, section, etc.
            batch_size: Upload N vectors at once
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        logger.info(f"Checking {len(chunks)} chunks for duplicates...")
        
        # Step 1: Deduplicate - filter out chunks that already exist
        chunk_ids = [str(chunk["id"]) for chunk in chunks]
        existing_ids = set()
        
        try:
            # Check which IDs already exist in Qdrant (batch retrieve)
            # Process in batches of 100 to avoid memory issues
            for i in range(0, len(chunk_ids), 100):
                batch_ids = chunk_ids[i:i+100]
                
                try:
                    points = self.client.retrieve(
                        collection_name=self.collection_name,
                        ids=batch_ids,
                        with_payload=False,  # Don't need payload, just checking existence
                        with_vectors=False   # Don't need vectors, just checking existence
                    )
                    existing_ids.update([p.id for p in points])
                except Exception as batch_error:
                    # If retrieve fails for this batch, log but continue
                    # (Qdrant returns error if ANY ID doesn't exist)
                    logger.debug(f"Batch {i//100 + 1} check failed (normal if IDs don't exist): {batch_error}")
                    continue
        
        except Exception as e:
            # If deduplication check fails entirely, warn and proceed with all chunks
            logger.warning(f"Could not check existing chunks, will attempt upload: {e}")
            existing_ids = set()
        
        # Filter to only new chunks
        new_chunks = [c for c in chunks if str(c["id"]) not in existing_ids]
        
        # Log results
        if existing_ids:
            logger.info(f"Found {len(existing_ids)} chunks already in Qdrant (skipping)")
        
        if not new_chunks:
            logger.info("✓ All chunks already exist in Qdrant, nothing to add")
            return
        
        logger.info(f"Adding {len(new_chunks)} new chunks to Qdrant...")
        
        # Use settings if not provided
        batch_size = batch_size or settings.qdrant_upload_batch_size
        
        # Step 2: Extract texts from new chunks only
        texts = [chunk['text'] for chunk in new_chunks]
        
        # Step 3: Generate embeddings (only for new chunks)
        embeddings = self.embed_texts(texts)
        
        # Step 4: Create points (vector + metadata)
         # Step 4: Create points (vector + metadata)
        points = []
        for chunk, embedding in zip(new_chunks, embeddings):
            # Normalize section name for easier filtering
            section_normalized = self._normalize_section_name(chunk['section'])
            
            point = PointStruct(
                id=str(chunk['id']),
                vector=embedding,
                payload={
                    "chunk_id": str(chunk['id']),
                    "filing_id": str(chunk['filing_id']),
                    "ticker": chunk['ticker'],
                    "filing_type": chunk['filing_type'],
                    "report_date": chunk['report_date'],
                    "section": section_normalized,  # ← Normalized: "Item 7"
                    "section_full": chunk['section'],  # ← Keep full name for display
                    "chunk_index": chunk['chunk_index'],
                    "chunk_type": chunk['chunk_type'],
                    "text": chunk['text'],
                    # Note: document_url is NOT stored in Qdrant to avoid duplication
                    # It's fetched from PostgreSQL via enrich_chunks_with_document_url()
                }
            )
            points.append(point)
        
        # Step 5: Upload to Qdrant in batches
        total_batches = (len(points) - 1) // batch_size + 1
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            logger.info(f"Uploaded batch {i//batch_size + 1}/{total_batches}")
        
        logger.info(f"✓ Successfully added {len(points)} new chunks to Qdrant")

    def search(
        self,
        query: str,
        limit: int = None,
        ticker:Optional[str] = None,
        filing_type:Optional[str] = None,
        section:Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for similar chunks.

        Two stage process:
            1. Filter: only search chunks matching metadata filters
            2. Vector search: find most similar vectors in filtered set
        
        Args:
            query: Text query ("What is apple's revenues?")
            limit: Return top N results
            ticker: Filter by ticker (e.g. "AAPL")
            filing_type: Filter by filing type (e.g. "10-K")
            section: Filter by section (e.g. "Item 1")
        
        Returns:
            List of results with scores:
            [
                {
                    "id": "uuid",
                    "score": 0.95, # similarity score
                    "chunk": {
                        "text": "text of the chunk",
                        "metadata": {
                            "chunk_id": "uuid",
                            "ticker": "AAPL",
                            "filing_type": "10-K",
                            "report_date": "2024-09-28",
                            "section": "Item 1",
                            "chunk_index": 1,
                            "chunk_type": "section",
                        }
                    }
                }
            ]
        """

        # Use settings if not provided
        limit = limit or settings.top_k
        
        # Step 1: Convert query to embedding vector
        # The query must be in the same vector space as the documents
        # Example: "What is Apple's revenue?" -> [0.23, -0.45, ..., 0.12]
        # We pass [query] as a list because embed_texts expects a batch
        # Then [0] extracts the single vector from the returned list
        query_vector = self.embed_texts([query])[0]

        # Step 2: Build metadata filters (optional)
        # Filters are applied BEFORE vector search (very efficient)
        # This is like SQL WHERE clauses but for vector search
        # Example: Only search in AAPL's 10-K filings
        filter_conditions = []

        if ticker:
            # Filter by company ticker (exact match)
            filter_conditions.append(
                FieldCondition(
                    key="ticker",
                    match=MatchValue(value=ticker)
                )
            )
        
        if section:
            # Normalize the section query
            section_normalized = self._normalize_section_name(section)
            # If user just provided a number (e.g., "7"), add "Item " prefix
            if section_normalized.isdigit():
                section_normalized = f"Item {section_normalized}"

            # Normalize case: "ITEM 7" → "Item 7", "item 7" → "Item 7"
            if section_normalized.lower().startswith('item'):
                section_normalized = 'Item ' + section_normalized.split()[-1].upper()

            # Filter by section name (exact match)
            # Example: Only search in "Item 1A: Risk Factors"
            filter_conditions.append(
                FieldCondition(
                    key="section",
                    match=MatchValue(value=section_normalized)
                )
            )
        
        if filing_type:
            # Filter by form type (exact match)
            # Example: Only search 10-K annual reports
            filter_conditions.append(
                FieldCondition(
                    key="filing_type",
                    match=MatchValue(value=filing_type)
                )
            )
        
        # Combine all conditions with AND logic (must satisfy all)
        # If no filters provided, query_filter = None (search everything)
        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Step 3: Search Qdrant for similar vectors
        # This is the core semantic search operation:
        # 1. Apply filters to narrow down search space
        # 2. Compute cosine similarity between query_vector and all filtered vectors
        # 3. Return top N most similar results
        # 
        # Performance: Qdrant uses HNSW index for fast approximate search
        # - Exact search on 1M vectors: ~seconds
        # - HNSW search on 1M vectors: ~milliseconds
        results = self.client.search(
            collection_name = self.collection_name,
            query_vector = query_vector,        # The query embedding
            query_filter = query_filter,        # Metadata filters (applied first)
            limit = limit,                      # Top N results
            with_payload=True,                  # Include metadata in results
        )

        # Step 4: Format and filter results by confidence threshold
        # Convert Qdrant's result objects to simple dictionaries
        # Filter out low-confidence results that don't meet the threshold
        formatted_results=[]
        filtered_count = 0
        
        for result in results:
            # Apply score threshold filter
            if result.score < settings.score_threshold:
                filtered_count += 1
                logger.debug(f"Filtered chunk {result.id} with score {result.score:.2f} (below threshold {settings.score_threshold})")
                continue
                
            formatted_results.append(
                {
                    "id":result.id,                 # UUID of the chunk
                "score":result.score,           # Cosine similarity (0 to 1, higher = more similar)
                **result.payload                # Unpack all metadata (ticker, text, section, etc)
                }
            )
        
        # Log filtering statistics
        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} chunks below threshold {settings.score_threshold}. Returning {len(formatted_results)} high-confidence chunks.")
        
        # Return empty list if no results meet threshold
        if not formatted_results:
            logger.warning(f"No chunks found above confidence threshold {settings.score_threshold}. Consider lowering threshold or improving query.")

        return formatted_results

    def get_collection_info(self) -> Dict:
        """
        Get collection statistics (like SELECT COUNT(*) in SQL).
        
        Useful for monitoring and debugging:
        - How many vectors are stored?
        - Is the collection healthy?
        - How many segments (internal storage units)?

        Returns:
            Dict with collection info:
            {
                "vectors_count": 1011,           # Total vectors stored
                "indexed_vector_count": 1023,    # Vectors indexed (ready for search)
                "points_count": 1111,            # Number of points (rows)
                "segments_count": 1,             # Internal storage segments
                "status": "green",               # Health status
            }
        """
        # Query Qdrant for collection metadata
        # This is a lightweight operation (no vector computation)
        collection = self.client.get_collection(self.collection_name)
        return {
            "vectors_count": collection.vectors_count,
            "points_count": collection.points_count,
            "status": collection.status
        }
            