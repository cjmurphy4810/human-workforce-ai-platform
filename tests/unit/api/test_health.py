from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_health_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200


async def test_health_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/health")).json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert data["database"] in ("connected", "disconnected")
    assert isinstance(data["sources_configured"], int)
    assert "timestamp" in data
    assert "version" in data


async def test_health_sources_count(api_client: AsyncClient, test_config) -> None:
    data = (await api_client.get("/health")).json()
    assert data["sources_configured"] == len(test_config.sources)


async def test_health_db_connected_when_repo_works(api_client: AsyncClient) -> None:
    data = (await api_client.get("/health")).json()
    assert data["database"] == "connected"
    assert data["status"] == "healthy"


async def test_health_db_disconnected_when_repo_raises(
    mock_repo, test_config, tmp_agent1_dir
) -> None:
    from api.dependencies import get_agent1_dir, get_config, get_repo
    from api.main import create_app
    from httpx import ASGITransport, AsyncClient
    from tests.unit.api.conftest import _no_lifespan

    mock_repo.count_all.side_effect = Exception("db error")

    broken_app = create_app(lifespan=_no_lifespan())
    broken_app.dependency_overrides[get_repo] = lambda: mock_repo
    broken_app.dependency_overrides[get_config] = lambda: test_config
    broken_app.dependency_overrides[get_agent1_dir] = lambda: tmp_agent1_dir

    async with AsyncClient(
        transport=ASGITransport(app=broken_app), base_url="http://test"
    ) as client:
        data = (await client.get("/health")).json()

    assert data["database"] == "disconnected"
    assert data["status"] == "degraded"
