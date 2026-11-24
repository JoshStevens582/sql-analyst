from typing import Any, Literal

from pydantic import BaseModel, Field


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskOut(BaseModel):
    question: str
    sql_query: str | None
    answer: str
    status: Literal["ok", "blocked", "failed"]
    retry_count: int
    query_columns: list[str] = Field(default_factory=list)
    query_rows: list[list[Any]] = Field(default_factory=list)
    error_log: list[str] = Field(default_factory=list)