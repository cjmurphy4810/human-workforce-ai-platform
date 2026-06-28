"""Recommendation Engine — assigns a recommended action to every article.

Each article receives exactly one action (or IGNORE) with reasoning.
Decision logic is deterministic: the highest-scoring dimension above its
threshold wins.  Ties are broken by the priority order defined below.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from intelligence.config.defaults import (
    LOOKBACK_DAYS,
    MAX_RECOMMENDATIONS,
    REC_CONSULTING_MIN,
    REC_EXEC_BUSINESS_MIN,
    REC_EXEC_INTEREST_MIN,
    REC_IGNORE_MAX,
    REC_NEWSLETTER_MIN,
    REC_PODCAST_MIN,
    REC_YOUTUBE_MIN,
)
from intelligence.models.intelligence import (
    ArticleData,
    ArticleRef,
    Recommendation,
    RecommendationAction,
)


def _to_ref(a: ArticleData) -> ArticleRef:
    return ArticleRef(
        title=a.title,
        url=a.url,
        source=a.source_name,
        published_at=a.published_at.isoformat(),
        overall_score=round(a.overall, 3),
    )


def _rec_id(url: str) -> str:
    return f"rec-{hashlib.md5(url.encode()).hexdigest()[:10]}"  # noqa: S324


def _determine_action(
    a: ArticleData,
) -> tuple[RecommendationAction, str, float]:
    """Return (action, reasoning, score) for a single article."""

    max_score = max(
        a.podcast_potential,
        a.consulting_opportunity,
        a.executive_interest,
        a.business_impact,
        a.overall,
    )
    if max_score <= REC_IGNORE_MAX:
        return (
            RecommendationAction.IGNORE,
            f"Overall score ({a.overall:.0%}) is below minimum threshold across all dimensions.",
            max_score,
        )

    # Executive Presentation: high C-suite interest + high business impact
    if a.executive_interest >= REC_EXEC_INTEREST_MIN and a.business_impact >= REC_EXEC_BUSINESS_MIN:
        score = round(a.executive_interest * 0.55 + a.business_impact * 0.45, 3)
        return (
            RecommendationAction.EXECUTIVE_PRESENTATION,
            (
                f"C-suite relevance is high ({a.executive_interest:.0%} executive interest, "
                f"{a.business_impact:.0%} business impact). Suitable for board-level deck."
            ),
            score,
        )

    # Podcast: strong audience engagement potential
    if a.podcast_potential >= REC_PODCAST_MIN:
        return (
            RecommendationAction.PODCAST,
            (
                f"High podcast potential ({a.podcast_potential:.0%}). "
                f"Topic is accessible, engaging, and conversational."
            ),
            a.podcast_potential,
        )

    # Consulting Article: clear commercial angle
    if a.consulting_opportunity >= REC_CONSULTING_MIN:
        return (
            RecommendationAction.CONSULTING_ARTICLE,
            (
                f"Strong consulting angle ({a.consulting_opportunity:.0%}). "
                f"Business impact ({a.business_impact:.0%}) supports a client-facing deliverable."
            ),
            a.consulting_opportunity,
        )

    # Newsletter: solid executive interest below C-suite threshold
    if a.executive_interest >= REC_NEWSLETTER_MIN:
        return (
            RecommendationAction.NEWSLETTER,
            (
                f"Executive interest ({a.executive_interest:.0%}) makes this a "
                f"good newsletter inclusion for a leadership audience."
            ),
            a.executive_interest,
        )

    # YouTube Video: good business impact — explainer or analysis format
    if a.business_impact >= REC_YOUTUBE_MIN:
        return (
            RecommendationAction.YOUTUBE_VIDEO,
            (
                f"Business impact ({a.business_impact:.0%}) supports a "
                f"YouTube explainer or market-analysis short."
            ),
            a.business_impact,
        )

    # Default: ignore
    return (
        RecommendationAction.IGNORE,
        (
            f"No single dimension crossed its threshold "
            f"(podcast: {a.podcast_potential:.0%}, consulting: {a.consulting_opportunity:.0%}, "
            f"exec: {a.executive_interest:.0%}, business: {a.business_impact:.0%})."
        ),
        max_score,
    )


def generate_recommendations(
    articles: list[ArticleData],
    lookback_days: int = LOOKBACK_DAYS,
    include_ignored: bool = False,
) -> list[Recommendation]:
    """Generate one recommendation per article, sorted by score descending."""
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [a for a in articles if a.published_at >= cutoff]

    recs: list[Recommendation] = []
    for a in eligible:
        action, reasoning, score = _determine_action(a)
        if action == RecommendationAction.IGNORE and not include_ignored:
            continue
        recs.append(Recommendation(
            id=_rec_id(a.url),
            action=action,
            title=a.title,
            reasoning=reasoning,
            score=round(score, 3),
            article_count=1,
            articles=[_to_ref(a)],
        ))

    recs.sort(key=lambda r: r.score, reverse=True)
    return recs[:MAX_RECOMMENDATIONS]
