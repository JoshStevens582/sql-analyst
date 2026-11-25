# CV / LinkedIn bullets — SQL Analyst

Paste after **Warehouse Ledger** on the CV. Link the repo in the header.

**Project line**  
`SQL Analyst` — [github.com/JoshStevens582/sql-analyst](https://github.com/JoshStevens582/sql-analyst)

**Stack line**  
Python, FastAPI, LangGraph, OpenAI, sqlglot, SQLite (synthetic), pytest, ruff, mypy, GitHub Actions

**Bullets (pick 2–3)**

- Built a **LangGraph** text-to-SQL agent: **generate → validate → execute → summarize**, with **fix_sql** retries (max 3) when validation or execution fails.

- **Deterministic read-only guardrails**: **sqlglot** rejects writes and multi-statement SQL before run; SQLite opens with **`mode=ro`** on a synthetic demo database (not production data).

- **pytest** eval cases load `evals/questions.json`; **GitHub Actions** runs **ruff**, **mypy**, and tests on every push; if they pass, GitHub updates the live demo.

**Skills / interview (one sentence)**  
“The model drafts SQL; Python and sqlglot must approve it before the database runs, and the graph can loop on errors up to three times.”

**Demo command (local)**  
`uv run python scripts/trace_one_question.py "How many products are in the catalogue?"`