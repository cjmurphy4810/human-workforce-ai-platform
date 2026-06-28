"""Integration test: full pipeline with mocked RSS and in-memory SQLite."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from config.loader import AppConfig, OutputConfig, ScoringConfig, SourceConfig
from models.article import Article
from pipeline.brief_builder import build_brief
from pipeline.deduplicator import filter_new, stamp_hashes
from pipeline.scorer import ScoringEngine
from storage.database import build_engine, build_session_factory, init_db
from storage.repository import ArticleRepository


def _make_article(i: int) -> Article:
    return Article(
        title=f"Enterprise AI Strategy Article {i}",
        url=f"https://example.com/article-{i}",
        source_name="Test Feed",
        source_weight=0.9,
        published_at=datetime.now(timezone.utc),
        summary=f"This article covers AI governance, strategy, and enterprise ROI number {i}.",
    )


def _default_config() -> AppConfig:
    return AppConfig(
        sources=[SourceConfig(name="Test Feed", url="https://example.com/feed", weight=0.9)],
        scoring=ScoringConfig(),
        output=OutputConfig(top_stories=5, top_consulting=3, top_podcast=3, lookback_days=7),
    )


@pytest.fixture
async def repo() -> ArticleRepository:
    engine = build_engine("sqlite+aiosqlite:///:memory:")
    await init_db(engine)
    return ArticleRepository(build_session_factory(engine))


async def test_full_pipeline_stores_and_retrieves(repo: ArticleRepository) -> None:
    cfg = _default_config()
    articles = [_make_article(i) for i in range(10)]
    stamp_hashes(articles)

    existing = await repo.get_existing_hashes()
    new_articles = filter_new(articles, existing)
    assert len(new_articles) == 10

    scorer = ScoringEngine(cfg.scoring.weights)
    for a in new_articles:
        sa = scorer.score(a)
        await repo.save_article(sa)

    recent = await repo.get_recent_articles(since_days=7)
    assert len(recent) == 10


async def test_dedup_prevents_double_save(repo: ArticleRepository) -> None:
    cfg = _default_config()
    articles = [_make_article(0)]
    stamp_hashes(articles)

    scorer = ScoringEngine(cfg.scoring.weights)

    # First run
    existing = await repo.get_existing_hashes()
    new1 = filter_new(articles, existing)
    for a in new1:
        await repo.save_article(scorer.score(a))

    # Second run — same articles should be filtered out
    existing2 = await repo.get_existing_hashes()
    new2 = filter_new(articles, existing2)
    assert new2 == []

    recent = await repo.get_recent_articles(since_days=7)
    assert len(recent) == 1


async def test_brief_generated_with_real_scores(repo: ArticleRepository) -> None:
    cfg = _default_config()
    articles = [_make_article(i) for i in range(5)]
    stamp_hashes(articles)
    scorer = ScoringEngine(cfg.scoring.weights)

    for a in articles:
        await repo.save_article(scorer.score(a))

    recent = await repo.get_recent_articles(since_days=7)
    md = build_brief(recent, cfg.output)

    assert "## Executive Summary" in md
    assert "## Top 10 Stories" in md
    assert "## Source Citations" in md
    assert "Test Feed" in md


async def test_brief_written_to_disk(tmp_path: Path, repo: ArticleRepository) -> None:
    cfg = _default_config()
    articles = [_make_article(i) for i in range(3)]
    stamp_hashes(articles)
    scorer = ScoringEngine(cfg.scoring.weights)

    for a in articles:
        await repo.save_article(scorer.score(a))

    recent = await repo.get_recent_articles(since_days=7)
    md = build_brief(recent, cfg.output)

    date_label = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = tmp_path / date_label
    out_dir.mkdir(parents=True)
    brief_path = out_dir / "executive_brief.md"
    brief_path.write_text(md, encoding="utf-8")

    assert brief_path.exists()
    content = brief_path.read_text()
    assert len(content) > 100


async def test_fetch_failure_does_not_crash_pipeline() -> None:
    """A source that raises an exception should be skipped, not abort the run."""
    from fetcher.rss import fetch_feeds

    sources = [
        SourceConfig(name="Good Source", url="https://good.example.com/feed", weight=1.0),
        SourceConfig(name="Bad Source", url="https://bad.example.com/feed", weight=1.0),
    ]

    good_articles = [_make_article(0), _make_article(1)]

    async def _mock_fetch_source(source: SourceConfig) -> list[Article]:
        if source.name == "Bad Source":
            raise ConnectionError("network error")
        return good_articles

    with patch("fetcher.rss.fetch_source", side_effect=_mock_fetch_source):
        articles = await fetch_feeds(sources)

    assert len(articles) == 2
    assert all(a.source_name == "Test Feed" for a in articles)
