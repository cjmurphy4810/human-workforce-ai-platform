from __future__ import annotations

import hashlib

from models.article import Article


def compute_hash(title: str, url: str) -> str:
    key = f"{title.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def stamp_hashes(articles: list[Article]) -> list[Article]:
    for a in articles:
        if not a.content_hash:
            a.content_hash = compute_hash(a.title, a.url)
    return articles


def filter_new(articles: list[Article], existing_hashes: set[str]) -> list[Article]:
    seen: set[str] = set()
    result: list[Article] = []
    for article in articles:
        h = article.content_hash
        if h and h not in existing_hashes and h not in seen:
            seen.add(h)
            result.append(article)
    return result
