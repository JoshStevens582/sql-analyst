"""Print LangGraph state after every node — run to see nodes, edges, and state."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

# project root on path when run as script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sql_analyst.config import get_settings
from sql_analyst.demo_db import SCHEMA_CONTEXT
from sql_analyst.graph.builder import AnalystDeps, build_analyst_graph
from sql_analyst.graph.state import AnalystState
from sql_analyst.llm import build_llm


def _compact(state: AnalystState) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in state.items():
        if key == "schema_context":
            out[key] = f"<{len(str(value))} chars>"
        elif key == "query_rows" and isinstance(value, list) and len(value) > 5:
            out[key] = value[:5] + ["…"]
        else:
            out[key] = value
    return out


def main() -> None:
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "How many products are in the catalogue?"
    )
    cfg = get_settings()
    llm = build_llm(api_key=cfg.openai_api_key, model=cfg.openai_model)
    graph = build_analyst_graph(
        AnalystDeps(
            llm=llm,
            database_path=cfg.database_path,
            max_retries=cfg.max_retries,
            max_rows=cfg.max_rows,
        )
    )
    initial: AnalystState = {
        "question": question.strip(),
        "schema_context": SCHEMA_CONTEXT,
    }

    print("=== LANGGRAPH TRACE ===")
    print(f"Question: {question}\n")
    print("STATE = the dict LangGraph carries through the run (graph/state.py).")
    print("Each NODE = one function in graph/builder.py.")
    print("Each step below = one node finished; EDGE = why the next node ran.\n")

    merged = cast(AnalystState, dict(initial))
    step = 0
    for chunk in graph.stream(initial, config={"recursion_limit": cfg.recursion_limit}):
        for node_name, patch in chunk.items():
            step += 1
            merged.update(patch)
            print(f"--- Step {step}: NODE '{node_name}' finished ---")
            print("Returned patch:")
            print(json.dumps(_compact(patch), indent=2, default=str))
            print("Full STATE so far:")
            print(json.dumps(_compact(merged), indent=2, default=str))
            print()

    print("=== END (no more edges; invoke done) ===")
    print(f"status={merged.get('status')!r}  answer={merged.get('answer')!r}")


if __name__ == "__main__":
    main()