from __future__ import annotations

import hashlib


def content_hash(title: str, url: str) -> str:
    """SHA-256 fingerprint of title+url for stable deduplication."""
    payload = f"{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(payload.encode()).hexdigest()
