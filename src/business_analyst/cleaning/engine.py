"""Execute approved cleaning operations with an audit trail."""

from __future__ import annotations

from uuid import uuid4

import pandas as pd

from business_analyst.cleaning.models import (
    AuditRecord,
    CleaningOperation,
    CleaningResult,
)
from business_analyst.cleaning.operations import apply_operation


class CleaningEngine:
    """Apply an ordered list of explicitly approved transformations."""

    def run(
        self,
        dataframe: pd.DataFrame,
        operations: list[CleaningOperation],
    ) -> CleaningResult:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas DataFrame.")

        original = dataframe.copy(deep=True)
        working = dataframe.copy(deep=True)
        audit: list[AuditRecord] = []

        for sequence, operation in enumerate(operations, start=1):
            operation_id = operation.operation_id or str(uuid4())
            rows_before = len(working)

            if not operation.approved:
                audit.append(
                    AuditRecord(
                        sequence=sequence,
                        operation_id=operation_id,
                        operation_type=operation.operation_type,
                        columns=list(operation.columns),
                        parameters=dict(operation.parameters),
                        status="skipped",
                        rows_before=rows_before,
                        rows_after=rows_before,
                        affected_rows=0,
                        affected_cells=0,
                        summary="Skipped because the operation was not approved.",
                    )
                )
                continue

            try:
                candidate, affected_rows, affected_cells, summary = apply_operation(
                    dataframe=working,
                    operation_type=operation.operation_type,
                    columns=operation.columns,
                    parameters=operation.parameters,
                )
            except Exception as exc:
                audit.append(
                    AuditRecord(
                        sequence=sequence,
                        operation_id=operation_id,
                        operation_type=operation.operation_type,
                        columns=list(operation.columns),
                        parameters=dict(operation.parameters),
                        status="failed",
                        rows_before=rows_before,
                        rows_after=rows_before,
                        affected_rows=0,
                        affected_cells=0,
                        summary=f"{type(exc).__name__}: {exc}",
                    )
                )

                # Stop immediately. The returned DataFrame reflects only
                # previously successful operations; this one was not applied.
                break

            working = candidate

            audit.append(
                AuditRecord(
                    sequence=sequence,
                    operation_id=operation_id,
                    operation_type=operation.operation_type,
                    columns=list(operation.columns),
                    parameters=dict(operation.parameters),
                    status="applied",
                    rows_before=rows_before,
                    rows_after=len(working),
                    affected_rows=affected_rows,
                    affected_cells=affected_cells,
                    summary=summary,
                )
            )

        return CleaningResult(
            dataframe=working,
            audit_trail=audit,
            original_row_count=len(original),
            final_row_count=len(working),
        )
