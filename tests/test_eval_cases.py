"""Fixture evals from evals/questions.json (stub LLM in CI)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from sql_analyst.service import AnalystService

EVAL_PATH = Path(__file__).resolve().parents[1] / "evals" / "questions.json"


def _cases() -> list[dict[str, Any]]:
    payload: object = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = "evals/questions.json must be a list"
        raise TypeError(msg)
    return [row for row in payload if isinstance(row, dict)]


@pytest.mark.parametrize("case", _cases(), ids=lambda c: str(c.get("id", "case")))
def test_eval_question(analyst: AnalystService, case: dict[str, Any]) -> None:
    question = case.get("question")
    assert isinstance(question, str)
    result = analyst.ask(question)
    assert result.status == case.get("expect_status", "ok")

    expect_column = case.get("expect_column")
    if isinstance(expect_column, str):
        assert expect_column in result.query_columns

    if "expect_scalar" in case:
        assert len(result.query_rows) == 1
        assert result.query_rows[0][0] == case["expect_scalar"]

    if "expect_min_rows" in case:
        min_rows = case["expect_min_rows"]
        assert isinstance(min_rows, int)
        assert len(result.query_rows) >= min_rows


@dataclass
class DeleteThenCountStub:
    saw_delete: bool = False

    def draft_sql(
        self,
        question: str,
        *,
        schema: str,
        previous_sql: str | None,
        error: str | None,
    ) -> str:
        _ = question, schema
        if error is None:
            self.saw_delete = True
            return "DELETE FROM products"
        return "SELECT COUNT(*) AS product_count FROM products"

    def summarize(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str:
        _ = question, sql, columns
        return f"count={rows[0][0]}"


def test_guardrail_blocks_delete_then_recovers(demo_db: Path) -> None:
    stub = DeleteThenCountStub()
    service = AnalystService(
        llm=stub,
        database_path=demo_db,
        max_retries=3,
        max_rows=50,
        recursion_limit=25,
    )
    result = service.ask("How many products are in the catalogue?")
    assert stub.saw_delete
    assert result.status == "ok"
    assert result.sql_query is not None
    assert "SELECT" in result.sql_query.upper()
    assert "DELETE" not in result.sql_query.upper()
    assert result.query_rows == [[4]]
    assert result.retry_count >= 1