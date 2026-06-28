"""Shared fixtures for intelligence engine tests."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

# Make intelligence-engine importable in test context
_INTELLIGENCE_DIR = Path(__file__).parents[3] / "intelligence-engine"
if str(_INTELLIGENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_INTELLIGENCE_DIR))

from intelligence.models.intelligence import ArticleData


def _article(
    title: str,
    *,
    business_impact: float = 0.5,
    executive_interest: float = 0.5,
    consulting_opportunity: float = 0.5,
    podcast_potential: float = 0.5,
    urgency: float = 0.5,
    overall: float = 0.5,
    source: str = "Test Source",
    days_ago: int = 5,
    url: str | None = None,
) -> ArticleData:
    return ArticleData(
        title=title,
        url=url or f"https://example.com/{title.replace(' ', '-').lower()}",
        source_name=source,
        published_at=datetime.now(UTC) - timedelta(days=days_ago),
        summary=f"Summary of {title}. This discusses {title.lower()} in detail.",
        business_impact=business_impact,
        executive_interest=executive_interest,
        consulting_opportunity=consulting_opportunity,
        podcast_potential=podcast_potential,
        urgency=urgency,
        overall=overall,
    )


@pytest.fixture
def high_consulting_articles() -> list[ArticleData]:
    return [
        _article(
            f"AI Governance Framework Article {i}",
            consulting_opportunity=0.80,
            business_impact=0.75,
            executive_interest=0.70,
            overall=0.75,
        )
        for i in range(5)
    ]


@pytest.fixture
def high_podcast_articles() -> list[ArticleData]:
    return [
        _article(
            f"Future of Work Podcast Topic {i}",
            podcast_potential=0.82,
            executive_interest=0.65,
            overall=0.70,
        )
        for i in range(4)
    ]


@pytest.fixture
def mixed_articles() -> list[ArticleData]:
    return [
        _article("AI Strategy High", consulting_opportunity=0.85, business_impact=0.80, executive_interest=0.75, overall=0.80),
        _article("Podcast Worthy Topic", podcast_potential=0.88, executive_interest=0.65, overall=0.72),
        _article("Board Level Briefing", executive_interest=0.80, business_impact=0.75, urgency=0.70, overall=0.78),
        _article("Low Score Article", business_impact=0.10, executive_interest=0.10, consulting_opportunity=0.10, podcast_potential=0.10, urgency=0.10, overall=0.10),
        _article("Machine Learning Operations", business_impact=0.65, consulting_opportunity=0.60, executive_interest=0.55, overall=0.60),
        _article("Generative AI Enterprise Use", executive_interest=0.70, business_impact=0.68, consulting_opportunity=0.72, overall=0.70),
    ]


@pytest.fixture
def trending_articles() -> list[ArticleData]:
    """Articles spanning two time windows to trigger trend detection."""
    recent = [
        _article(f"Machine Learning Operations New {i}", business_impact=0.65, overall=0.60, days_ago=3)
        for i in range(5)
    ]
    baseline = [
        _article(f"Old Topic Legacy {i}", business_impact=0.50, overall=0.50, days_ago=20)
        for i in range(6)
    ]
    return recent + baseline
