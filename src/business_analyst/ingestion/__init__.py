
"""File ingestion services for CSV and Excel datasets."""

from business_analyst.ingestion.loader import DataIngestionService
from business_analyst.ingestion.models import IngestionResult, SourceMetadata

__all__ = [
    "DataIngestionService",
    "IngestionResult",
    "SourceMetadata",
]
