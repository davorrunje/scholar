"""A small caching JSON-over-HTTP client — the package's house HTTP layer.

Wraps ``requests`` with an on-disk, content-addressed response cache (the
provenance root — never silently refreshed within a run) and exponential backoff
on ``429`` / ``5xx``. The transport (`session`) and the sleep function are
injectable so the client is fully testable without touching the network.

Design: ``docs/design/proposals/literature-citation-graph-client.md`` (deps &
posture), ``docs/design/proposals/tooling-package.md`` (house HTTP client).
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlencode

import requests

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

JsonValue = dict[str, Any] | list[Any]


class HttpError(RuntimeError):
    """Raised when a request ultimately fails (after retries) or returns non-JSON."""


class RateLimitError(HttpError):
    """Raised when retries are exhausted on a rate-limit signal.

    The signal is a ``429``, or a ``503`` carrying ``Retry-After``. A distinct
    type so callers can tell a *transient throttle* apart from a permanent miss
    (``404``): a throttle must never be recorded as "not found".
    """


class Response(Protocol):
    """The minimal response shape the client needs (``requests``-compatible)."""

    status_code: int

    @property
    def headers(self) -> Mapping[str, str]:
        """Response headers (read for ``Retry-After``)."""

    def json(self) -> Any:
        """Decode the response body as JSON."""


class Session(Protocol):
    """The minimal session shape the client needs (``requests.Session``)."""

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
    ) -> Response:
        """Issue a GET request."""


def _cache_key(url: str, params: dict[str, str] | None) -> str:
    """Return a stable content-addressed cache key for a URL + params."""
    query = urlencode(sorted((params or {}).items()))
    return hashlib.sha256(f"{url}?{query}".encode()).hexdigest()


def _retry_after_seconds(headers: Mapping[str, str]) -> int | None:
    """Parse a ``Retry-After`` header value as integer seconds, else ``None``.

    :param headers: The response headers.
    :returns: The delay in seconds, or ``None`` when the header is absent or is
        an HTTP-date / otherwise unparsable (in which case the caller falls back
        to exponential backoff).
    """
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        return int(value.strip())
    except ValueError:
        # An HTTP-date (or garbage) — ignore it and fall back to backoff.
        return None


@dataclass
class HttpClient:
    """A caching JSON HTTP client.

    :param cache_dir: Directory for the response cache (no caching if ``None``).
    :param mailto: Email for the OpenAlex polite pool (sent as ``mailto=``).
    :param s2_key: Optional Semantic Scholar API key (sent as ``x-api-key``).
    :param session: The HTTP transport (defaults to a ``requests.Session``).
    :param sleep: Sleep function for backoff (injectable for tests).
    :param timeout: Per-request timeout in seconds.
    :param max_retries: Attempts on ``429`` / ``5xx`` before giving up.
    """

    cache_dir: Path | None = None
    mailto: str | None = None
    s2_key: str | None = None
    session: Session = field(default_factory=requests.Session)
    sleep: object = time.sleep
    timeout: float = 30.0
    max_retries: int = 4

    def _cached(self, key: str) -> JsonValue | None:
        if self.cache_dir is None:
            return None
        path = self.cache_dir / f"{key}.json"
        if path.is_file():
            data: JsonValue = json.loads(path.read_text(encoding="utf-8"))
            return data
        return None

    def _store(self, key: str, value: JsonValue) -> None:
        if self.cache_dir is None:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / f"{key}.json").write_text(json.dumps(value), encoding="utf-8")

    def get_json(
        self,
        url: str,
        params: dict[str, str] | None = None,
        *,
        headers: dict[str, str] | None = None,
        s2: bool = False,
    ) -> JsonValue:
        """GET `url` and return decoded JSON, cache-backed with backoff.

        :param url: The request URL.
        :param params: Query parameters (``mailto`` is added for non-S2 calls).
        :param headers: Extra headers (``x-api-key`` is added when `s2` + a key).
        :param s2: Whether this is a Semantic Scholar call (key/header handling).
        :returns: The decoded JSON document (served from cache when present).
        :raises HttpError: On a non-retryable status, a non-JSON body, or a
            non-rate-limit exhaustion.
        :raises RateLimitError: When retries are exhausted on a rate-limit signal.
        """
        query = dict(params or {})
        if not s2 and self.mailto:
            query.setdefault("mailto", self.mailto)
        request_headers = dict(headers or {})
        if s2 and self.s2_key:
            request_headers.setdefault("x-api-key", self.s2_key)

        key = _cache_key(url, query)
        if (hit := self._cached(key)) is not None:
            return hit

        value = self._fetch(url, query, request_headers)
        self._store(key, value)
        return value

    def _fetch(
        self, url: str, query: dict[str, str], headers: dict[str, str]
    ) -> JsonValue:
        """Issue the request with retries; the network side of :meth:`get_json`.

        Honors ``Retry-After`` on ``429`` / ``503`` (integer seconds); otherwise
        backs off exponentially with jitter. A rate-limit signal (``429``, or a
        ``503`` carrying ``Retry-After``) that survives every retry surfaces as a
        :class:`RateLimitError` so it is never mistaken for a permanent miss.
        """
        last_error = "no attempt made"
        rate_limited = False
        for attempt in range(self.max_retries):
            retry_after: int | None = None
            try:
                resp = self.session.get(
                    url, params=query, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:  # pragma: no cover - network
                last_error = str(exc)
                rate_limited = False
            else:
                if resp.status_code == 200:
                    try:
                        data: JsonValue = resp.json()
                    except (ValueError, json.JSONDecodeError) as exc:
                        raise HttpError(f"{url}: non-JSON response") from exc
                    return data
                if resp.status_code not in (429, 500, 502, 503, 504):
                    raise HttpError(f"{url}: HTTP {resp.status_code}")
                last_error = f"HTTP {resp.status_code}"
                retry_after = _retry_after_seconds(resp.headers)
                rate_limited = resp.status_code == 429 or (
                    resp.status_code == 503 and retry_after is not None
                )
            self.sleep(self._backoff(attempt, retry_after))  # type: ignore[operator]
        detail = f"{url}: giving up after {self.max_retries} attempts ({last_error})"
        if rate_limited:
            raise RateLimitError(detail)
        raise HttpError(detail)

    @staticmethod
    def _backoff(attempt: int, retry_after: int | None) -> float:
        """Return the seconds to sleep before the next attempt.

        :param attempt: The zero-based attempt index.
        :param retry_after: A server-supplied ``Retry-After`` delay, if any.
        :returns: `retry_after` when the server asked for one, else exponential
            backoff (``2**attempt``) with additive jitter to avoid thundering herds.
        """
        if retry_after is not None:
            return float(retry_after)
        return 2.0**attempt + random.uniform(0.0, 1.0)
