"""Opportunity Detector — identifies six types of business opportunities from research.

Each detector applies score thresholds (from config/defaults.py), clusters articles
by dominant keywords, and produces a prioritized Opportunity for each cluster.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from intelligence.config.defaults import (
    BUSINESS_VALUE,
    LOOKBACK_DAYS,
    MAX_OPPORTUNITY_CLUSTERS,
    OPPORTUNITY_THRESHOLDS,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
)
from intelligence.engines.scoring_engine import ScoringEngine
from intelligence.models.intelligence import (
    ArticleData,
    ArticleRef,
    Opportunity,
    OpportunityType,
    Priority,
)

# ── Keyword helpers ───────────────────────────────────────────────────────────

_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "its", "it", "as", "into",
    "through", "how", "what", "when", "where", "who", "why", "which",
    "this", "that", "these", "those", "new", "report", "says", "use",
    "using", "used", "about", "after", "all", "also", "both",
    "their", "they", "them", "then", "there", "than", "more", "one",
    "other", "out", "over", "up", "your", "our", "we", "you", "he", "she",
    "his", "her", "not", "no", "so", "if", "now", "just", "even", "only",
    "s", "re", "ve", "ll", "d", "m", "t", "ai", "technology", "data",
    "company", "companies", "business", "businesses", "market", "industry",
    "week", "month", "year", "today", "said", "according", "help", "make", "way", "need", "get", "take", "give", "know", "think",
    "look", "want", "work", "come", "go", "see", "find", "tell", "ask",
})


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in _STOP_WORDS]


def _bigrams(text: str) -> list[str]:
    toks = _tokens(text)
    return [f"{toks[i]} {toks[i + 1]}" for i in range(len(toks) - 1)]


def _article_text(a: ArticleData) -> str:
    return f"{a.title} {a.summary}"


def _cluster_articles(
    articles: list[ArticleData],
    max_clusters: int = MAX_OPPORTUNITY_CLUSTERS,
) -> dict[str, list[ArticleData]]:
    """Group articles by dominant bigram keyword clusters."""
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
                break  # assign to first matching cluster only

    # Also add unclustered articles to their closest center by any bigram overlap
    clustered_ids = {a.id for arts in clusters.values() for a in arts}
    for a in articles:
        if a.id not in clustered_ids and centers:
            a_bgs = set(article_bigrams.get(a.id, []))
            best = max(centers, key=lambda c: 1 if c in a_bgs else 0)
            clusters[best].append(a)

    return {k: v for k, v in clusters.items() if v}


def _to_ref(a: ArticleData) -> ArticleRef:
    return ArticleRef(
        title=a.title,
        url=a.url,
        source=a.source_name,
        published_at=a.published_at.isoformat(),
        overall_score=round(a.overall, 3),
    )


def _priority(score: float) -> Priority:
    if score >= PRIORITY_HIGH:
        return Priority.HIGH
    if score >= PRIORITY_MEDIUM:
        return Priority.MEDIUM
    return Priority.LOW


def _business_value(opp_type: OpportunityType, priority: Priority) -> str:
    return BUSINESS_VALUE.get(opp_type.value, {}).get(priority.value, "Value TBD")


def _opp_id(opp_type: OpportunityType, topic: str) -> str:
    import hashlib
    slug = re.sub(r"[^a-z0-9]", "-", f"{opp_type.value}-{topic.lower()}")[:40]
    suffix = hashlib.md5(slug.encode()).hexdigest()[:6]  # noqa: S324
    return f"opp-{slug}-{suffix}"


# ── Per-type detectors ────────────────────────────────────────────────────────


def _detect_typed(
    articles: list[ArticleData],
    opp_type: OpportunityType,
    primary_filter: str,
    min_primary: float,
    min_overall: float,
    min_articles: int,
    target_audience: str,
    action_template: str,
    engine: ScoringEngine,
    lookback_days: int,
) -> list[Opportunity]:
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [
        a for a in articles
        if a.published_at >= cutoff
        and getattr(a, primary_filter, 0.0) >= min_primary
        and a.overall >= min_overall
    ]
    if len(eligible) < min_articles:
        return []

    clusters = _cluster_articles(eligible)
    opportunities: list[Opportunity] = []

    for topic, cluster in clusters.items():
        if len(cluster) < min_articles:
            continue

        scored = engine.score(cluster, opp_type)
        if not scored:
            continue

        avg_score = sum(s.score for s in scored) / len(scored)
        avg_conf = sum(s.confidence for s in scored) / len(scored)
        priority = _priority(avg_score)

        top_articles = [_to_ref(s.article) for s in scored[:5]]

        opportunities.append(Opportunity(
            id=_opp_id(opp_type, topic),
            type=opp_type,
            title=topic.title(),
            priority=priority,
            confidence=round(avg_conf, 3),
            estimated_business_value=_business_value(opp_type, priority),
            target_audience=target_audience,
            recommended_action=action_template.format(topic=topic.title()),
            supporting_articles=top_articles,
        ))

    return sorted(opportunities, key=lambda o: (o.priority.value, -len(o.supporting_articles)))


def detect_consulting_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["consulting"]
    return _detect_typed(
        articles, OpportunityType.CONSULTING,
        primary_filter="consulting_opportunity",
        min_primary=float(cfg["min_consulting_score"]),
        min_overall=float(cfg["min_overall_score"]),
        min_articles=int(cfg["min_articles"]),
        target_audience="Fortune 500 CIOs, CDOs, and transformation leaders",
        action_template="Develop a consulting engagement proposal on {topic} for enterprise clients",
        engine=engine,
        lookback_days=lookback_days,
    )


def detect_podcast_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["podcast"]
    return _detect_typed(
        articles, OpportunityType.PODCAST,
        primary_filter="podcast_potential",
        min_primary=float(cfg["min_podcast_score"]),
        min_overall=float(cfg["min_overall_score"]),
        min_articles=int(cfg["min_articles"]),
        target_audience="Business leaders and AI practitioners seeking strategic insight",
        action_template="Record a podcast episode exploring {topic} with a guest practitioner",
        engine=engine,
        lookback_days=lookback_days,
    )


def detect_executive_briefing_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["executive_briefing"]
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [
        a for a in articles
        if a.published_at >= cutoff
        and a.executive_interest >= float(cfg["min_executive_interest"])
    ]
    if not eligible:
        return []

    clusters = _cluster_articles(eligible)
    opportunities: list[Opportunity] = []

    for topic, cluster in clusters.items():
        if len(cluster) < int(cfg["min_articles"]):
            continue
        scored = engine.score(cluster, OpportunityType.EXECUTIVE_BRIEFING)
        if not scored:
            continue
        avg_score = sum(s.score for s in scored) / len(scored)
        avg_conf = sum(s.confidence for s in scored) / len(scored)
        priority = _priority(avg_score)

        opportunities.append(Opportunity(
            id=_opp_id(OpportunityType.EXECUTIVE_BRIEFING, topic),
            type=OpportunityType.EXECUTIVE_BRIEFING,
            title=topic.title(),
            priority=priority,
            confidence=round(avg_conf, 3),
            estimated_business_value=_business_value(OpportunityType.EXECUTIVE_BRIEFING, priority),
            target_audience="C-suite executives and board members",
            recommended_action=f"Prepare a 10-slide executive briefing on {topic.title()} for board-level decision-making",
            supporting_articles=[_to_ref(s.article) for s in scored[:5]],
        ))

    return sorted(opportunities, key=lambda o: o.priority.value)


def detect_book_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["book"]
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [
        a for a in articles
        if a.published_at >= cutoff
        and a.business_impact >= float(cfg["min_business_impact"])
    ]
    if len(eligible) < int(cfg["min_articles"]):
        return []

    clusters = _cluster_articles(eligible, max_clusters=6)
    opportunities: list[Opportunity] = []

    for topic, cluster in clusters.items():
        if len(cluster) < int(cfg["min_articles"]):
            continue
        scored = engine.score(cluster, OpportunityType.BOOK)
        avg_score = sum(s.score for s in scored) / len(scored)
        priority = _priority(avg_score)

        opportunities.append(Opportunity(
            id=_opp_id(OpportunityType.BOOK, topic),
            type=OpportunityType.BOOK,
            title=topic.title(),
            priority=priority,
            confidence=round(min(1.0, len(cluster) / 20), 3),
            estimated_business_value=_business_value(OpportunityType.BOOK, priority),
            target_audience="Business executives, practitioners, and strategy consultants",
            recommended_action=f"Develop book proposal on {topic.title()} — {len(cluster)} articles provide research foundation",
            supporting_articles=[_to_ref(s.article) for s in scored[:8]],
        ))

    return sorted(opportunities, key=lambda o: o.priority.value)


def detect_course_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["course"]
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [
        a for a in articles
        if a.published_at >= cutoff
        and a.executive_interest >= float(cfg["min_executive_interest"])
        and a.business_impact >= float(cfg["min_business_impact"])
    ]
    if len(eligible) < int(cfg["min_articles"]):
        return []

    clusters = _cluster_articles(eligible, max_clusters=8)
    opportunities: list[Opportunity] = []

    for topic, cluster in clusters.items():
        if len(cluster) < int(cfg["min_articles"]):
            continue
        scored = engine.score(cluster, OpportunityType.COURSE)
        avg_score = sum(s.score for s in scored) / len(scored)
        priority = _priority(avg_score)

        opportunities.append(Opportunity(
            id=_opp_id(OpportunityType.COURSE, topic),
            type=OpportunityType.COURSE,
            title=topic.title(),
            priority=priority,
            confidence=round(min(1.0, len(cluster) / 15), 3),
            estimated_business_value=_business_value(OpportunityType.COURSE, priority),
            target_audience="Mid-to-senior managers and technical leads in enterprise",
            recommended_action=f"Design a 4-week online course curriculum on {topic.title()} for business professionals",
            supporting_articles=[_to_ref(s.article) for s in scored[:6]],
        ))

    return sorted(opportunities, key=lambda o: o.priority.value)


def detect_linkedin_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    cfg = OPPORTUNITY_THRESHOLDS["linkedin_campaign"]
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    eligible = [
        a for a in articles
        if a.published_at >= cutoff
        and a.executive_interest >= float(cfg["min_executive_interest"])
        and a.business_impact >= float(cfg["min_business_impact"])
    ]
    if len(eligible) < int(cfg["min_articles"]):
        return []

    clusters = _cluster_articles(eligible, max_clusters=10)
    opportunities: list[Opportunity] = []

    for topic, cluster in clusters.items():
        if len(cluster) < int(cfg["min_articles"]):
            continue
        scored = engine.score(cluster, OpportunityType.LINKEDIN_CAMPAIGN)
        avg_score = sum(s.score for s in scored) / len(scored)
        priority = _priority(avg_score)
        unique_sources = len({a.source_name for a in cluster})

        opportunities.append(Opportunity(
            id=_opp_id(OpportunityType.LINKEDIN_CAMPAIGN, topic),
            type=OpportunityType.LINKEDIN_CAMPAIGN,
            title=topic.title(),
            priority=priority,
            confidence=round(min(1.0, unique_sources / 5), 3),
            estimated_business_value=_business_value(OpportunityType.LINKEDIN_CAMPAIGN, priority),
            target_audience="LinkedIn executive audience — VP and C-suite in enterprise",
            recommended_action=f"Launch a 5-post LinkedIn campaign on {topic.title()} — {unique_sources} sources confirm broad industry interest",
            supporting_articles=[_to_ref(s.article) for s in scored[:5]],
        ))

    return sorted(opportunities, key=lambda o: o.priority.value)


# ── Main entry point ──────────────────────────────────────────────────────────


def detect_all_opportunities(
    articles: list[ArticleData],
    engine: ScoringEngine,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[Opportunity]:
    """Run all six opportunity detectors and return combined, priority-sorted results."""
    all_opps: list[Opportunity] = []
    all_opps += detect_consulting_opportunities(articles, engine, lookback_days)
    all_opps += detect_podcast_opportunities(articles, engine, lookback_days)
    all_opps += detect_executive_briefing_opportunities(articles, engine, lookback_days)
    all_opps += detect_book_opportunities(articles, engine, lookback_days)
    all_opps += detect_course_opportunities(articles, engine, lookback_days)
    all_opps += detect_linkedin_opportunities(articles, engine, lookback_days)

    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    return sorted(all_opps, key=lambda o: (priority_order[o.priority], -o.confidence))
