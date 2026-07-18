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
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlencode

import requests

if TYPE_CHECKING:
    from pathlib import Path

JsonValue = dict[str, Any] | list[Any]


class HttpError(RuntimeError):
    """Raised when a request ultimately fails (after retries) or returns non-JSON."""


class Response(Protocol):
    """The minimal response shape the client needs (``requests``-compatible)."""

    status_code: int

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
        :raises HttpError: On repeated failure or a non-JSON body.
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
        """Issue the request with retries; the network side of :meth:`get_json`."""
        last_error = "no attempt made"
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(
                    url, params=query, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:  # pragma: no cover - network
                last_error = str(exc)
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
            backoff = 2.0**attempt
            self.sleep(backoff)  # type: ignore[operator]
        raise HttpError(
            f"{url}: giving up after {self.max_retries} attempts ({last_error})"
        )
