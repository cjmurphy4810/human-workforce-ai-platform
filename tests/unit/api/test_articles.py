from __future__ import annotations

from httpx import AsyncClient


async def test_articles_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/articles")
    assert response.status_code == 200


async def test_articles_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/articles")).json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


async def test_articles_default_pagination(api_client: AsyncClient) -> None:
    data = (await api_client.get("/articles")).json()
    assert data["limit"] == 50
    assert data["offset"] == 0


async def test_articles_item_schema(api_client: AsyncClient) -> None:
    data = (await api_client.get("/articles")).json()
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "title" in item
    assert "url" in item
    assert "source_name" in item
    assert "published_at" in item
    assert "summary" in item
    assert "score" in item
    score = item["score"]
    assert "overall" in score
    assert "business_impact" in score
    assert "consulting_opportunity" in score


async def test_articles_with_limit(api_client: AsyncClient) -> None:
    response = await api_client.get("/articles?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10


async def test_articles_with_min_score_filter(
    api_client: AsyncClient, mock_repo
) -> None:
    response = await api_client.get("/articles?min_score=0.3")
    assert response.status_code == 200
    _, kwargs = mock_repo.get_articles_filtered.call_args
    assert kwargs["min_score"] == 0.3


async def test_articles_with_source_filter(
    api_client: AsyncClient, mock_repo
) -> None:
    response = await api_client.get("/articles?source=TechCrunch")
    assert response.status_code == 200
    _, kwargs = mock_repo.get_articles_filtered.call_args
    assert kwargs["source"] == "TechCrunch"


async def test_articles_with_topic_filter(
    api_client: AsyncClient, mock_repo
) -> None:
    response = await api_client.get("/articles?topic=consulting_opportunity")
    assert response.status_code == 200
    _, kwargs = mock_repo.get_articles_filtered.call_args
    assert kwargs["dimension"] == "consulting_opportunity"


async def test_articles_invalid_topic_ignored(
    api_client: AsyncClient, mock_repo
) -> None:
    response = await api_client.get("/articles?topic=nonexistent_dimension")
    assert response.status_code == 200
    _, kwargs = mock_repo.get_articles_filtered.call_args
    assert kwargs["dimension"] is None


async def test_articles_limit_out_of_range(api_client: AsyncClient) -> None:
    response = await api_client.get("/articles?limit=999")
    assert response.status_code == 422  # Pydantic validation rejects > 200
