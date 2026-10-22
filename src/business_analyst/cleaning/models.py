"""Typed models for approved cleaning operations and audit records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


OperationType = Literal[
    "fill_missing",
    "drop_missing",
    "drop_duplicates",
    "convert_numeric",
    "convert_date",
    "trim_text",
    "normalize_category",
]


@dataclass(frozen=True)
class CleaningOperation:
    """A user-approved transformation with explicit parameters."""

    operation_type: OperationType
    columns: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    operation_id: str = ""


@dataclass(frozen=True)
class AuditRecord:
    """An auditable record of one attempted transformation."""

    sequence: int
    operation_id: str
    operation_type: str
    columns: list[str]
    parameters: dict[str, Any]
    status: Literal["applied", "skipped", "failed"]
    rows_before: int
    rows_after: int
    affected_rows: int
    affected_cells: int
    summary: str


@dataclass(frozen=True)
class CleaningResult:
    """Output dataset plus the complete audit trail."""

    dataframe: Any
    audit_trail: list[AuditRecord]
    original_row_count: int
    final_row_count: int

    @property
    def operations_applied(self) -> int:
        return sum(record.status == "applied" for record in self.audit_trail)

    def audit_as_dicts(self) -> list[dict[str, Any]]:
        """Return audit entries suitable for JSON or tabular export."""
        return [asdict(record) for record in self.audit_trail]
