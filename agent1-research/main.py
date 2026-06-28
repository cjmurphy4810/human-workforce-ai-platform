#!/usr/bin/env python3
"""Human Workforce Research Agent — vertical slice entry point.

Usage:
    python main.py
    python main.py --config config/config.yaml --log-level DEBUG
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Put agent1-research/ on the import path so sub-packages resolve when this
# script is invoked directly from any working directory.
_HERE = Path(__file__).parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from config.loader import load_config
from fetcher.rss import fetch_feeds
from pipeline.brief_builder import build_brief
from pipeline.deduplicator import filter_new, stamp_hashes
from pipeline.scorer import ScoringEngine
from storage.database import build_engine, build_session_factory, init_db
from storage.repository import ArticleRepository


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="Fetch RSS feeds, score articles, generate Executive Brief.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_HERE / "config" / "config.yaml",
        help="Path to YAML config (default: config/config.yaml)",
    )
    parser.add_argument(
        "--db",
        default=f"sqlite+aiosqlite:///{_HERE / 'data' / 'research.db'}",
        help="SQLAlchemy async DB URL",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output root directory (overrides config)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


async def run(config_path: Path, db_url: str, output_root: Path) -> Path:
    logger = logging.getLogger(__name__)
    config = load_config(config_path)
    out_cfg = config.output

    # Ensure SQLite directory exists
    if db_url.startswith("sqlite"):
        db_file = db_url.split("///")[-1]
        if db_file and db_file != ":memory:":
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    engine = build_engine(db_url)
    await init_db(engine)
    repo = ArticleRepository(build_session_factory(engine))

    # 1. Fetch
    logger.info("Fetching %d RSS sources…", len(config.sources))
    articles = await fetch_feeds(config.sources)
    logger.info("Total articles fetched: %d", len(articles))

    # 2. Hash + deduplicate
    stamp_hashes(articles)
    existing_hashes = await repo.get_existing_hashes(since_days=out_cfg.lookback_days * 4)
    new_articles = filter_new(articles, existing_hashes)
    logger.info("New articles after dedup: %d (skipped %d)", len(new_articles), len(articles) - len(new_articles))

    # 3. Score + store
    scorer = ScoringEngine(config.scoring.weights)
    scored_new = [scorer.score(a) for a in new_articles]
    for sa in scored_new:
        try:
            sa.db_id = await repo.save_article(sa)
        except Exception as exc:
            logger.warning("Could not save article '%s': %s", sa.article.title[:60], exc)

    # 4. Load full lookback window for brief
    brief_articles = await repo.get_recent_articles(out_cfg.lookback_days)
    logger.info("Articles in brief window: %d", len(brief_articles))

    # 5. Generate brief
    brief_md = build_brief(brief_articles, out_cfg)

    # 6. Write output
    date_label = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = output_root / date_label
    out_dir.mkdir(parents=True, exist_ok=True)
    brief_path = out_dir / "executive_brief.md"
    brief_path.write_text(brief_md, encoding="utf-8")

    await engine.dispose()
    return brief_path


def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)

    output_root = args.output or (_HERE / args.config.parent.parent / "output")
    if args.output is None:
        output_root = _HERE / "output"

    brief_path = asyncio.run(run(args.config, args.db, output_root))

    sep = "─" * 56
    print(f"\n{sep}")
    print(f"  Executive Brief ready")
    print(f"  {brief_path}")
    print(f"{sep}\n")


if __name__ == "__main__":
    main()
