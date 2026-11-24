from fastapi.testclient import TestClient

from sql_analyst.config import Settings
from sql_analyst.main import create_app


def test_health_and_ask(tmp_path) -> None:
    db = tmp_path / "demo.db"
    settings = Settings(
        database_path=db,
        openai_api_key=None,
        max_retries=3,
        max_rows=50,
    )
    with TestClient(create_app(settings)) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        ask = client.post("/api/ask", json={"question": "How many products are there?"})
        assert ask.status_code == 200
        body = ask.json()
        assert body["status"] == "ok"
        assert body["sql_query"]