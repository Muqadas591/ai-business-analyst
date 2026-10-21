
"""Public ingestion service for supported tabular uploads."""

from __future__ import annotations

from business_analyst.config import Settings, get_settings
from business_analyst.exceptions import (
    IngestionConfigurationError,
    InvalidFileError,
)
from business_analyst.ingestion.csv_reader import read_csv_bytes
from business_analyst.ingestion.excel_reader import (
    list_excel_sheets,
    read_excel_bytes,
)
from business_analyst.ingestion.file_checks import (
    detect_file_format,
    normalize_filename,
    validate_file_size,
)
from business_analyst.ingestion.models import (
    IngestionResult,
    SourceMetadata,
)


class DataIngestionService:
    """Load supported files into normalized ingestion results."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def list_sheets(self, filename: str, data: bytes) -> list[str]:
        """List worksheets for a supported Excel workbook."""
        safe_name = normalize_filename(filename)

        if detect_file_format(safe_name) != "xlsx":
            raise IngestionConfigurationError(
                "Worksheet listing is available only for .xlsx files."
            )

        validate_file_size(data, self.settings)
        return list_excel_sheets(data)

    def ingest(
        self,
        filename: str,
        data: bytes,
        *,
        sheet_name: str | None = None,
    ) -> IngestionResult:
        """Ingest CSV or XLSX bytes and return a normalized result."""
        safe_name = normalize_filename(filename)
        file_format = detect_file_format(safe_name)
        validate_file_size(data, self.settings)

        if file_format == "csv":
            if sheet_name is not None:
                raise IngestionConfigurationError(
                    "A worksheet cannot be selected for a CSV file."
                )

            dataframe, encoding, delimiter = read_csv_bytes(
                data,
                self.settings,
            )
            selected_sheet = None

        elif file_format == "xlsx":
            sheets = list_excel_sheets(data)

            if sheet_name is None:
                if len(sheets) != 1:
                    raise IngestionConfigurationError(
                        "This workbook contains multiple worksheets. "
                        "List the worksheets and select one explicitly."
                    )
                sheet_name = sheets[0]

            dataframe = read_excel_bytes(
                data,
                sheet_name,
                self.settings,
            )
            encoding = None
            delimiter = None
            selected_sheet = sheet_name

        else:
            # Defensive guard if supported formats are extended later.
            raise InvalidFileError("Unsupported file format.")

        source = SourceMetadata(
            filename=safe_name,
            file_format=file_format,  # type: ignore[arg-type]
            file_size_bytes=len(data),
            encoding=encoding,
            delimiter=delimiter,
            sheet_name=selected_sheet,
        )

        return IngestionResult(
            dataframe=dataframe,
            source=source,
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            column_names=tuple(str(column) for column in dataframe.columns),
            warnings=(),
        )
