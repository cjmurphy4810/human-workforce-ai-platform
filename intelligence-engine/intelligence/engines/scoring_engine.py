"""Modular scoring engine with pluggable strategies.

Future AI providers (Claude, NotebookLM, OpenAI, local models) implement
ScoringStrategy to replace or augment the default rule-based scorer.

Usage:
    engine = ScoringEngine()

    # Extend with a custom strategy (e.g. a Claude-backed scorer):
    class ClaudeScorer:
        name = "claude_v1"
        def score_articles(self, articles, opportunity_type): ...

    engine.register(ClaudeScorer())
    scores = engine.score(articles, OpportunityType.CONSULTING, strategy="claude_v1")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from intelligence.models.intelligence import ArticleData, OpportunityType

# ── Public contract ───────────────────────────────────────────────────────────


@dataclass
class ArticleScore:
    article: ArticleData
    score: float       # 0.0–1.0 composite
    confidence: float  # 0.0–1.0 based on article count and score consistency
    strategy: str


@runtime_checkable
class ScoringStrategy(Protocol):
    """Interface for pluggable scoring strategies.

    Implement this Protocol to add a new scoring model without modifying
    any existing code.  Register the implementation with ScoringEngine.register().
    """

    name: str

    def score_articles(
        self,
        articles: list[ArticleData],
        opportunity_type: OpportunityType,
    ) -> list[ArticleScore]: ...


# ── Default rule-based implementation ────────────────────────────────────────


_WEIGHTS: dict[OpportunityType, dict[str, float]] = {
    OpportunityType.CONSULTING: {
        "consulting_opportunity": 0.50,
        "business_impact": 0.30,
        "executive_interest": 0.20,
    },
    OpportunityType.PODCAST: {
        "podcast_potential": 0.60,
        "executive_interest": 0.25,
        "urgency": 0.15,
    },
    OpportunityType.EXECUTIVE_BRIEFING: {
        "executive_interest": 0.50,
        "urgency": 0.30,
        "business_impact": 0.20,
    },
    OpportunityType.BOOK: {
        "business_impact": 0.40,
        "consulting_opportunity": 0.35,
        "executive_interest": 0.25,
    },
    OpportunityType.COURSE: {
        "executive_interest": 0.45,
        "business_impact": 0.35,
        "consulting_opportunity": 0.20,
    },
    OpportunityType.LINKEDIN_CAMPAIGN: {
        "executive_interest": 0.50,
        "business_impact": 0.50,
    },
}


class RuleBasedScoringStrategy:
    """Default scorer: weighted sum of article score dimensions.

    Weights are defined per opportunity type in _WEIGHTS above.
    Business rules are intentionally in this class, not in the engine,
    so they can be overridden by a different strategy without any refactoring.
    """

    name = "rule_based_v1"

    def score_articles(
        self,
        articles: list[ArticleData],
        opportunity_type: OpportunityType,
    ) -> list[ArticleScore]:
        weights = _WEIGHTS.get(opportunity_type, {"overall": 1.0})
        results: list[ArticleScore] = []

        for article in articles:
            raw = sum(
                getattr(article, dim, 0.0) * w for dim, w in weights.items()
            )
            score = min(1.0, max(0.0, raw))

            # Confidence: boosted when multiple dimensions are above threshold
            dims_above = sum(
                1 for dim in weights if getattr(article, dim, 0.0) >= 0.50
            )
            confidence = min(1.0, 0.50 + dims_above * 0.15)

            results.append(ArticleScore(
                article=article,
                score=score,
                confidence=confidence,
                strategy=self.name,
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results


# ── Registry ──────────────────────────────────────────────────────────────────


class ScoringEngine:
    """Central registry for scoring strategies.

    Instantiate once (at application start) and inject wherever scoring is needed.
    Thread-safe for reads; register() should be called before first use.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, ScoringStrategy] = {}
        default = RuleBasedScoringStrategy()
        self.register(default)
        self._default_name = default.name

    def register(self, strategy: ScoringStrategy) -> None:
        """Register (or replace) a named scoring strategy."""
        self._strategies[strategy.name] = strategy

    def available(self) -> list[str]:
        return list(self._strategies.keys())

    def score(
        self,
        articles: list[ArticleData],
        opportunity_type: OpportunityType,
        strategy: str | None = None,
    ) -> list[ArticleScore]:
        name = strategy or self._default_name
        impl = self._strategies.get(name)
        if impl is None:
            raise KeyError(f"Scoring strategy '{name}' is not registered. Available: {self.available()}")
        return impl.score_articles(articles, opportunity_type)
