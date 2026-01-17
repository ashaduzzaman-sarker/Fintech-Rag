"""
Unit tests for chunking functionality.
"""

import pytest
from langchain.schema import Document

from app.ingestion.chunkers import SemanticChunker, AdvancedSemanticChunker


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return Document(
        page_content="""
        This is a test document. It has multiple sentences.
        
        This is a new paragraph. It contains more information.
        We want to test how the chunker handles this content.
        
        Here's another section with even more text to process.
        The chunker should handle this appropriately.
        """,
        metadata={"source": "test.pdf", "page": 1}
    )


def test_semantic_chunker_initialization():
    """Test chunker initialization."""
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=100)
    
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 100
    assert chunker.tokenizer is not None


def test_chunk_documents(sample_document):
    """Test document chunking."""
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    
    chunks = chunker.chunk_documents([sample_document])
    
    # Should produce multiple chunks
    assert len(chunks) > 0
    
    # Each chunk should have metadata
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata
        assert "total_chunks" in chunk.metadata
        assert "chunk_tokens" in chunk.metadata
        assert "source" in chunk.metadata
        assert chunk.metadata["source"] == "test.pdf"


def test_chunk_preserves_metadata(sample_document):
    """Test that original metadata is preserved."""
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    
    chunks = chunker.chunk_documents([sample_document])
    
    for chunk in chunks:
        assert chunk.metadata["source"] == sample_document.metadata["source"]
        assert chunk.metadata["page"] == sample_document.metadata["page"]


def test_advanced_chunker_sections():
    """Test advanced chunker with section detection."""
    doc = Document(
        page_content="""
        # Section 1
        
        Content for section 1.
        
        # Section 2
        
        Content for section 2.
        """,
        metadata={"source": "test.md"}
    )
    
    chunker = AdvancedSemanticChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk_documents([doc])
    
    assert len(chunks) > 0


def test_empty_document_handling():
    """Test handling of empty documents."""
    chunker = SemanticChunker()
    
    empty_doc = Document(page_content="", metadata={"source": "empty.pdf"})
    chunks = chunker.chunk_documents([empty_doc])
    
    # Should return empty list for empty document
    assert len(chunks) == 0


def test_token_counting():
    """Test token counting functionality."""
    chunker = SemanticChunker()
    
    text = "This is a test sentence with multiple words."
    token_count = chunker._count_tokens(text)
    
    # Should return a positive integer
    assert isinstance(token_count, int)
    assert token_count > 0