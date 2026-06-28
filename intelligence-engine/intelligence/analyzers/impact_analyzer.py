"""Executive Impact Analyzer — multi-dimensional impact scoring per topic cluster.

For each significant topic cluster, computes eight impact dimensions:
  Business Impact, Technology Impact, Operational Risk, Governance Impact,
  Regulatory Impact, Financial Services Relevance, Executive Priority, Time Sensitivity.

Dimension derivation from article scores:
  - business_impact        → direct from article.business_impact
  - technology_impact      → article.executive_interest (proxy: exec interest tracks tech shifts)
  - operational_risk       → article.urgency
  - governance_impact      → 0.5*consulting_opportunity + 0.5*executive_interest
  - regulatory_impact      → 0.7*urgency + 0.3*business_impact
  - financial_services_rel → 0.6*business_impact + 0.4*consulting_opportunity
  - executive_priority     → article.executive_interest
  - time_sensitivity       → article.urgency
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from intelligence.config.defaults import LOOKBACK_DAYS, MAX_IMPACT_TOPICS
from intelligence.models.intelligence import ArticleData, ArticleRef, ExecutiveImpact

# ── Keyword helpers (duplicated intentionally — no shared mutable state) ──────

_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "its", "it", "as", "into",
    "through", "how", "what", "when", "where", "who", "why", "which",
    "this", "that", "these", "those", "report", "says", "use", "using",
    "used", "about", "after", "all", "also", "more", "one", "other",
    "out", "over", "up", "your", "our", "we", "you", "s", "re", "ve",
    "ll", "d", "m", "t", "ai", "technology", "data", "new",
})


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in _STOP_WORDS]


def _bigrams(text: str) -> list[str]:
    toks = _tokens(text)
    return [f"{toks[i]} {toks[i + 1]}" for i in range(len(toks) - 1)]


def _article_text(a: ArticleData) -> str:
    return f"{a.title} {a.summary}"


def _to_ref(a: ArticleData) -> ArticleRef:
    return ArticleRef(
        title=a.title,
        url=a.url,
        source=a.source_name,
        published_at=a.published_at.isoformat(),
        overall_score=round(a.overall, 3),
    )


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _cluster_articles(articles: list[ArticleData], max_clusters: int = MAX_IMPACT_TOPICS) -> dict[str, list[ArticleData]]:
    freq: Counter[str] = Counter()
    article_bigrams: dict[str, list[str]] = {}

    for a in articles:
        bgs = _bigrams(_article_text(a))
        article_bigrams[a.id] = bgs
        freq.update(bgs)

    centers = [bg for bg, _ in freq.most_common(max_clusters)]
    clusters: dict[str, list[ArticleData]] = {c: [] for c in centers}

    for a in articles:
        for center in centers:
            if center in article_bigrams.get(a.id, []):
                clusters[center].append(a)
                break

    # Catch stragglers in the best-matching cluster
    clustered_ids = {a.id for arts in clusters.values() for a in arts}
    for a in articles:
        if a.id not in clustered_ids and centers:
            a_bgs = set(article_bigrams.get(a.id, []))
            best = max(centers, key=lambda c: 1 if c in a_bgs else 0)
            clusters[best].append(a)

    return {k: v for k, v in clusters.items() if len(v) >= 2}


# ── Public API ────────────────────────────────────────────────────────────────


def analyze_executive_impact(
    articles: list[ArticleData],
    lookback_days: int = LOOKBACK_DAYS,
) -> list[ExecutiveImpact]:
    """Return executive impact analysis for each significant topic cluster."""
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [a for a in articles if a.published_at >= cutoff and a.overall >= 0.35]

    if not eligible:
        return []

    clusters = _cluster_articles(eligible)
    impacts: list[ExecutiveImpact] = []

    for topic, cluster in clusters.items():
        n = len(cluster)

        bi = _avg([a.business_impact for a in cluster])
        ei = _avg([a.executive_interest for a in cluster])
        co = _avg([a.consulting_opportunity for a in cluster])
        ug = _avg([a.urgency for a in cluster])

        top_refs = [_to_ref(a) for a in sorted(cluster, key=lambda x: x.overall, reverse=True)[:5]]

        impacts.append(ExecutiveImpact(
            topic=topic.title(),
            article_count=n,
            business_impact=round(bi, 3),
            technology_impact=round(ei, 3),
            operational_risk=round(ug, 3),
            governance_impact=round(0.5 * co + 0.5 * ei, 3),
            regulatory_impact=round(0.7 * ug + 0.3 * bi, 3),
            financial_services_relevance=round(0.6 * bi + 0.4 * co, 3),
            executive_priority=round(ei, 3),
            time_sensitivity=round(ug, 3),
            top_articles=top_refs,
        ))

    # Sort by executive_priority descending, then by business_impact
    impacts.sort(key=lambda i: (i.executive_priority, i.business_impact), reverse=True)
    return impacts[:MAX_IMPACT_TOPICS]
