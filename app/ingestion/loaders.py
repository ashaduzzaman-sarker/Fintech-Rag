"""
Document loaders for multiple file formats.
Handles PDF, DOCX, TXT with robust error handling and metadata extraction.
"""

import re
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """
    Unified document loader supporting multiple formats.
    Extracts text and enriches with metadata.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self):
        self.stats: dict[str, Any] = {"total_loaded": 0, "failed": 0, "by_type": {}}

    def load_document(self, file_path: Path) -> list[Document]:
        """
        Load a single document and extract text.

        Args:
            file_path: Path to document file

        Returns:
            List of Document objects (one per page for PDFs)

        Raises:
            ValueError: If file format is unsupported
            IOError: If file cannot be read
        """

        if not file_path.exists():
            raise OSError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. " f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        logger.info(
            f"Loading document: {file_path.name}",
            extra={"file_type": extension, "file_size": file_path.stat().st_size},
        )

        try:
            # Select appropriate loader
            loader: PyPDFLoader | Docx2txtLoader | TextLoader
            if extension == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif extension == ".docx":
                loader = Docx2txtLoader(str(file_path))
            elif extension in {".txt", ".md"}:
                loader = TextLoader(str(file_path), encoding="utf-8")
            else:
                raise ValueError(f"No loader for {extension}")

            # Load documents
            documents = loader.load()

            # Enrich metadata
            for doc in documents:
                doc.metadata.update(self._extract_base_metadata(file_path))
                doc.metadata = self._clean_metadata(doc.metadata)

            # Update stats
            self.stats["total_loaded"] += 1
            self.stats["by_type"][extension] = self.stats["by_type"].get(extension, 0) + 1

            logger.info(
                f"Successfully loaded {file_path.name}",
                extra={
                    "pages": len(documents),
                    "chars": sum(len(d.page_content) for d in documents),
                },
            )

            return documents

        except Exception as e:
            self.stats["failed"] += 1
            logger.error(
                f"Failed to load {file_path.name}: {str(e)}",
                extra={"error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    def load_directory(
        self, directory: Path, recursive: bool = True, pattern: str = "*"
    ) -> list[Document]:
        """
        Load all documents from a directory.

        Args:
            directory: Directory containing documents
            recursive: Whether to search subdirectories
            pattern: Glob pattern for file matching

        Returns:
            List of all loaded documents
        """

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        logger.info(
            f"Loading documents from {directory}",
            extra={"recursive": recursive, "pattern": pattern},
        )

        # Find files
        glob_pattern = f"**/{pattern}" if recursive else pattern
        all_files = [
            f
            for f in directory.glob(glob_pattern)
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        logger.info(f"Found {len(all_files)} documents to load")

        # Load all documents
        all_documents = []
        for file_path in all_files:
            try:
                docs = self.load_document(file_path)
                all_documents.extend(docs)
            except Exception as e:
                logger.warning(f"Skipping {file_path.name} due to error: {e}")
                continue

        logger.info(
            f"Loaded {len(all_documents)} document chunks from {len(all_files)} files",
            extra=self.stats,
        )

        return all_documents

    def _extract_base_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract standard metadata from file."""

        stat = file_path.stat()

        return {
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            # Attempt to extract document category from filename or path
            "category": self._infer_category(file_path),
        }

    def _infer_category(self, file_path: Path) -> str:
        """
        Infer document category from filename/path.
        Useful for FinTech document organization.
        """

        path_lower = str(file_path).lower()
        name_lower = file_path.stem.lower()

        # Define category keywords
        categories = {
            "compliance": ["compliance", "policy", "procedure", "regulation", "aml", "kyc"],
            "risk": ["risk", "credit", "market", "operational", "var", "stress"],
            "regulatory": ["sec", "finra", "basel", "mifid", "dodd-frank", "regulatory"],
            "financial": [
                "financial",
                "statement",
                "balance",
                "income",
                "cash-flow",
                "10-k",
                "10-q",
            ],
            "product": ["product", "feature", "specification", "requirements"],
            "legal": ["legal", "contract", "agreement", "terms"],
        }

        for category, keywords in categories.items():
            if any(kw in path_lower or kw in name_lower for kw in keywords):
                return category

        return "general"

    def _clean_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Clean and standardize metadata.
        Remove None values and ensure JSON-serializable types.
        """

        cleaned: dict[str, Any] = {}
        for key, value in metadata.items():
            # Skip None values
            if value is None:
                continue

            # Convert non-serializable types
            if isinstance(value, Path):
                value = str(value)

            # Clean whitespace in strings
            if isinstance(value, str):
                value = value.strip()
                # Remove excessive whitespace
                value = re.sub(r"\s+", " ", value)

            cleaned[key] = value

        return cleaned

    def get_stats(self) -> dict[str, Any]:
        """Get loading statistics."""
        return self.stats.copy()
