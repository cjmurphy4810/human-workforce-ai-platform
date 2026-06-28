from __future__ import annotations

from httpx import AsyncClient


async def test_stats_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/stats")
    assert response.status_code == 200


async def test_stats_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/stats")).json()
    assert "total_articles" in data
    assert "articles_last_7_days" in data
    assert "articles_last_30_days" in data
    assert "sources_configured" in data
    assert "last_fetch" in data


async def test_stats_values_from_repo(api_client: AsyncClient) -> None:
    data = (await api_client.get("/stats")).json()
    assert data["total_articles"] == 150
    assert data["articles_last_7_days"] == 50  # mock returns 50 for any since value
    assert data["sources_configured"] == 2  # test_config has 2 sources


async def test_stats_last_fetch_not_null(api_client: AsyncClient) -> None:
    data = (await api_client.get("/stats")).json()
    assert data["last_fetch"] is not None
