"""
Setup Pinecone index for the RAG system.
Run this once before first ingestion.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def setup_pinecone_index():
    """
    Create Pinecone index if it doesn't exist.
    """

    logger.info("Setting up Pinecone index...")
    logger.info(f"Index name: {settings.pinecone_index_name}")
    logger.info(f"Dimension: {settings.pinecone_dimension}")
    logger.info(f"Metric: {settings.pinecone_metric}")

    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)

        # Check if index exists
        existing_indexes = [idx.name for idx in pc.list_indexes()]

        if settings.pinecone_index_name in existing_indexes:
            logger.info(f"✓ Index '{settings.pinecone_index_name}' already exists")

            # Get index stats
            index = pc.Index(settings.pinecone_index_name)
            stats = index.describe_index_stats()
            logger.info(f"  Total vectors: {stats.total_vector_count}")
            logger.info(f"  Dimension: {stats.dimension}")

            return True

        # Create index
        logger.info(f"Creating index '{settings.pinecone_index_name}'...")

        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.pinecone_dimension,
            metric=settings.pinecone_metric,
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )

        logger.info("✓ Index created successfully!")
        logger.info("  Waiting for index to be ready (this may take 30-60 seconds)...")

        import time

        time.sleep(30)  # Wait for index initialization

        logger.info("✓ Setup complete!")
        logger.info("\nNext steps:")
        logger.info("  1. Run: python scripts/generate_test_data.py")
        logger.info("  2. Run: make run")
        logger.info("  3. Ingest: make ingest-sample")

        return True

    except Exception as e:
        logger.error(f"✗ Setup failed: {e}", exc_info=True)
        logger.error("\nTroubleshooting:")
        logger.error("  - Check PINECONE_API_KEY in .env")
        logger.error("  - Verify Pinecone account is active")
        logger.error("  - Check region availability")
        return False


if __name__ == "__main__":
    success = setup_pinecone_index()
    sys.exit(0 if success else 1)
