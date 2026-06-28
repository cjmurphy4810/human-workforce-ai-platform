#!/usr/bin/env python3
"""Human Workforce Research Agent — CLI entry point.

Usage:
    python main.py
    python main.py --config config/config.yaml --log-level DEBUG
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Put agent1-research/ on the import path so sub-packages resolve when this
# script is invoked directly from any working directory.
_HERE = Path(__file__).parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from config.loader import load_config
from pipeline.orchestrator import orchestrate_run
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
        default=_HERE / "output",
        help="Output root directory (default: output/)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
    config = load_config(args.config)

    if args.db.startswith("sqlite"):
        db_file = args.db.split("///")[-1]
        if db_file and db_file != ":memory:":
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    engine = build_engine(args.db)
    await init_db(engine)
    repo = ArticleRepository(build_session_factory(engine))

    result = await orchestrate_run(config, repo, args.output)
    await engine.dispose()

    sep = "─" * 56
    print(f"\n{sep}")
    print("  Executive Brief ready")
    print(f"  {result.brief_path}")
    print(
        f"  fetched={result.articles_fetched}  new={result.articles_new}  "
        f"sources={result.sources_succeeded}/{result.sources_attempted}  "
        f"time={result.duration_seconds}s"
    )
    print(f"{sep}\n")


def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
