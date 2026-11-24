from __future__ import annotations

from pathlib import Path
from typing import cast

from sql_analyst.demo_db import SCHEMA_CONTEXT, ensure_demo_database
from sql_analyst.graph.builder import AnalystDeps, build_analyst_graph
from sql_analyst.graph.state import AnalystState
from sql_analyst.llm import SqlLlm
from sql_analyst.schemas import AskOut


class AnalystService:
    def __init__(
        self,
        *,
        llm: SqlLlm,
        database_path: Path,
        max_retries: int,
        max_rows: int,
        recursion_limit: int,
    ) -> None:
        ensure_demo_database(database_path)
        deps = AnalystDeps(
            llm=llm,
            database_path=database_path,
            max_retries=max_retries,
            max_rows=max_rows,
        )
        self._graph = build_analyst_graph(deps)
        self._recursion_limit = recursion_limit

    def ask(self, question: str) -> AskOut:
        initial: AnalystState = {
            "question": question.strip(),
            "schema_context": SCHEMA_CONTEXT,
        }
        final = cast(
            AnalystState,
            self._graph.invoke(initial, config={"recursion_limit": self._recursion_limit}),
        )
        return AskOut(
            question=question.strip(),
            sql_query=final.get("sql_query"),
            answer=final.get("answer", ""),
            status=final.get("status", "failed"),
            retry_count=int(final.get("retry_count", 0)),
            query_columns=list(final.get("query_columns", [])),
            query_rows=list(final.get("query_rows", [])),
            error_log=list(final.get("error_log", [])),
        )