from __future__ import annotations

from httpx import AsyncClient


async def test_topics_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/topics")
    assert response.status_code == 200


async def test_topics_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/topics")).json()
    assert "items" in data
    assert "since_days" in data
    assert data["since_days"] == 30  # default


async def test_topics_returns_five_dimensions(api_client: AsyncClient) -> None:
    data = (await api_client.get("/topics")).json()
    assert len(data["items"]) == 5


async def test_topics_item_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/topics")).json()
    item = data["items"][0]
    assert "id" in item
    assert "label" in item
    assert "article_count" in item
    assert "avg_score" in item
    assert "top_article" in item


async def test_topics_dimension_ids(api_client: AsyncClient) -> None:
    data = (await api_client.get("/topics")).json()
    ids = {item["id"] for item in data["items"]}
    assert ids == {
        "business_impact",
        "executive_interest",
        "consulting_opportunity",
        "podcast_potential",
        "urgency",
    }


async def test_topics_custom_since_days(api_client: AsyncClient, mock_repo) -> None:
    await api_client.get("/topics?since_days=7")
    mock_repo.get_dimension_averages.assert_called_once_with(since_days=7)


async def test_topics_sorted_by_avg_score_desc(api_client: AsyncClient) -> None:
    data = (await api_client.get("/topics")).json()
    scores = [item["avg_score"] for item in data["items"]]
    assert scores == sorted(scores, reverse=True)
