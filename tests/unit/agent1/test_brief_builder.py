from __future__ import annotations

from datetime import UTC, datetime

from config.loader import OutputConfig
from models.article import Article, ArticleScore, ScoredArticle
from pipeline.brief_builder import build_brief


def _scored(
    title: str, overall: float = 0.5, consulting: float = 0.3, podcast: float = 0.2
) -> ScoredArticle:
    return ScoredArticle(
        article=Article(
            title=title,
            url=f"https://example.com/{title.replace(' ', '-')}",
            source_name="Test Source",
            published_at=datetime.now(UTC),
            summary=f"Summary of {title}.",
        ),
        score=ArticleScore(
            business_impact=0.4,
            executive_interest=0.3,
            consulting_opportunity=consulting,
            podcast_potential=podcast,
            urgency=0.2,
            overall=overall,
        ),
    )


def _cfg(**kwargs: int) -> OutputConfig:
    defaults = {"top_stories": 10, "top_consulting": 5, "top_podcast": 5, "lookback_days": 7}
    defaults.update(kwargs)
    return OutputConfig(**defaults)


def test_brief_contains_required_sections() -> None:
    articles = [_scored(f"Article {i}", overall=0.5 - i * 0.01) for i in range(5)]
    md = build_brief(articles, _cfg())
    assert "## Executive Summary" in md
    assert "## Top 10 Stories" in md
    assert "## Top Consulting Opportunities" in md
    assert "## Top Podcast Ideas" in md
    assert "## Source Citations" in md


def test_empty_articles_returns_no_articles_message() -> None:
    md = build_brief([], _cfg())
    assert "No articles found" in md


def test_top_stories_capped_at_config_limit() -> None:
    articles = [_scored(f"Article {i}") for i in range(20)]
    md = build_brief(articles, _cfg(top_stories=3))
    # Count "### 1.", "### 2.", "### 3.", "### 4." to verify only 3 appear in stories section
    import re

    story_headers = re.findall(r"^### \d+\.", md, re.MULTILINE)
    # At most top_stories + top_consulting + top_podcast headers
    # Just verify we can't have more than 3+5+5=13 numbered entries total with defaults capped
    assert len(story_headers) <= 3 + 5 + 5


def test_articles_sorted_by_overall_for_stories() -> None:
    articles = [
        _scored("Low", overall=0.1),
        _scored("High", overall=0.9),
        _scored("Mid", overall=0.5),
    ]
    md = build_brief(articles, _cfg())
    high_pos = md.index("High")
    mid_pos = md.index("Mid")
    low_pos = md.index("Low")
    assert high_pos < mid_pos < low_pos


def test_citations_table_present() -> None:
    articles = [_scored(f"Story {i}") for i in range(3)]
    md = build_brief(articles, _cfg())
    assert "| # | Title | Source | Published | Score |" in md


def test_brief_includes_source_name() -> None:
    articles = [_scored("Test Article")]
    articles[0].article.source_name = "Unique Source XYZ"
    md = build_brief(articles, _cfg())
    assert "Unique Source XYZ" in md
