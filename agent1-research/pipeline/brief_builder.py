from __future__ import annotations

from datetime import UTC, datetime

from config.loader import OutputConfig
from models.article import ScoredArticle


def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _article_row(rank: int, sa: ScoredArticle) -> str:
    a = sa.article
    pub = _format_date(a.published_at)
    summary = a.summary[:200].rstrip()
    if len(a.summary) > 200:
        summary += "…"
    return (
        f"### {rank}. [{a.title}]({a.url})\n"
        f"**Source:** {a.source_name} | **Published:** {pub} | "
        f"**Score:** {sa.score.overall:.2f}\n\n"
        f"{summary}\n"
    )


def _consulting_row(rank: int, sa: ScoredArticle) -> str:
    a = sa.article
    pub = _format_date(a.published_at)
    summary = a.summary[:180].rstrip()
    if len(a.summary) > 180:
        summary += "…"
    return (
        f"### {rank}. [{a.title}]({a.url})\n"
        f"**Source:** {a.source_name} | **Published:** {pub} | "
        f"**Consulting Score:** {sa.score.consulting_opportunity:.2f}\n\n"
        f"{summary}\n"
    )


def _podcast_row(rank: int, sa: ScoredArticle) -> str:
    a = sa.article
    pub = _format_date(a.published_at)
    summary = a.summary[:180].rstrip()
    if len(a.summary) > 180:
        summary += "…"
    return (
        f"### {rank}. [{a.title}]({a.url})\n"
        f"**Source:** {a.source_name} | **Published:** {pub} | "
        f"**Podcast Score:** {sa.score.podcast_potential:.2f}\n\n"
        f"{summary}\n"
    )


def _citation_row(rank: int, sa: ScoredArticle) -> str:
    a = sa.article
    pub = _format_date(a.published_at)
    return f"| {rank} | [{a.title}]({a.url}) | {a.source_name} | {pub} | {sa.score.overall:.2f} |"


def _executive_summary(articles: list[ScoredArticle], cfg: OutputConfig, date_label: str) -> str:
    n = len(articles)
    sources = sorted({sa.article.source_name for sa in articles})
    avg_score = sum(sa.score.overall for sa in articles) / n if n else 0.0
    top_source = max(
        sources,
        key=lambda s: sum(sa.score.overall for sa in articles if sa.article.source_name == s),
        default="—",
    )
    return (
        f"Research period ending **{date_label}** covering **{n} articles** "
        f"from **{len(sources)} sources** (lookback: {cfg.lookback_days} days). "
        f"Average relevance score: **{avg_score:.2f}**. "
        f"Most active source this period: **{top_source}**."
    )


def build_brief(articles: list[ScoredArticle], cfg: OutputConfig) -> str:
    if not articles:
        date_label = datetime.now(UTC).strftime("%Y-%m-%d")
        return (
            f"# Human Workforce AI — Executive Brief\n\n"
            f"**Date:** {date_label}\n\n"
            f"No articles found for this period.\n"
        )

    date_label = datetime.now(UTC).strftime("%Y-%m-%d")
    by_overall = sorted(articles, key=lambda sa: sa.score.overall, reverse=True)
    by_consulting = sorted(articles, key=lambda sa: sa.score.consulting_opportunity, reverse=True)
    by_podcast = sorted(articles, key=lambda sa: sa.score.podcast_potential, reverse=True)

    top_stories = by_overall[: cfg.top_stories]
    top_consulting = by_consulting[: cfg.top_consulting]
    top_podcast = by_podcast[: cfg.top_podcast]
    citations = by_overall[:25]

    lines: list[str] = []

    lines.append("# Human Workforce AI — Executive Brief")
    lines.append(
        f"\n**Date:** {date_label} | **Articles:** {len(articles)} | "
        f"**Sources:** {len({sa.article.source_name for sa in articles})}\n"
    )
    lines.append("---\n")

    lines.append("## Executive Summary\n")
    lines.append(_executive_summary(articles, cfg, date_label))
    lines.append("\n\n---\n")

    lines.append("## Top 10 Stories\n")
    for i, sa in enumerate(top_stories, 1):
        lines.append(_article_row(i, sa))
    lines.append("---\n")

    lines.append("## Top Consulting Opportunities\n")
    for i, sa in enumerate(top_consulting, 1):
        lines.append(_consulting_row(i, sa))
    lines.append("---\n")

    lines.append("## Top Podcast Ideas\n")
    for i, sa in enumerate(top_podcast, 1):
        lines.append(_podcast_row(i, sa))
    lines.append("---\n")

    lines.append("## Source Citations\n")
    lines.append("| # | Title | Source | Published | Score |")
    lines.append("|---|---|---|---|---|")
    for i, sa in enumerate(citations, 1):
        lines.append(_citation_row(i, sa))
    lines.append("")

    return "\n".join(lines)
