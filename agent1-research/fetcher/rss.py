from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from config.loader import SourceConfig
from models.article import Article

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", _HTML_TAG_RE.sub(" ", text)).strip()


def _parse_date(entry: feedparser.FeedParserDict) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _entry_to_article(entry: feedparser.FeedParserDict, source: SourceConfig) -> Optional[Article]:
    title = _strip_html(getattr(entry, "title", "")).strip()
    url = getattr(entry, "link", "").strip()
    if not title or not url:
        return None

    summary_raw = getattr(entry, "summary", "") or ""
    summary = _strip_html(summary_raw)[:500]

    return Article(
        title=title,
        url=url,
        source_name=source.name,
        source_weight=source.weight,
        published_at=_parse_date(entry),
        summary=summary,
    )


def _fetch_feed_sync(url: str) -> feedparser.FeedParserDict:
    return feedparser.parse(url, agent="HumanWorkforceAI/1.0")


async def fetch_source(source: SourceConfig) -> list[Article]:
    feed = await asyncio.to_thread(_fetch_feed_sync, source.url)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Feed parse error: {feed.bozo_exception}")

    articles: list[Article] = []
    for entry in feed.entries:
        article = _entry_to_article(entry, source)
        if article:
            articles.append(article)

    return articles


class FetchResult:
    __slots__ = ("articles", "sources_succeeded", "source_errors")

    def __init__(
        self,
        articles: list[Article],
        sources_succeeded: int,
        source_errors: list[tuple[str, str]],
    ) -> None:
        self.articles = articles
        self.sources_succeeded = sources_succeeded
        self.source_errors = source_errors  # [(source_name, error_msg), ...]


async def fetch_feeds(sources: list[SourceConfig]) -> FetchResult:
    tasks = [fetch_source(s) for s in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles: list[Article] = []
    source_errors: list[tuple[str, str]] = []
    succeeded = 0

    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            msg = str(result)
            logger.warning("fetch failed: source=%s error=%s", source.name, msg)
            source_errors.append((source.name, msg))
        else:
            logger.info("fetched: source=%s count=%d", source.name, len(result))
            articles.extend(result)
            succeeded += 1

    return FetchResult(
        articles=articles,
        sources_succeeded=succeeded,
        source_errors=source_errors,
    )
