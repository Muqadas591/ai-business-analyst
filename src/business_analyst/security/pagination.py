"""Validated pagination parameters for list operations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pagination:
    limit: int = 50
    offset: int = 0


def parse_pagination(
    *,
    limit: int | str = 50,
    offset: int | str = 0,
    max_limit: int = 100,
) -> Pagination:
    """Parse and bound pagination parameters."""
    try:
        parsed_limit = int(limit)
        parsed_offset = int(offset)
    except (TypeError, ValueError) as exc:
        raise ValueError("Limit and offset must be integers.") from exc

    if max_limit < 1:
        raise ValueError("Maximum limit must be positive.")

    if parsed_limit < 1 or parsed_limit > max_limit:
        raise ValueError(f"Limit must be between 1 and {max_limit}.")

    if parsed_offset < 0:
        raise ValueError("Offset cannot be negative.")

    return Pagination(
        limit=parsed_limit,
        offset=parsed_offset,
    )
