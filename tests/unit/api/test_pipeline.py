from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from pipeline.orchestrator import RunResult


def _make_run_result(brief_path: str = "/tmp/brief.md") -> RunResult:
    return RunResult(
        articles_fetched=100,
        articles_new=25,
        articles_saved=25,
        sources_attempted=9,
        sources_succeeded=6,
        source_errors=[("Bad Source", "SSL error")],
        save_errors=[],
        brief_path=brief_path,
        duration_seconds=3.14,
        timestamp=datetime(2026, 6, 28, 12, 0, tzinfo=timezone.utc),
    )


async def test_run_returns_202_with_mock(
    api_client: AsyncClient,
    tmp_agent1_dir: Path,
) -> None:
    result = _make_run_result(str(tmp_agent1_dir / "output" / "2026-06-28" / "executive_brief.md"))
    with patch("api.routers.pipeline.orchestrate_run", new=AsyncMock(return_value=result)):
        response = await api_client.post("/run")
    assert response.status_code == 200


async def test_run_response_schema(
    api_client: AsyncClient,
    tmp_agent1_dir: Path,
) -> None:
    result = _make_run_result()
    with patch("api.routers.pipeline.orchestrate_run", new=AsyncMock(return_value=result)):
        data = (await api_client.post("/run")).json()

    assert data["status"] == "completed"
    assert data["articles_fetched"] == 100
    assert data["articles_new"] == 25
    assert data["sources_attempted"] == 9
    assert data["sources_succeeded"] == 6
    assert len(data["source_errors"]) == 1
    assert data["source_errors"][0]["source"] == "Bad Source"
    assert isinstance(data["duration_seconds"], float)


async def test_run_returns_500_on_pipeline_failure(
    api_client: AsyncClient,
) -> None:
    with patch(
        "api.routers.pipeline.orchestrate_run",
        new=AsyncMock(side_effect=RuntimeError("network timeout")),
    ):
        response = await api_client.post("/run")

    assert response.status_code == 500
    assert "Pipeline failed" in response.json()["detail"]
