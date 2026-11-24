"""Parse SQL with sqlglot and allow read-only SELECT statements only."""

from __future__ import annotations

from typing import cast

import sqlglot
from sqlglot import exp

_FORBIDDEN_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Merge,
    exp.Command,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
)


class SqlValidationError(ValueError):
    """The generated SQL failed a deterministic guardrail."""


def _is_select_query(statement: exp.Expression) -> bool:
    if isinstance(statement, exp.Select | exp.Union | exp.Intersect | exp.Except):
        return True
    if isinstance(statement, exp.With) and statement.this is not None:
        return isinstance(statement.this, exp.Select | exp.Union)
    return False


def normalize_select_sql(sql: str) -> str:
    """Return a single SELECT statement or raise SqlValidationError."""
    stripped = sql.strip().strip("`").strip()
    if not stripped:
        raise SqlValidationError("SQL was empty.")

    try:
        statements = sqlglot.parse(stripped, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError(f"SQL did not parse: {exc}") from exc

    if len(statements) != 1 or statements[0] is None:
        raise SqlValidationError("Only one SQL statement is allowed.")
    statement = cast(exp.Expression, statements[0])

    if not _is_select_query(statement):
        raise SqlValidationError("Only SELECT queries are allowed.")

    for node in statement.walk():
        if isinstance(node, _FORBIDDEN_TYPES):
            raise SqlValidationError(f"Forbidden statement kind: {type(node).__name__}.")

    return statement.sql(dialect="sqlite")