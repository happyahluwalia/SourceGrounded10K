# enum imported but not currently used (may be for future chunk type enums)
import enum
# LangChain's text splitter - handles intelligent text splitting with overlap
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Type hints for better code clarity and IDE support
from typing import Dict, List, Optional
# Import settings for configuration
from app.core.config import settings

class FinancialDocumentChunker:
    """
    Structure-aware chunker for SEC Filings.

    Strategy:
    - Sections: Chunk within each section (preserves section boundaries)
    - Tables: Keep whole (no splitting - financial data need to be intact)
    - Overlap: 15% overlap between sections (prevents context loss)
    - Metadata: Rich metadata for citations and filtering

    Why this approach:
    - SEC filings have clear boundaries
    - Section boundaries are semantically meaningful
    - Tables contain critical data that loses meaning if split
    - Metadata enables section-filtered retrieval
    """

    def __init__(self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = 50
        ) :
        """
        Initialize chunker

        Args:
            chunk_size: Target chunk size in characters (default: from settings)
            chunk_overlap: Overlap between chunks to avoid context loss (default: from settings)
            min_chunk_size: minimum chunk size.
        """
        # Use settings if not provided
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Store parameters as instance attributes for use in other methods
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Initialize text splitter
        # We use RecursiveCharacterTextSplitter which tries to split on:
        # 1. Paragraph breaks (\n\n)
        # 2. Line breaks (\n)
        # 3. Sentence ends (. )
        # 4. Words ( )
        # 5. Characters (last resort)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # Target size for each chunk
            chunk_overlap=chunk_overlap,  # Overlap prevents losing context at boundaries
            length_function = len,  # Use character count (not token count) for simplicity
            separators=["\n\n","\n",". ", " ", ""],  # Try to split at natural boundaries
            keep_separator=True  # Keep separators to maintain readability
        )

    def chunk_filing(
        self,
        sections:Dict[str,str],
        tables: List[Dict],
        filing_metadata: Dict
    )->List[Dict]:
        """
        Chunk a complete SEC filing.
        
        Args:
            sections: Dict of {section_name: section_text}
            tables: List of table dicts from parser
            filing_metadata: Filing info (ticker, date, form type, etc.)
            
        Returns:
            List of chunk dicts with text and metadata
        """
        all_chunks = []

        # Chunk sections first (main content of the filing)
        section_chunks = self._chunk_sections(sections,filing_metadata)
        all_chunks.extend(section_chunks)

        # Chunk tables (kept whole to preserve financial data integrity)
        table_chunks = self._chunk_tables(tables, filing_metadata)
        all_chunks.extend(table_chunks)

        return all_chunks

    def _chunk_sections(
        self,
        sections: Dict[str,str],
        filing_metadata: Dict
    )-> List[Dict]:
        """
        Chunk sections using recursive text splitter.

        Key insight: We chunk WITHIN each section, never across sections.
        This preserves semantic boundaries.
        """

        chunks = []

        # Process each section independently to preserve semantic boundaries
        for section_name, section_text in sections.items():
            # Skip empty or very small sections (likely artifacts or formatting)
            if not section_text or len(section_text.strip()) < self.min_chunk_size:
                continue

            # Split this section into chunks using the recursive splitter
            # This respects natural text boundaries (paragraphs, sentences, etc.)
            section_chunks = self.text_splitter.split_text(section_text)

            # Enrich each chunk with metadata for retrieval and citation
            for i, chunk_text in enumerate(section_chunks):
                # Skip very small chunks (edge cases from splitting)
                if len(chunk_text.strip())< self.min_chunk_size:
                    continue

                # Create chunk dictionary with text and rich metadata
                chunk = {
                    "text": chunk_text.strip(),  # The actual content
                    "section": section_name,  # Which section this came from (for filtering)
                    "chunk_index": i,  # Position within section (for ordering)
                    "total_chunks_in_section": len(section_chunks),  # Context about section size
                    "chunk_type":"section",  # Distinguish from table chunks
                    "char_count":len(chunk_text),  # Actual size
                    "token_count_estimate":len(chunk_text)/4,  # Rough estimate: ~4 chars per token
                    **filing_metadata  # Spread operator: adds ticker, filing_date, form, etc.
                }

                chunks.append(chunk)

        return chunks

    def _chunk_tables(
        self,
        tables: List[Dict],
        filing_metadata: Dict
    )-> List[Dict]:
        """
        Handle tables - keep them whole (no splitting).
        
        Why: Financial tables lose all meaning when split.
        Example: If header row is in one chunk and data rows in another,
        you can't understand what the numbers represent.
        
        """

        chunks = []

        for table in tables:
            # Use the text representation (pipe-separated format from parser)
            table_text = table.get("text","")

            # Skip empty or very small tables
            if not table_text or len(table_text.strip())<self.min_chunk_size:
                continue

            # Check if table is too large for a single chunk
            # 3x chunk_size is our threshold for "too large"
            # TODO: For very large tables, might need to split by rows
            # while keeping header with each chunk
            if len(table_text) > self.chunk_size * 3:
                # Log warning for oversized tables (in production, use proper logging)
                print(f"⚠️  Warning: Large table ({len(table_text)} chars) exceeds 3x chunk_size")
            
            # Create chunk with table-specific metadata
            chunk = {
                "text": table_text.strip(),  # Pipe-separated text representation
                "section": "Financial Table",  # Generic section name for tables
                "chunk_index": table["table_index"],  # Position in document
                "chunk_type": "table",  # Distinguish from section chunks
                "table_rows": table["num_rows"],  # Table dimensions for context
                "table_cols": table["num_cols"],
                "char_count": len(table_text),
                "token_count_estimate": len(table_text) // 4,  # Integer division for estimate
                **filing_metadata  # Add filing-level metadata
            }
            
            chunks.append(chunk)
        
        return chunks

    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks (useful for debugging/optimization).
        
        Returns:
            Dict with stats: total chunks, avg size, size distribution, etc.
        """
        # Handle edge case: no chunks
        if not chunks:
            return {"total_chunks": 0}
        
        # Separate chunks by type for type-specific statistics
        section_chunks = [c for c in chunks if c["chunk_type"] == "section"]
        table_chunks = [c for c in chunks if c["chunk_type"] == "table"]
        
        # Extract sizes for statistical calculations
        section_sizes = [c["char_count"] for c in section_chunks]
        table_sizes = [c["char_count"] for c in table_chunks]
        
        # Return comprehensive statistics for analysis and optimization
        return {
            "total_chunks": len(chunks),  # Overall count
            "section_chunks": len(section_chunks),  # Breakdown by type
            "table_chunks": len(table_chunks),
            "avg_section_size": sum(section_sizes) / len(section_sizes) if section_sizes else 0,  # Avoid division by zero
            "avg_table_size": sum(table_sizes) / len(table_sizes) if table_sizes else 0,
            "min_size": min([c["char_count"] for c in chunks]),  # Size distribution
            "max_size": max([c["char_count"] for c in chunks]),
            "total_chars": sum([c["char_count"] for c in chunks]),  # Total content size
        }