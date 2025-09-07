"""
URL normalization helpers for Pydantic v2 compatibility.

Pydantic v2 `HttpUrl` / `AnyUrl` fields are `pydantic_core.Url` objects.
Those objects do not expose string methods like `.rstrip()`. Always coerce to
`str` before doing string operations or passing to HTTP clients.
"""

from __future__ import annotations

from typing import Any


def normalize_url(value: Any) -> str:
    """Coerce any URL-like value to a trimmed string.

    - Safely handles `pydantic_core.Url` by casting to `str`.
    - Strips surrounding whitespace.
    """

    return str(value).strip() if value is not None else ""


def ensure_no_trailing_slash(value: Any) -> str:
    """Return URL string without a trailing slash.

    Example: "https://example.com/" -> "https://example.com"
    """

    return normalize_url(value).rstrip("/")


def ensure_trailing_slash(value: Any) -> str:
    """Return URL string guaranteed to end with a single trailing slash."""

    base = ensure_no_trailing_slash(value)
    return f"{base}/" if base else base


def join_url(base: Any, path: str | None) -> str:
    """Join base URL and path with exactly one slash between them.

    - Does not add a trailing slash if `path` is empty/None.
    - Does not strip query or fragment from `path`.
    """

    b = ensure_no_trailing_slash(base)
    if not path:
        return b
    p = str(path).lstrip("/")
    return f"{b}/{p}" if b else f"/{p}"


__all__ = [
    "normalize_url",
    "ensure_no_trailing_slash",
    "ensure_trailing_slash",
    "join_url",
]

