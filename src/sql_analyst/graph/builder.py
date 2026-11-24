"""LangGraph loop: draft SQL, validate, execute, self-heal, summarize."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from sql_analyst.execute import QueryExecutionError, run_select
from sql_analyst.graph.state import AnalystState
from sql_analyst.llm import SqlLlm
from sql_analyst.security import SqlValidationError, normalize_select_sql


class AnalystDeps:
    def __init__(
        self,
        *,
        llm: SqlLlm,
        database_path: Path,
        max_retries: int,
        max_rows: int,
    ) -> None:
        self.llm = llm
        self.database_path = database_path
        self.max_retries = max_retries
        self.max_rows = max_rows


def build_analyst_graph(
    deps: AnalystDeps,
) -> CompiledStateGraph[AnalystState, None, AnalystState, AnalystState]:
    def generate_sql(state: AnalystState) -> AnalystState:
        sql = deps.llm.draft_sql(
            state["question"],
            schema=state["schema_context"],
            previous_sql=None,
            error=None,
        )
        return {"sql_query": sql, "retry_count": 0, "error_log": []}

    def validate_sql(state: AnalystState) -> AnalystState:
        try:
            normalized = normalize_select_sql(state.get("sql_query", ""))
        except SqlValidationError as exc:
            errors = list(state.get("error_log", []))
            errors.append(str(exc))
            return {"error_log": errors, "sql_query": state.get("sql_query", "")}
        return {"sql_query": normalized, "error_log": []}

    def fix_sql(state: AnalystState) -> AnalystState:
        last_error = state.get("error_log", [])[-1] if state.get("error_log") else "Unknown error"
        retry = int(state.get("retry_count", 0)) + 1
        sql = deps.llm.draft_sql(
            state["question"],
            schema=state["schema_context"],
            previous_sql=state.get("sql_query"),
            error=last_error,
        )
        return {"sql_query": sql, "retry_count": retry}

    def execute_sql(state: AnalystState) -> AnalystState:
        try:
            columns, rows = run_select(
                state.get("sql_query", ""),
                deps.database_path,
                max_rows=deps.max_rows,
            )
        except (QueryExecutionError, SqlValidationError) as exc:
            errors = list(state.get("error_log", []))
            errors.append(str(exc))
            return {"error_log": errors}
        return {
            "query_columns": columns,
            "query_rows": rows,
            "error_log": state.get("error_log", []),
        }

    def summarize(state: AnalystState) -> AnalystState:
        answer = deps.llm.summarize(
            state["question"],
            state.get("sql_query", ""),
            state.get("query_columns", []),
            state.get("query_rows", []),
        )
        return {"answer": answer, "status": "ok"}

    def blocked(state: AnalystState) -> AnalystState:
        return {"status": "blocked", "answer": "The query was blocked by the read-only guardrail."}

    def failed(state: AnalystState) -> AnalystState:
        errors = state.get("error_log", [])
        detail = errors[-1] if errors else "The analyst could not finish the question."
        return {"status": "failed", "answer": detail}

    def route_after_validate(state: AnalystState) -> Literal["execute_sql", "fix_sql", "blocked"]:
        errors = state.get("error_log", [])
        if not errors:
            return "execute_sql"
        retries = int(state.get("retry_count", 0))
        if retries >= deps.max_retries:
            return "blocked"
        return "fix_sql"

    def route_after_execute(state: AnalystState) -> Literal["summarize", "fix_sql", "failed"]:
        if "query_columns" in state and "query_rows" in state:
            return "summarize"
        retries = int(state.get("retry_count", 0))
        if retries >= deps.max_retries:
            return "failed"
        return "fix_sql"

    graph: StateGraph[AnalystState] = StateGraph(AnalystState)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("fix_sql", fix_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("summarize", summarize)
    graph.add_node("blocked", blocked)
    graph.add_node("failed", failed)

    graph.add_edge(START, "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_conditional_edges(
        "validate_sql",
        route_after_validate,
        {"execute_sql": "execute_sql", "fix_sql": "fix_sql", "blocked": "blocked"},
    )
    graph.add_edge("fix_sql", "validate_sql")
    graph.add_conditional_edges(
        "execute_sql",
        route_after_execute,
        {"summarize": "summarize", "fix_sql": "fix_sql", "failed": "failed"},
    )
    graph.add_edge("summarize", END)
    graph.add_edge("blocked", END)
    graph.add_edge("failed", END)

    return graph.compile()