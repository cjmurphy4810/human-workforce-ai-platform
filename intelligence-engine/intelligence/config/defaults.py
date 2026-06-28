"""Scoring thresholds and configuration defaults for the Intelligence Engine.

All business rules live here so they can be tuned without touching analyzer logic.
"""

from __future__ import annotations

# ── Analysis windows ──────────────────────────────────────────────────────────

LOOKBACK_DAYS: int = 30
RECENT_WINDOW_DAYS: int = 7

# ── Opportunity thresholds ────────────────────────────────────────────────────

OPPORTUNITY_THRESHOLDS: dict[str, dict[str, float | int]] = {
    "consulting": {
        "min_consulting_score": 0.58,
        "min_overall_score": 0.45,
        "min_articles": 1,
    },
    "podcast": {
        "min_podcast_score": 0.58,
        "min_overall_score": 0.40,
        "min_articles": 1,
    },
    "executive_briefing": {
        "min_executive_interest": 0.62,
        "min_urgency": 0.00,
        "min_articles": 1,
    },
    "book": {
        "min_business_impact": 0.55,
        "min_articles": 6,
    },
    "course": {
        "min_executive_interest": 0.55,
        "min_business_impact": 0.45,
        "min_articles": 4,
    },
    "linkedin_campaign": {
        "min_executive_interest": 0.52,
        "min_business_impact": 0.45,
        "min_articles": 2,
    },
}

# ── Trend detection ───────────────────────────────────────────────────────────

TREND_MIN_RECENT_COUNT: int = 3
TREND_GROWTH_RATIO: float = 1.8
TREND_DECLINE_RATIO: float = 0.3
TREND_REPEATED_MIN_BOTH: int = 4
ENTERPRISE_RISK_URGENCY_THRESHOLD: float = 0.60

# ── Priority bands (composite score) ─────────────────────────────────────────

PRIORITY_HIGH: float = 0.72
PRIORITY_MEDIUM: float = 0.52

# ── Recommendation thresholds ─────────────────────────────────────────────────

REC_PODCAST_MIN: float = 0.62
REC_CONSULTING_MIN: float = 0.62
REC_EXEC_INTEREST_MIN: float = 0.65
REC_EXEC_BUSINESS_MIN: float = 0.55
REC_NEWSLETTER_MIN: float = 0.50
REC_YOUTUBE_MIN: float = 0.50
REC_IGNORE_MAX: float = 0.35

# ── Cluster sizing ────────────────────────────────────────────────────────────

MAX_OPPORTUNITY_CLUSTERS: int = 12
MAX_TREND_TOPICS: int = 20
MAX_IMPACT_TOPICS: int = 15
MAX_RECOMMENDATIONS: int = 60

# ── Business value estimates by opportunity type and priority ─────────────────

BUSINESS_VALUE: dict[str, dict[str, str]] = {
    "consulting": {
        "high": "$100,000–$500,000",
        "medium": "$25,000–$100,000",
        "low": "$10,000–$25,000",
    },
    "podcast": {
        "high": "10,000+ targeted listeners per episode",
        "medium": "2,000–10,000 listeners per episode",
        "low": "500–2,000 niche listeners per episode",
    },
    "book": {
        "high": "$50,000–$200,000 (advance + royalties + speaking)",
        "medium": "$15,000–$50,000",
        "low": "$5,000–$15,000",
    },
    "course": {
        "high": "$30,000–$150,000 annually",
        "medium": "$10,000–$30,000 annually",
        "low": "$2,000–$10,000 annually",
    },
    "executive_briefing": {
        "high": "Direct C-suite engagement — $50,000+ pipeline value",
        "medium": "Director-level engagement — $20,000–$50,000",
        "low": "Manager-level engagement — $5,000–$20,000",
    },
    "linkedin_campaign": {
        "high": "50,000+ impressions — 5–10 qualified leads",
        "medium": "10,000–50,000 impressions — 2–5 leads",
        "low": "1,000–10,000 impressions — 0–2 leads",
    },
}
