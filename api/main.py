"""Human Workforce AI — FastAPI application.

Start:
    uvicorn api.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make agent1-research packages importable. This must happen before
# any imports from those packages.
_AGENT1_DIR = Path(__file__).parent.parent / "agent1-research"
if str(_AGENT1_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT1_DIR))

# Make intelligence-engine packages importable.
_INTELLIGENCE_DIR = Path(__file__).parent.parent / "intelligence-engine"
if str(_INTELLIGENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTELLIGENCE_DIR))

from config.loader import load_config  # noqa: E402
from storage.database import build_engine, build_session_factory, init_db  # noqa: E402

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = _AGENT1_DIR / "config" / "config.yaml"
_DEFAULT_DB = f"sqlite+aiosqlite:///{_AGENT1_DIR / 'data' / 'research.db'}"


def _make_lifespan(
    config_path: Path = _DEFAULT_CONFIG,
    db_url: str = _DEFAULT_DB,
    agent1_dir: Path = _AGENT1_DIR,
) -> Any:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # ── startup ──────────────────────────────────────────────────────
        logger.info("loading config: %s", config_path)
        config = load_config(config_path)

        if db_url.startswith("sqlite"):
            db_file = db_url.split("///")[-1]
            if db_file and db_file != ":memory:":
                Path(db_file).parent.mkdir(parents=True, exist_ok=True)

        engine = build_engine(db_url)
        await init_db(engine)
        session_factory = build_session_factory(engine)

        app.state.config = config
        app.state.session_factory = session_factory
        app.state.agent1_dir = agent1_dir
        app.state.engine = engine

        logger.info(
            "startup complete: sources=%d db=%s",
            len(config.sources),
            db_url.split("///")[-1] or ":memory:",
        )
        yield

        # ── shutdown ─────────────────────────────────────────────────────
        await engine.dispose()
        logger.info("database engine disposed")

    return lifespan


def create_app(
    config_path: Path = _DEFAULT_CONFIG,
    db_url: str = _DEFAULT_DB,
    agent1_dir: Path = _AGENT1_DIR,
    lifespan: Any = None,
) -> FastAPI:
    """Application factory.

    Pass `lifespan=None` (no argument) for production — the default lifespan
    is used.  Pass an explicit lifespan (or omit for tests that override
    dependencies without DB startup).
    """
    resolved_lifespan = (
        lifespan
        if lifespan is not None
        else _make_lifespan(
            config_path=config_path,
            db_url=db_url,
            agent1_dir=agent1_dir,
        )
    )

    application = FastAPI(
        title="Human Workforce AI API",
        description=(
            "REST API for the Human Workforce AI research pipeline. "
            "Fetches, scores, and surfaces enterprise AI intelligence "
            "from configurable RSS sources."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=resolved_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routers(application)
    return application


def _register_routers(application: FastAPI) -> None:
    from api.routers import (  # noqa: PLC0415
        articles,
        brief,
        health,
        intelligence,
        pipeline,
        sources,
        stats,
        topics,
    )

    application.include_router(health.router)
    application.include_router(stats.router)
    application.include_router(brief.router)
    application.include_router(pipeline.router)
    application.include_router(articles.router)
    application.include_router(topics.router)
    application.include_router(sources.router)
    application.include_router(intelligence.router)


# Module-level app used by uvicorn
app = create_app()
