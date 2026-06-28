from __future__ import annotations

from datetime import UTC, datetime

from config.loader import ScoringWeights
from models.article import Article
from pipeline.scorer import ScoringEngine


def _make(title: str = "", summary: str = "") -> Article:
    return Article(
        title=title,
        url="https://example.com/a",
        source_name="Test",
        published_at=datetime.now(UTC),
        summary=summary,
    )


def _engine() -> ScoringEngine:
    return ScoringEngine(ScoringWeights())


def test_scores_in_range() -> None:
    engine = _engine()
    sa = engine.score(_make("AI disrupts enterprise revenue growth"))
    assert 0.0 <= sa.score.overall <= 1.0
    assert 0.0 <= sa.score.business_impact <= 1.0
    assert 0.0 <= sa.score.podcast_potential <= 1.0


def test_business_terms_raise_business_impact() -> None:
    engine = _engine()
    high = engine.score(_make("Enterprise ROI and revenue efficiency savings"))
    low = engine.score(_make("A new color palette for designers"))
    assert high.score.business_impact > low.score.business_impact


def test_executive_terms_raise_executive_interest() -> None:
    engine = _engine()
    high = engine.score(_make("CEO and board strategic governance leadership"))
    low = engine.score(_make("Latest recipes for pasta dinner"))
    assert high.score.executive_interest > low.score.executive_interest


def test_consulting_terms_raise_consulting_score() -> None:
    engine = _engine()
    high = engine.score(_make("Governance framework advisory implementation strategy"))
    low = engine.score(_make("Weather forecast for the weekend"))
    assert high.score.consulting_opportunity > low.score.consulting_opportunity


def test_podcast_terms_raise_podcast_score() -> None:
    engine = _engine()
    high = engine.score(_make("Breakthrough innovation disrupting the future of AI"))
    low = engine.score(_make("Quarterly earnings report filing"))
    assert high.score.podcast_potential > low.score.podcast_potential


def test_urgency_terms_raise_urgency() -> None:
    engine = _engine()
    high = engine.score(_make("Critical security vulnerability breach compliance mandate"))
    low = engine.score(_make("New design trends for 2026"))
    assert high.score.urgency > low.score.urgency


def test_blank_article_scores_zero() -> None:
    engine = _engine()
    sa = engine.score(_make("", ""))
    assert sa.score.overall == 0.0


def test_overall_is_weighted_sum() -> None:
    weights = ScoringWeights(
        business_impact=1.0,
        executive_interest=0.0,
        consulting_opportunity=0.0,
        podcast_potential=0.0,
        urgency=0.0,
    )
    engine = ScoringEngine(weights)
    sa = engine.score(_make("enterprise revenue roi cost savings efficiency productivity"))
    # overall must equal business_impact (weight=1, all others=0), adjusted for source_weight
    expected = sa.score.business_impact * (0.95 + 0.05 * 1.0)
    assert abs(sa.score.overall - round(expected, 4)) < 0.001
