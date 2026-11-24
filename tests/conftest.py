from pathlib import Path

import pytest

from sql_analyst.demo_db import ensure_demo_database
from sql_analyst.llm import StubSqlLlm
from sql_analyst.service import AnalystService


@pytest.fixture
def demo_db(tmp_path: Path) -> Path:
    db = tmp_path / "demo.db"
    ensure_demo_database(db)
    return db


@pytest.fixture
def analyst(demo_db: Path) -> AnalystService:
    return AnalystService(
        llm=StubSqlLlm(),
        database_path=demo_db,
        max_retries=3,
        max_rows=50,
        recursion_limit=25,
    )