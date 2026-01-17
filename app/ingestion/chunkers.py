"""
Advanced document chunking strategies.

Implements semantic-aware chunking that:
1. Respects sentence boundaries
2. Maintains context with overlap
3. Tracks token counts (not just characters)
4. Preserves document structure
"""

import re

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticChunker:
    """
    Semantic-aware document chunker.

    Design principles:
    - Never split mid-sentence
    - Maintain topic coherence
    - Track exact token counts for LLM context limits
    - Preserve metadata across chunks
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        model_name: str = "gpt-4",
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            model_name: Model for tokenization (affects token counting)
        """

        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.model_name = model_name

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found, using cl100k_base")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Configure text splitter
        # Use RecursiveCharacterTextSplitter with custom separators
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens,
            separators=[
                "\n\n\n",  # Multiple blank lines (section breaks)
                "\n\n",  # Paragraph breaks
                "\n",  # Line breaks
                ". ",  # Sentence endings
                "! ",
                "? ",
                "; ",
                ": ",
                ", ",  # Clause breaks
                " ",  # Word breaks
                "",  # Character breaks (last resort)
            ],
            keep_separator=True,
        )

        logger.info(
            "Chunker initialized",
            extra={
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "model": model_name,
            },
        )

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        Chunk a list of documents.

        Args:
            documents: List of documents to chunk

        Returns:
            List of chunked documents with preserved metadata
        """

        logger.info(f"Chunking {len(documents)} documents")

        all_chunks = []
        stats = {
            "input_docs": len(documents),
            "output_chunks": 0,
            "avg_tokens_per_chunk": 0.0,
            "total_tokens": 0,
        }

        for doc in documents:
            try:
                chunks = self._chunk_single_document(doc)
                all_chunks.extend(chunks)
                stats["output_chunks"] += len(chunks)
                stats["total_tokens"] += sum(self._count_tokens(c.page_content) for c in chunks)
            except Exception as e:
                logger.error(
                    f"Failed to chunk document: {doc.metadata.get('source', 'unknown')}",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                continue

        if stats["output_chunks"] > 0:
            stats["avg_tokens_per_chunk"] = stats["total_tokens"] / stats["output_chunks"]

        logger.info("Chunking complete", extra=stats)

        return all_chunks

    def _chunk_single_document(self, document: Document) -> list[Document]:
        """
        Chunk a single document while preserving metadata.

        Args:
            document: Document to chunk

        Returns:
            List of chunk documents
        """

        # Skip empty documents
        if not document.page_content.strip():
            logger.warning(f"Empty document: {document.metadata.get('source', 'unknown')}")
            return []

        # Clean text
        text = self._preprocess_text(document.page_content)

        # Split into chunks
        chunks = self.text_splitter.split_text(text)

        # Create Document objects with metadata
        chunk_documents = []
        for i, chunk_text in enumerate(chunks):
            # Clone metadata
            chunk_metadata = document.metadata.copy()

            # Add chunk-specific metadata
            chunk_metadata.update(
                {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_tokens": self._count_tokens(chunk_text),
                    "chunk_chars": len(chunk_text),
                }
            )

            # Create document
            chunk_doc = Document(page_content=chunk_text, metadata=chunk_metadata)

            chunk_documents.append(chunk_doc)

        return chunk_documents

    def _preprocess_text(self, text: str) -> str:
        """
        Clean and normalize text before chunking.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Normalize line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove control characters (except newlines and tabs)
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # Trim
        text = text.strip()

        return text

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the configured tokenizer.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text, disallowed_special=()))

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks without actually splitting.
        Useful for progress estimation.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        token_count = self._count_tokens(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        return max(1, (token_count + effective_chunk_size - 1) // effective_chunk_size)


class AdvancedSemanticChunker(SemanticChunker):
    """
    Enhanced chunker with structure awareness.

    Detects and preserves:
    - Headers and sections
    - Lists and tables
    - Code blocks
    - Financial tables/data
    """

    def _preprocess_text(self, text: str) -> str:
        """
        Enhanced preprocessing that preserves structure markers.
        """

        # First apply base preprocessing
        text = super()._preprocess_text(text)

        # Detect and mark sections
        text = self._mark_sections(text)

        # Preserve tables
        text = self._preserve_tables(text)

        return text

    def _mark_sections(self, text: str) -> str:
        """
        Detect section headers and add markers.
        Helps chunker avoid breaking sections.
        """

        # Detect markdown-style headers
        text = re.sub(r"^(#{1,6})\s+(.+)$", r"\n\n\1 \2\n\n", text, flags=re.MULTILINE)

        # Detect numbered sections (e.g., "1. Introduction", "Section 2.1")
        text = re.sub(r"^(\d+\.[\d\.]*)\s+([A-Z].+)$", r"\n\n\1 \2\n\n", text, flags=re.MULTILINE)

        return text

    def _preserve_tables(self, text: str) -> str:
        """
        Detect financial tables and try to keep them together.
        Adds extra newlines to discourage splitting.
        """

        # Simple heuristic: lines with multiple | or tab separators
        lines = text.split("\n")
        in_table = False
        result = []

        for line in lines:
            # Detect table-like content
            if line.count("|") >= 2 or line.count("\t") >= 2:
                if not in_table:
                    result.append("\n\n")  # Add break before table
                    in_table = True
                result.append(line)
            else:
                if in_table:
                    result.append("\n\n")  # Add break after table
                    in_table = False
                result.append(line)

        return "\n".join(result)
