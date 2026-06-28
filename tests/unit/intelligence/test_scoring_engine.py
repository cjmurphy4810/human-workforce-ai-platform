"""Tests for the modular scoring engine and strategy pattern."""

from __future__ import annotations

import pytest
from intelligence.engines.scoring_engine import (
    ArticleScore,
    ScoringEngine,
    ScoringStrategy,
)
from intelligence.models.intelligence import ArticleData, OpportunityType

from tests.unit.intelligence.conftest import _article


def test_rule_based_strategy_is_registered_by_default() -> None:
    engine = ScoringEngine()
    assert "rule_based_v1" in engine.available()


def test_score_returns_sorted_by_score_descending(high_consulting_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    results = engine.score(high_consulting_articles, OpportunityType.CONSULTING)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_consulting_weights_prioritize_consulting_dimension() -> None:
    engine = ScoringEngine()
    high_consulting = _article("Consulting", consulting_opportunity=0.90, business_impact=0.10, executive_interest=0.10)
    low_consulting = _article("Low Consulting", consulting_opportunity=0.10, business_impact=0.90, executive_interest=0.90)

    results = engine.score([high_consulting, low_consulting], OpportunityType.CONSULTING)
    assert results[0].article.title == "Consulting"


def test_podcast_weights_prioritize_podcast_dimension() -> None:
    engine = ScoringEngine()
    high_podcast = _article("Podcast Star", podcast_potential=0.90, executive_interest=0.20, urgency=0.20)
    low_podcast = _article("Not Podcast", podcast_potential=0.10, executive_interest=0.90, urgency=0.90)

    results = engine.score([high_podcast, low_podcast], OpportunityType.PODCAST)
    assert results[0].article.title == "Podcast Star"


def test_register_custom_strategy() -> None:
    """Pluggable strategy pattern: custom scorer can be registered and used."""

    class MockStrategy:
        name = "mock_v1"

        def score_articles(
            self, articles: list[ArticleData], opportunity_type: OpportunityType
        ) -> list[ArticleScore]:
            return [
                ArticleScore(article=a, score=0.99, confidence=1.0, strategy=self.name)
                for a in articles
            ]

    engine = ScoringEngine()
    engine.register(MockStrategy())
    assert "mock_v1" in engine.available()

    articles = [_article("Test")]
    results = engine.score(articles, OpportunityType.CONSULTING, strategy="mock_v1")
    assert results[0].score == 0.99
    assert results[0].strategy == "mock_v1"


def test_unknown_strategy_raises_key_error() -> None:
    engine = ScoringEngine()
    with pytest.raises(KeyError, match="not registered"):
        engine.score([_article("Test")], OpportunityType.PODCAST, strategy="nonexistent_v99")


def test_custom_strategy_satisfies_protocol() -> None:
    """Verify that a class implementing the protocol is accepted."""

    class MyScorer:
        name = "my_scorer"

        def score_articles(self, articles: list[ArticleData], opportunity_type: OpportunityType) -> list[ArticleScore]:
            return []

    assert isinstance(MyScorer(), ScoringStrategy)


def test_score_clamped_to_unit_interval() -> None:
    engine = ScoringEngine()
    # All dims at 1.0 — weighted sum should not exceed 1.0
    article = _article("Max", consulting_opportunity=1.0, business_impact=1.0, executive_interest=1.0)
    results = engine.score([article], OpportunityType.CONSULTING)
    assert results[0].score <= 1.0
    assert results[0].score >= 0.0
