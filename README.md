# SQL Analyst

![CI](https://github.com/JoshStevens582/sql-analyst/actions/workflows/ci.yml/badge.svg)

English question → model drafts SQLite → **your code** allows only read-only `SELECT` → run on a **synthetic** database → plain-language answer.

Built with **LangGraph** so a failed validation or query can loop back (max 3 tries) before the API responds.

This is not connected to the live warehouse ledger.

## Run locally

```bash
cd sql-analyst
uv sync --all-groups
uv run uvicorn sql_analyst.main:app --reload --port 8088
```

Open http://127.0.0.1:8088/

Without `OPENAI_API_KEY`, the stub LLM answers fixture questions for development and CI.

## Guardrails

- `sqlglot` parses every statement and rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and multi-statement scripts.
- SQLite opens with `mode=ro`.
- Row cap (`SQL_ANALYST_MAX_ROWS`, default 200).

## Tests

```bash
uv run ruff check .
uv run mypy .
uv run pytest
```