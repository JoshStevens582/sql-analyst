"""OpenAI-backed SQL drafter and summarizer, plus a deterministic stub for tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from openai import OpenAI

from sql_analyst.demo_db import SCHEMA_CONTEXT


class SqlLlm(Protocol):
    def draft_sql(
        self,
        question: str,
        *,
        schema: str,
        previous_sql: str | None,
        error: str | None,
    ) -> str: ...

    def summarize(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str: ...


@dataclass
class OpenAiSqlLlm:
    client: OpenAI
    model: str

    def draft_sql(
        self,
        question: str,
        *,
        schema: str,
        previous_sql: str | None,
        error: str | None,
    ) -> str:
        system = (
            "You write SQLite SELECT queries for analytics questions. "
            "Return JSON with one key sql_query. "
            "Never write INSERT, UPDATE, DELETE, DROP, or ALTER. "
            "Use only tables from the schema."
        )
        user_parts = [f"Schema:\n{schema}", f"Question:\n{question}"]
        if previous_sql:
            user_parts.append(f"Previous SQL:\n{previous_sql}")
        if error:
            user_parts.append(f"Error to fix:\n{error}")
        payload = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            temperature=0,
        )
        raw = payload.choices[0].message.content or "{}"
        data = json.loads(raw)
        sql = data.get("sql_query")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("Model did not return sql_query.")
        return sql.strip()

    def summarize(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str:
        preview = {"columns": columns, "rows": rows[:20]}
        system = (
            "Summarize query results for a warehouse manager. "
            "Use short plain sentences. Mention numbers from the table. "
            "Do not invent rows that are not in the preview."
        )
        user = (
            f"Question: {question}\n"
            f"SQL: {sql}\n"
            f"Preview JSON:\n{json.dumps(preview, default=str)}"
        )
        payload = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return (payload.choices[0].message.content or "").strip()


@dataclass
class StubSqlLlm:
    """Fixture responses for CI without an API key."""

    def draft_sql(
        self,
        question: str,
        *,
        schema: str,
        previous_sql: str | None,
        error: str | None,
    ) -> str:
        _ = schema
        lower = question.lower()
        if "how many" in lower and "product" in lower:
            return "SELECT COUNT(*) AS product_count FROM products"
        if error and previous_sql:
            if "stock_movements" in previous_sql and "group" not in previous_sql.lower():
                return (
                    "SELECT p.sku, SUM(m.quantity_delta) AS shelf_qty "
                    "FROM products p "
                    "JOIN stock_movements m ON m.product_id = p.id "
                    "GROUP BY p.id, p.sku"
                )
        if "shelf" in lower or "stock" in lower or "quantity per sku" in lower:
            return (
                "SELECT p.sku, SUM(m.quantity_delta) AS shelf_qty "
                "FROM products p "
                "JOIN stock_movements m ON m.product_id = p.id "
                "GROUP BY p.id, p.sku"
            )
        if "revenue" in lower or "sales" in lower:
            return (
                "SELECT SUM(line_total_cents) AS revenue_cents FROM order_lines "
                "JOIN orders o ON o.id = order_lines.order_id WHERE o.status != 'cancelled'"
            )
        return (
            "SELECT p.sku, p.name FROM products p ORDER BY p.sku LIMIT 10"
        )

    def summarize(
        self,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> str:
        _ = sql
        if not rows:
            return f'No rows for: "{question}"'
        preview = rows[0] if len(rows) == 1 else f"{len(rows)} rows; first is {rows[0]}"
        return f'For "{question}": {", ".join(columns)} → {preview}'


def default_schema() -> str:
    return SCHEMA_CONTEXT


def build_llm(*, api_key: str | None, model: str) -> SqlLlm:
    if api_key:
        return OpenAiSqlLlm(client=OpenAI(api_key=api_key), model=model)
    return StubSqlLlm()