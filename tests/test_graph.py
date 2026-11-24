from dataclasses import dataclass
from pathlib import Path

from sql_analyst.service import AnalystService


@dataclass
class BadThenGoodStub:
    calls: int = 0

    def draft_sql(
        self,
        question: str,
        *,
        schema: str,
        previous_sql: str | None,
        error: str | None,
    ) -> str:
        _ = question, schema, previous_sql
        self.calls += 1
        if error is None:
            return "DELETE FROM products"
        return "SELECT COUNT(*) AS product_count FROM products"

    def summarize(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[object]],
    ) -> str:
        _ = question, sql, columns
        return f"Count is {rows[0][0]}."


def test_self_heal_after_blocked_sql(demo_db: Path) -> None:
    stub = BadThenGoodStub()
    service = AnalystService(
        llm=stub,
        database_path=demo_db,
        max_retries=3,
        max_rows=50,
        recursion_limit=25,
    )
    result = service.ask("How many products are in the catalogue?")
    assert result.status == "ok"
    assert result.sql_query is not None
    assert "SELECT" in result.sql_query.upper()
    assert stub.calls >= 2


def test_stub_answers_product_count(analyst: AnalystService) -> None:
    result = analyst.ask("How many products do we stock?")
    assert result.status == "ok"
    assert result.query_rows[0][0] == 4