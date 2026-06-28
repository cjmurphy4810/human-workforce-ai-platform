"""Tests for the trend detector."""

from __future__ import annotations

from intelligence.analyzers.trend_detector import detect_trends
from intelligence.models.intelligence import ArticleData, TrendType

from tests.unit.intelligence.conftest import _article


def test_emerging_trend_detected_when_only_in_recent() -> None:
    """Topic with 3+ recent articles and zero baseline should be EMERGING."""
    recent_articles = [
        _article(f"Quantum Computing Edge {i}", days_ago=2)
        for i in range(4)
    ]
    trends = detect_trends(recent_articles, lookback_days=30, recent_window_days=7)
    types = {t.type for t in trends}
    assert TrendType.EMERGING in types


def test_declining_trend_detected_when_only_in_baseline() -> None:
    """Topic present in baseline but absent from recent should be DECLINING."""
    baseline_articles = [
        _article(f"Blockchain Legacy System {i}", days_ago=20)
        for i in range(6)
    ]
    trends = detect_trends(baseline_articles, lookback_days=30, recent_window_days=7)
    types = {t.type for t in trends}
    assert TrendType.DECLINING in types


def test_repeated_trend_detected_in_both_windows() -> None:
    """Topic consistent across both windows should be REPEATED."""
    both = [
        _article(f"Enterprise Software Platform {i}", days_ago=d)
        for i in range(4) for d in [3, 20]
    ]
    trends = detect_trends(both, lookback_days=30, recent_window_days=7)
    types = {t.type for t in trends}
    # Should have repeated or growing trend for this sustained topic
    assert TrendType.REPEATED in types or TrendType.GROWING in types


def test_trend_has_required_fields(trending_articles: list[ArticleData]) -> None:
    trends = detect_trends(trending_articles)
    if trends:
        t = trends[0]
        assert t.id
        assert t.topic
        assert t.type in TrendType
        assert isinstance(t.velocity, float)
        assert isinstance(t.recent_count, int)
        assert isinstance(t.baseline_count, int)
        assert isinstance(t.key_sources, list)
        assert isinstance(t.sample_titles, list)


def test_empty_articles_returns_empty_trends() -> None:
    trends = detect_trends([])
    assert trends == []


def test_trend_count_bounded() -> None:
    """Trend detector should not return more than MAX_TREND_TOPICS."""
    from intelligence.config.defaults import MAX_TREND_TOPICS
    many_articles = [
        _article(f"Topic {i} Article {j}", days_ago=2 if j % 2 == 0 else 20)
        for i in range(30)
        for j in range(4)
    ]
    trends = detect_trends(many_articles)
    assert len(trends) <= MAX_TREND_TOPICS


def test_no_duplicate_topics_in_trends(trending_articles: list[ArticleData]) -> None:
    """Each topic should appear at most once in the trend list."""
    trends = detect_trends(trending_articles)
    topics = [t.topic.lower() for t in trends]
    assert len(topics) == len(set(topics))
