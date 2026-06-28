"""Shared fixtures for API unit tests.

Tests use an in-memory mock repo and a fixed test config.
No database, no network access, no lifespan startup.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

# Make agent1-research importable
_AGENT1 = Path(__file__).parent.parent.parent.parent / "agent1-research"
if str(_AGENT1) not in sys.path:
    sys.path.insert(0, str(_AGENT1))

from config.loader import AppConfig, OutputConfig, ScoringConfig, SourceConfig
from models.article import Article, ArticleScore, ScoredArticle

# ── shared domain helpers ─────────────────────────────────────────────────────


def make_article(n: int = 0) -> Article:
    return Article(
        title=f"Test Article {n}",
        url=f"https://example.com/article-{n}",
        source_name="Test Source",
        source_weight=0.9,
        published_at=datetime(2026, 6, 28, tzinfo=UTC),
        fetched_at=datetime(2026, 6, 28, 12, 0, tzinfo=UTC),
        summary=f"Summary of article {n} covering AI governance and enterprise strategy.",
        content_hash=f"hash{n:04d}",
    )


def make_scored(n: int = 0, overall: float = 0.50) -> ScoredArticle:
    return ScoredArticle(
        article=make_article(n),
        score=ArticleScore(
            business_impact=0.40,
            executive_interest=0.30,
            consulting_opportunity=0.50,
            podcast_potential=0.25,
            urgency=0.20,
            overall=overall,
        ),
        db_id=n + 1,
    )


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def test_config() -> AppConfig:
    return AppConfig(
        sources=[
            SourceConfig(name="Test Source", url="https://example.com/feed", weight=0.9),
            SourceConfig(name="Another Source", url="https://other.com/feed", weight=0.8),
        ],
        scoring=ScoringConfig(),
        output=OutputConfig(
            directory="output",
            lookback_days=7,
            top_stories=10,
            top_consulting=5,
            top_podcast=5,
        ),
    )


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    scored_articles = [make_scored(i, overall=0.5 - i * 0.02) for i in range(5)]

    repo.count_all.return_value = 150
    repo.count_since.return_value = 50
    repo.get_latest_fetch_time.return_value = datetime(2026, 6, 28, 12, 0, tzinfo=UTC)
    repo.get_recent_articles.return_value = scored_articles
    repo.get_articles_filtered.return_value = (scored_articles, 5)
    repo.get_source_stats.return_value = [
        {
            "source_name": "Test Source",
            "article_count": 30,
            "avg_score": 0.18,
            "latest_published": datetime(2026, 6, 28, tzinfo=UTC),
        }
    ]
    repo.get_dimension_averages.return_value = {
        dim: {
            "label": dim.replace("_", " ").title(),
            "avg": 0.15,
            "article_count": 150,
            "top_article": make_scored(0),
        }
        for dim in [
            "business_impact",
            "executive_interest",
            "consulting_opportunity",
            "podcast_potential",
            "urgency",
        ]
    }
    return repo


@pytest.fixture
def tmp_agent1_dir(tmp_path: Path) -> Path:
    """Minimal agent1-research directory stub for tests that need the dir."""
    (tmp_path / "output").mkdir()
    return tmp_path


@pytest.fixture
async def api_client(
    mock_repo: AsyncMock,
    test_config: AppConfig,
    tmp_agent1_dir: Path,
) -> AsyncClient:
    """AsyncClient pointed at the test app with all dependencies mocked."""
    from api.dependencies import get_agent1_dir, get_config, get_repo
    from api.main import create_app

    # Create app without lifespan (no real DB startup)
    test_app = create_app(lifespan=_no_lifespan())
    test_app.dependency_overrides[get_repo] = lambda: mock_repo
    test_app.dependency_overrides[get_config] = lambda: test_config
    test_app.dependency_overrides[get_agent1_dir] = lambda: tmp_agent1_dir

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client

    test_app.dependency_overrides.clear()


def _no_lifespan():
    """A do-nothing async context manager used as a lifespan for tests."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _lifespan(app):
        yield

    return _lifespan
