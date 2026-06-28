"""Trend Detector — identifies seven trend types from time-windowed article analysis.

Approach: compare keyword frequency in a recent window (last N days) against
a baseline window (the preceding M days) and classify trends by velocity.
No external NLP libraries are required.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from intelligence.config.defaults import (
    ENTERPRISE_RISK_URGENCY_THRESHOLD,
    LOOKBACK_DAYS,
    MAX_TREND_TOPICS,
    RECENT_WINDOW_DAYS,
    TREND_DECLINE_RATIO,
    TREND_GROWTH_RATIO,
    TREND_MIN_RECENT_COUNT,
    TREND_REPEATED_MIN_BOTH,
)
from intelligence.models.intelligence import ArticleData, ArticleRef, Trend, TrendType

# ── Keyword helpers ───────────────────────────────────────────────────────────

_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "its", "it", "as", "into",
    "through", "how", "what", "when", "where", "who", "why", "which",
    "this", "that", "these", "those", "report", "says", "use", "using",
    "used", "about", "after", "all", "also", "both", "more", "one",
    "other", "out", "over", "up", "your", "our", "we", "you", "he", "she",
    "his", "her", "not", "no", "so", "if", "now", "just", "even", "only",
    "s", "re", "ve", "ll", "d", "m", "t", "ai", "technology", "data",
    "new", "help", "make", "way", "need", "get", "take", "give", "know",
})

_VENDOR_SIGNALS = frozenset({
    "microsoft", "google", "amazon", "aws", "meta", "openai", "anthropic",
    "salesforce", "servicenow", "workday", "oracle", "sap", "ibm", "nvidia",
    "apple", "netflix", "uber", "airbnb", "appian", "tableau", "snowflake",
    "databricks", "palantir", "dataiku", "hugging", "cohere", "mistral",
})


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"\b[a-z]{3,}\b", text.lower()) if w not in _STOP_WORDS]


def _bigrams(text: str) -> list[str]:
    toks = _tokens(text)
    return [f"{toks[i]} {toks[i + 1]}" for i in range(len(toks) - 1)]


def _article_text(a: ArticleData) -> str:
    return f"{a.title} {a.summary}"


def _key_freq(articles: list[ArticleData]) -> Counter[str]:
    freq: Counter[str] = Counter()
    for a in articles:
        freq.update(_bigrams(_article_text(a)))
    return freq


def _to_ref(a: ArticleData) -> ArticleRef:
    return ArticleRef(
        title=a.title,
        url=a.url,
        source=a.source_name,
        published_at=a.published_at.isoformat(),
        overall_score=round(a.overall, 3),
    )


def _trend_id(trend_type: TrendType, topic: str) -> str:
    import hashlib
    slug = re.sub(r"[^a-z0-9]", "-", f"{trend_type.value}-{topic.lower()}")[:40]
    return f"trnd-{hashlib.md5(slug.encode()).hexdigest()[:8]}"  # noqa: S324


def _articles_for_topic(topic: str, articles: list[ArticleData]) -> list[ArticleData]:
    return [a for a in articles if topic in _article_text(a).lower()]


def _make_trend(
    topic: str,
    trend_type: TrendType,
    recent_articles: list[ArticleData],
    recent_count: int,
    baseline_count: int,
) -> Trend:
    matching = _articles_for_topic(topic, recent_articles)
    velocity = (
        (recent_count - baseline_count) / max(baseline_count, 1)
        if trend_type != TrendType.DECLINING
        else -(baseline_count - recent_count) / max(recent_count, 1)
    )
    avg_score = (
        sum(a.overall for a in matching) / len(matching) if matching else 0.0
    )
    key_sources = list({a.source_name for a in matching})[:5]
    sample_titles = [a.title for a in matching[:3]]
    dates = [a.published_at for a in matching]

    return Trend(
        id=_trend_id(trend_type, topic),
        topic=topic.title(),
        type=trend_type,
        velocity=round(velocity, 3),
        recent_count=recent_count,
        baseline_count=baseline_count,
        avg_score=round(avg_score, 3),
        key_sources=key_sources,
        sample_titles=sample_titles,
        first_seen=min(dates).isoformat() if dates else "",
        last_seen=max(dates).isoformat() if dates else "",
    )


# ── Public detectors ──────────────────────────────────────────────────────────


def detect_trends(
    articles: list[ArticleData],
    lookback_days: int = LOOKBACK_DAYS,
    recent_window_days: int = RECENT_WINDOW_DAYS,
) -> list[Trend]:
    """Detect all trend types and return a combined list sorted by velocity."""
    now = datetime.now(UTC)
    recent_cutoff = now - timedelta(days=recent_window_days)
    baseline_cutoff = now - timedelta(days=lookback_days)

    recent = [a for a in articles if a.published_at >= recent_cutoff]
    baseline = [a for a in articles if baseline_cutoff <= a.published_at < recent_cutoff]

    recent_freq = _key_freq(recent)
    baseline_freq = _key_freq(baseline)

    all_topics = set(recent_freq) | set(baseline_freq)
    trends: list[Trend] = []

    for topic in all_topics:
        rc = recent_freq.get(topic, 0)
        bc = baseline_freq.get(topic, 0)

        if rc < TREND_MIN_RECENT_COUNT and bc < TREND_REPEATED_MIN_BOTH:
            continue

        if bc == 0 and rc >= TREND_MIN_RECENT_COUNT:
            # Emerging: appears only in recent window
            trends.append(_make_trend(topic, TrendType.EMERGING, recent, rc, bc))

        elif bc > 0 and rc >= TREND_MIN_RECENT_COUNT and (rc / bc) >= TREND_GROWTH_RATIO:
            # Growing: recent frequency is significantly higher than baseline
            trends.append(_make_trend(topic, TrendType.GROWING, recent, rc, bc))

        elif rc >= TREND_REPEATED_MIN_BOTH and bc >= TREND_REPEATED_MIN_BOTH and (rc / bc) < TREND_GROWTH_RATIO:
            # Repeated: sustained presence in both windows
            trends.append(_make_trend(topic, TrendType.REPEATED, recent + baseline, rc, bc))

        elif bc >= TREND_MIN_RECENT_COUNT and (rc == 0 or (rc / bc) <= TREND_DECLINE_RATIO):
            # Declining: was present in baseline but dropped in recent
            trends.append(_make_trend(topic, TrendType.DECLINING, baseline, rc, bc))

    # Vendor activity: topics where a vendor name is in the bigram
    vendor_topics = [
        t for t in (recent_freq | baseline_freq)
        if any(v in t for v in _VENDOR_SIGNALS)
        and recent_freq.get(t, 0) >= 2
    ]
    for topic in vendor_topics[:10]:
        rc = recent_freq.get(topic, 0)
        bc = baseline_freq.get(topic, 0)
        if not any(t.topic.lower() == topic.lower() for t in trends):
            trends.append(_make_trend(topic, TrendType.VENDOR_ACTIVITY, recent + baseline, rc, bc))

    # Industry patterns: high avg business_impact on repeated topics
    high_impact_recent = [a for a in recent if a.business_impact >= 0.55]
    if high_impact_recent:
        hi_freq = _key_freq(high_impact_recent)
        for topic, cnt in hi_freq.most_common(5):
            if cnt >= 3 and not any(t.topic.lower() == topic.lower() for t in trends):
                trends.append(_make_trend(topic, TrendType.INDUSTRY_PATTERN, high_impact_recent, cnt, baseline_freq.get(topic, 0)))

    # Enterprise risk trends: high urgency + recent
    risk_articles = [a for a in recent if a.urgency >= ENTERPRISE_RISK_URGENCY_THRESHOLD]
    if risk_articles:
        risk_freq = _key_freq(risk_articles)
        for topic, cnt in risk_freq.most_common(5):
            if cnt >= 2 and not any(t.topic.lower() == topic.lower() for t in trends):
                trends.append(_make_trend(topic, TrendType.ENTERPRISE_RISK, risk_articles, cnt, baseline_freq.get(topic, 0)))

    # Deduplicate by topic (keep highest velocity per topic)
    seen: dict[str, Trend] = {}
    for t in trends:
        key = t.topic.lower()
        if key not in seen or abs(t.velocity) > abs(seen[key].velocity):
            seen[key] = t

    deduped = list(seen.values())

    # Sort: emerging first, then by abs velocity descending
    type_order = {
        TrendType.EMERGING: 0,
        TrendType.GROWING: 1,
        TrendType.ENTERPRISE_RISK: 2,
        TrendType.INDUSTRY_PATTERN: 3,
        TrendType.VENDOR_ACTIVITY: 4,
        TrendType.REPEATED: 5,
        TrendType.DECLINING: 6,
    }
    deduped.sort(key=lambda t: (type_order.get(t.type, 9), -abs(t.velocity)))
    return deduped[:MAX_TREND_TOPICS]
