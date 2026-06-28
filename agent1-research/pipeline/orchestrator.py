"""Pipeline orchestrator — single entry point for the full research workflow.

Called by both the CLI (main.py) and the FastAPI service (POST /run).
Business logic stays here; callers only provide config, repo, and output path.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from config.loader import AppConfig
from fetcher.rss import fetch_feeds
from pipeline.brief_builder import build_brief
from pipeline.deduplicator import filter_new, stamp_hashes
from pipeline.scorer import ScoringEngine
from storage.repository import ArticleRepository

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    articles_fetched: int
    articles_new: int
    articles_saved: int
    sources_attempted: int
    sources_succeeded: int
    source_errors: list[tuple[str, str]] = field(default_factory=list)
    save_errors: list[str] = field(default_factory=list)
    brief_path: str = ""
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


async def orchestrate_run(
    config: AppConfig,
    repo: ArticleRepository,
    output_root: Path,
) -> RunResult:
    t0 = time.monotonic()
    save_errors: list[str] = []

    # 1. Fetch
    logger.info("fetching %d sources", len(config.sources))
    fetch_result = await fetch_feeds(config.sources)

    # 2. Hash + dedup
    stamp_hashes(fetch_result.articles)
    existing_hashes = await repo.get_existing_hashes(since_days=config.output.lookback_days * 4)
    new_articles = filter_new(fetch_result.articles, existing_hashes)
    logger.info(
        "dedup: total=%d new=%d skipped=%d",
        len(fetch_result.articles),
        len(new_articles),
        len(fetch_result.articles) - len(new_articles),
    )

    # 3. Score + store
    scorer = ScoringEngine(config.scoring.weights)
    saved = 0
    for article in new_articles:
        scored = scorer.score(article)
        try:
            await repo.save_article(scored)
            saved += 1
        except Exception as exc:
            msg = f"{article.title[:60]}: {exc}"
            logger.warning("save failed: %s", msg)
            save_errors.append(msg)

    # 4. Load lookback window for brief
    brief_articles = await repo.get_recent_articles(config.output.lookback_days)
    logger.info("brief window: %d articles", len(brief_articles))

    # 5. Generate + write brief
    brief_md = build_brief(brief_articles, config.output)
    date_label = datetime.now(UTC).strftime("%Y-%m-%d")
    out_dir = output_root / date_label
    out_dir.mkdir(parents=True, exist_ok=True)
    brief_path = out_dir / "executive_brief.md"
    brief_path.write_text(brief_md, encoding="utf-8")
    logger.info("brief written: %s", brief_path)

    return RunResult(
        articles_fetched=len(fetch_result.articles),
        articles_new=len(new_articles),
        articles_saved=saved,
        sources_attempted=len(config.sources),
        sources_succeeded=fetch_result.sources_succeeded,
        source_errors=fetch_result.source_errors,
        save_errors=save_errors,
        brief_path=str(brief_path),
        duration_seconds=round(time.monotonic() - t0, 2),
    )
