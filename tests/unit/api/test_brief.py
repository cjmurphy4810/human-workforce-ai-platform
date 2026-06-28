from __future__ import annotations

from pathlib import Path

from httpx import AsyncClient


async def test_brief_404_when_no_file(api_client: AsyncClient) -> None:
    # tmp_agent1_dir has an empty output/ dir — no brief files
    response = await api_client.get("/brief/latest")
    assert response.status_code == 404


async def test_brief_returns_200_when_file_exists(
    api_client: AsyncClient,
    tmp_agent1_dir: Path,
) -> None:
    brief_dir = tmp_agent1_dir / "output" / "2026-06-28"
    brief_dir.mkdir(parents=True)
    (brief_dir / "executive_brief.md").write_text("# Test Brief\n\nContent here.", encoding="utf-8")

    response = await api_client.get("/brief/latest")
    assert response.status_code == 200


async def test_brief_schema(api_client: AsyncClient, tmp_agent1_dir: Path) -> None:
    brief_dir = tmp_agent1_dir / "output" / "2026-06-28"
    brief_dir.mkdir(parents=True)
    content = "# Brief\n\nHello world article text here."
    (brief_dir / "executive_brief.md").write_text(content, encoding="utf-8")

    data = (await api_client.get("/brief/latest")).json()
    assert data["date"] == "2026-06-28"
    assert "content" in data
    assert "# Brief" in data["content"]
    assert isinstance(data["word_count"], int)
    assert isinstance(data["character_count"], int)
    assert data["character_count"] == len(content)


async def test_brief_returns_latest_date(api_client: AsyncClient, tmp_agent1_dir: Path) -> None:
    for date in ("2026-06-25", "2026-06-27", "2026-06-26"):
        d = tmp_agent1_dir / "output" / date
        d.mkdir(parents=True)
        (d / "executive_brief.md").write_text(f"# Brief {date}", encoding="utf-8")

    data = (await api_client.get("/brief/latest")).json()
    assert data["date"] == "2026-06-27"
