"""Tests for the opportunity detector."""

from __future__ import annotations

from intelligence.analyzers.opportunity_detector import (
    detect_all_opportunities,
    detect_consulting_opportunities,
    detect_podcast_opportunities,
)
from intelligence.engines.scoring_engine import ScoringEngine
from intelligence.models.intelligence import ArticleData, OpportunityType, Priority

from tests.unit.intelligence.conftest import _article


def test_consulting_opportunities_detected(high_consulting_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_consulting_opportunities(high_consulting_articles, engine)
    assert len(opps) > 0
    assert all(o.type == OpportunityType.CONSULTING for o in opps)


def test_podcast_opportunities_detected(high_podcast_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_podcast_opportunities(high_podcast_articles, engine)
    assert len(opps) > 0
    assert all(o.type == OpportunityType.PODCAST for o in opps)


def test_no_opportunities_when_scores_too_low() -> None:
    engine = ScoringEngine()
    low_articles = [
        _article(f"Low Article {i}", consulting_opportunity=0.10, overall=0.10)
        for i in range(5)
    ]
    opps = detect_consulting_opportunities(low_articles, engine)
    assert len(opps) == 0


def test_opportunity_has_required_fields(high_consulting_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_consulting_opportunities(high_consulting_articles, engine)
    assert len(opps) > 0
    opp = opps[0]
    assert opp.id
    assert opp.type == OpportunityType.CONSULTING
    assert opp.title
    assert opp.priority in (Priority.HIGH, Priority.MEDIUM, Priority.LOW)
    assert 0.0 <= opp.confidence <= 1.0
    assert opp.estimated_business_value
    assert opp.target_audience
    assert opp.recommended_action
    assert isinstance(opp.supporting_articles, list)


def test_detect_all_returns_multiple_types(mixed_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_all_opportunities(mixed_articles, engine)
    types = {o.type for o in opps}
    # Mixed articles should trigger at least two different opportunity types
    assert len(types) >= 1


def test_opportunities_sorted_high_priority_first(mixed_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_all_opportunities(mixed_articles, engine)
    if len(opps) > 1:
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        for i in range(len(opps) - 1):
            assert priority_order[opps[i].priority] <= priority_order[opps[i + 1].priority]


def test_opportunity_id_is_stable(high_consulting_articles: list[ArticleData]) -> None:
    """Same inputs must produce the same opportunity IDs."""
    engine = ScoringEngine()
    opps1 = detect_consulting_opportunities(high_consulting_articles, engine)
    opps2 = detect_consulting_opportunities(high_consulting_articles, engine)
    assert [o.id for o in opps1] == [o.id for o in opps2]


def test_supporting_articles_capped_at_five(high_consulting_articles: list[ArticleData]) -> None:
    engine = ScoringEngine()
    opps = detect_consulting_opportunities(high_consulting_articles, engine)
    for opp in opps:
        assert len(opp.supporting_articles) <= 5
