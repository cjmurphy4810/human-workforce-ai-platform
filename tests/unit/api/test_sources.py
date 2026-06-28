from __future__ import annotations

from httpx import AsyncClient


async def test_sources_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/sources")
    assert response.status_code == 200


async def test_sources_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/sources")).json()
    assert "items" in data
    assert "total" in data


async def test_sources_count_matches_config(
    api_client: AsyncClient, test_config
) -> None:
    data = (await api_client.get("/sources")).json()
    assert data["total"] == len(test_config.sources)
    assert len(data["items"]) == len(test_config.sources)


async def test_sources_item_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/sources")).json()
    item = data["items"][0]
    assert "name" in item
    assert "url" in item
    assert "weight" in item
    assert "article_count" in item
    assert "avg_score" in item
    assert "latest_article_date" in item


async def test_sources_merges_db_stats(api_client: AsyncClient) -> None:
    data = (await api_client.get("/sources")).json()
    # "Test Source" is in both config and mock_repo stats
    test_source = next((s for s in data["items"] if s["name"] == "Test Source"), None)
    assert test_source is not None
    assert test_source["article_count"] == 30
    assert test_source["avg_score"] == 0.18


async def test_sources_unknown_source_has_zero_stats(api_client: AsyncClient) -> None:
    data = (await api_client.get("/sources")).json()
    # "Another Source" is in config but NOT in mock_repo stats
    other = next((s for s in data["items"] if s["name"] == "Another Source"), None)
    assert other is not None
    assert other["article_count"] == 0
    assert other["avg_score"] == 0.0
