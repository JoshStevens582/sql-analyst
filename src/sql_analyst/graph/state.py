from __future__ import annotations

from typing import Any, Literal, TypedDict


class AnalystState(TypedDict, total=False):
    question: str
    schema_context: str
    sql_query: str
    query_columns: list[str]
    query_rows: list[list[Any]]
    error_log: list[str]
    retry_count: int
    answer: str
    status: Literal["ok", "blocked", "failed"]