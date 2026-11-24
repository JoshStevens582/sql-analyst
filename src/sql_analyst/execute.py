"""Run validated SELECT queries against the demo database in read-only mode."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sql_analyst.security import normalize_select_sql


class QueryExecutionError(RuntimeError):
    pass


def run_select(
    sql: str,
    database_path: Path,
    *,
    max_rows: int,
) -> tuple[list[str], list[list[Any]]]:
    normalized = normalize_select_sql(sql)
    uri = f"file:{database_path.resolve()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(normalized)
            rows_raw = cur.fetchmany(max_rows + 1)
    except sqlite3.Error as exc:
        raise QueryExecutionError(str(exc)) from exc

    if len(rows_raw) > max_rows:
        raise QueryExecutionError(f"Query returned more than {max_rows} rows. Add LIMIT.")

    columns = list(rows_raw[0].keys()) if rows_raw else []
    rows: list[list[Any]] = [list(row) for row in rows_raw]
    return columns, rows