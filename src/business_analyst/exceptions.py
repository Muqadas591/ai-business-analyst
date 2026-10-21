"""Application-specific exceptions."""


class IngestionError(Exception):
    """Base class for safe, user-facing ingestion errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnsupportedFileTypeError(IngestionError):
    """Raised when a file extension or content type is unsupported."""


class FileSizeLimitError(IngestionError):
    """Raised when the upload exceeds the configured byte limit."""


class InvalidFileError(IngestionError):
    """Raised when a file is malformed or its contents do not match its type."""


class EmptyFileError(IngestionError):
    """Raised when a file contains no usable data."""


class EmptyDatasetError(IngestionError):
    """Raised when a parsed file contains no data rows."""


class MissingHeaderError(IngestionError):
    """Raised when a tabular file has no valid column headers."""


class DuplicateHeaderError(IngestionError):
    """Raised when column names are duplicated."""


class RowLimitError(IngestionError):
    """Raised when the dataset exceeds the configured row limit."""


class ColumnLimitError(IngestionError):
    """Raised when the dataset exceeds the configured column limit."""


class SheetSelectionError(IngestionError):
    """Raised when an Excel worksheet selection is invalid."""


class IngestionConfigurationError(IngestionError):
    """Raised when an ingestion setting is invalid."""
