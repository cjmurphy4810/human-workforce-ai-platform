from __future__ import annotations

from datetime import UTC, datetime

from models.article import Article
from pipeline.deduplicator import compute_hash, filter_new, stamp_hashes


def _article(title: str = "Title", url: str = "https://example.com/a") -> Article:
    return Article(
        title=title,
        url=url,
        source_name="Test",
        published_at=datetime.now(UTC),
    )


def test_hash_is_deterministic() -> None:
    assert compute_hash("Hello World", "https://example.com") == compute_hash(
        "Hello World", "https://example.com"
    )


def test_hash_is_case_insensitive() -> None:
    assert compute_hash("HELLO", "https://EXAMPLE.COM") == compute_hash(
        "hello", "https://example.com"
    )


def test_hash_differs_by_url() -> None:
    assert compute_hash("Same Title", "https://a.com") != compute_hash(
        "Same Title", "https://b.com"
    )


def test_stamp_hashes_fills_empty_hash() -> None:
    articles = [_article()]
    result = stamp_hashes(articles)
    assert all(len(a.content_hash) == 64 for a in result)


def test_stamp_hashes_does_not_overwrite_existing() -> None:
    a = _article()
    a.content_hash = "already_set"
    stamp_hashes([a])
    assert a.content_hash == "already_set"


def test_filter_new_removes_existing() -> None:
    a = _article()
    stamp_hashes([a])
    result = filter_new([a], existing_hashes={a.content_hash})
    assert result == []


def test_filter_new_keeps_new() -> None:
    a = _article()
    stamp_hashes([a])
    result = filter_new([a], existing_hashes=set())
    assert len(result) == 1


def test_filter_new_removes_within_batch_duplicates() -> None:
    a1 = _article()
    a2 = _article()  # same title + url
    stamp_hashes([a1, a2])
    result = filter_new([a1, a2], existing_hashes=set())
    assert len(result) == 1


def test_filter_new_preserves_order() -> None:
    articles = [_article(title=f"Article {i}", url=f"https://example.com/{i}") for i in range(5)]
    stamp_hashes(articles)
    result = filter_new(articles, existing_hashes=set())
    assert [a.title for a in result] == [a.title for a in articles]
