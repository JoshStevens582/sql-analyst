from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sql_analyst.config import Settings, get_settings
from sql_analyst.llm import build_llm
from sql_analyst.schemas import AskIn, AskOut
from sql_analyst.service import AnalystService


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        llm = build_llm(api_key=cfg.openai_api_key, model=cfg.openai_model)
        app.state.analyst = AnalystService(
            llm=llm,
            database_path=cfg.database_path,
            max_retries=cfg.max_retries,
            max_rows=cfg.max_rows,
            recursion_limit=cfg.recursion_limit,
        )
        yield

    app = FastAPI(title="SQL Analyst", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5180", "http://localhost:5180"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).resolve().parent.parent.parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": str(cfg.database_path)}

    @app.get("/api/meta")
    def meta() -> dict[str, str]:
        mode = "openai" if cfg.openai_api_key else "stub"
        return {"llm_mode": mode, "model": cfg.openai_model if mode == "openai" else "stub"}

    @app.post("/api/ask", response_model=AskOut)
    def ask(body: AskIn) -> AskOut:
        service: AnalystService = app.state.analyst
        try:
            return service.ask(body.question)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/")
    def desk() -> FileResponse:
        index = static_dir / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Desk UI is missing.")
        return FileResponse(
            index,
            headers={"Cache-Control": "no-store"},
        )

    return app


app = create_app()