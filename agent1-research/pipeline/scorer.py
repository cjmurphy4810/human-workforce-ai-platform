from __future__ import annotations

import math

from config.loader import ScoringWeights
from models.article import Article, ArticleScore, ScoredArticle

_BUSINESS_TERMS: frozenset[str] = frozenset(
    {
        "revenue", "roi", "cost", "profit", "efficiency", "enterprise", "business",
        "productivity", "growth", "workforce", "savings", "budget", "investment",
        "operations", "competitive", "market", "value", "performance", "kpi",
    }
)

_EXECUTIVE_TERMS: frozenset[str] = frozenset(
    {
        "ceo", "cto", "ciso", "coo", "cfo", "board", "executive", "leadership",
        "strategic", "c-suite", "chief", "president", "director", "vp",
        "strategy", "enterprise", "organization", "corporate", "governance",
    }
)

_CONSULTING_TERMS: frozenset[str] = frozenset(
    {
        "strategy", "framework", "governance", "advisory", "consulting", "implementation",
        "transformation", "roadmap", "assessment", "audit", "compliance", "policy",
        "change management", "best practice", "methodology", "solution", "guideline",
        "standard", "evaluation", "recommendation",
    }
)

_PODCAST_TERMS: frozenset[str] = frozenset(
    {
        "breakthrough", "disruption", "future", "trend", "innovation", "analysis",
        "insight", "interview", "debate", "prediction", "vision", "explore",
        "discover", "perspective", "implications", "impact", "revolution",
        "shift", "emerging", "new",
    }
)

_URGENCY_TERMS: frozenset[str] = frozenset(
    {
        "critical", "urgent", "risk", "security", "breach", "vulnerability",
        "compliance", "regulation", "mandate", "deadline", "threat", "alert",
        "warning", "immediate", "emergency", "crisis", "attack", "exposure",
        "incident", "failure",
    }
)


def _keyword_score(text: str, terms: frozenset[str]) -> float:
    hits = sum(1 for term in terms if term in text)
    if hits == 0:
        return 0.0
    return min(1.0, hits / math.sqrt(len(terms)))


class ScoringEngine:
    def __init__(self, weights: ScoringWeights) -> None:
        self._weights = weights

    def score(self, article: Article) -> ScoredArticle:
        text = f"{article.title} {article.summary}".lower()

        business_impact = _keyword_score(text, _BUSINESS_TERMS)
        executive_interest = _keyword_score(text, _EXECUTIVE_TERMS)
        consulting_opportunity = _keyword_score(text, _CONSULTING_TERMS)
        podcast_potential = _keyword_score(text, _PODCAST_TERMS)
        urgency = _keyword_score(text, _URGENCY_TERMS)

        w = self._weights
        overall = (
            w.business_impact * business_impact
            + w.executive_interest * executive_interest
            + w.consulting_opportunity * consulting_opportunity
            + w.podcast_potential * podcast_potential
            + w.urgency * urgency
        )
        # source weight nudges overall score (max 5% bonus)
        overall = min(1.0, overall * (0.95 + 0.05 * article.source_weight))

        return ScoredArticle(
            article=article,
            score=ArticleScore(
                business_impact=round(business_impact, 4),
                executive_interest=round(executive_interest, 4),
                consulting_opportunity=round(consulting_opportunity, 4),
                podcast_potential=round(podcast_potential, 4),
                urgency=round(urgency, 4),
                overall=round(overall, 4),
            ),
        )
