"""Tests for the recommendation engine."""

from __future__ import annotations

from intelligence.engines.recommendation_engine import generate_recommendations
from intelligence.models.intelligence import ArticleData, RecommendationAction

from tests.unit.intelligence.conftest import _article


def test_podcast_action_for_high_podcast_potential() -> None:
    articles = [_article("Great Podcast Topic", podcast_potential=0.90, executive_interest=0.50, overall=0.70)]
    recs = generate_recommendations(articles)
    assert len(recs) == 1
    assert recs[0].action == RecommendationAction.PODCAST


def test_consulting_action_for_high_consulting_opportunity() -> None:
    articles = [_article("Consulting Goldmine", consulting_opportunity=0.88, business_impact=0.70, overall=0.75)]
    recs = generate_recommendations(articles)
    assert len(recs) == 1
    assert recs[0].action == RecommendationAction.CONSULTING_ARTICLE


def test_executive_presentation_for_high_exec_and_business() -> None:
    articles = [_article("Board Deck Topic", executive_interest=0.80, business_impact=0.70, overall=0.75)]
    recs = generate_recommendations(articles)
    assert len(recs) == 1
    assert recs[0].action == RecommendationAction.EXECUTIVE_PRESENTATION


def test_low_score_article_excluded_by_default() -> None:
    articles = [_article("Irrelevant", business_impact=0.10, executive_interest=0.10, consulting_opportunity=0.10, podcast_potential=0.10, urgency=0.10, overall=0.10)]
    recs = generate_recommendations(articles)
    assert len(recs) == 0


def test_low_score_article_included_when_include_ignored() -> None:
    articles = [_article("Irrelevant", business_impact=0.10, executive_interest=0.10, consulting_opportunity=0.10, podcast_potential=0.10, urgency=0.10, overall=0.10)]
    recs = generate_recommendations(articles, include_ignored=True)
    assert len(recs) == 1
    assert recs[0].action == RecommendationAction.IGNORE


def test_recommendations_sorted_by_score_descending(mixed_articles: list[ArticleData]) -> None:
    recs = generate_recommendations(mixed_articles)
    if len(recs) > 1:
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)


def test_recommendation_has_reasoning(mixed_articles: list[ArticleData]) -> None:
    recs = generate_recommendations(mixed_articles)
    for rec in recs:
        assert rec.reasoning
        assert len(rec.reasoning) > 10


def test_recommendation_id_is_stable() -> None:
    article = _article("Stable ID Test", podcast_potential=0.90, overall=0.80)
    recs1 = generate_recommendations([article])
    recs2 = generate_recommendations([article])
    assert recs1[0].id == recs2[0].id


def test_recommendations_capped_at_max(mixed_articles: list[ArticleData]) -> None:
    from intelligence.config.defaults import MAX_RECOMMENDATIONS
    many = mixed_articles * 20
    recs = generate_recommendations(many)
    assert len(recs) <= MAX_RECOMMENDATIONS
