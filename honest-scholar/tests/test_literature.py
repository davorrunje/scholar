"""Tests for the citation-graph client + HTTP layer (honest-scholar#1)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from honest_scholar import cli
from honest_scholar.cli import app
from honest_scholar.core import http
from honest_scholar.literature import graph

runner = CliRunner()


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeSession:
    """A routing fake: maps a URL to a queue of responses (or one response)."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.calls.append((url, params))
        payload = self.routes.get(url)
        if isinstance(payload, list):  # a queue of successive responses
            payload = payload.pop(0)
        if isinstance(payload, FakeResponse):
            return payload
        if payload is None:
            return FakeResponse(404, {})
        return FakeResponse(200, payload)


def _client(routes: dict[str, Any], **kw: Any) -> http.HttpClient:
    return http.HttpClient(
        session=FakeSession(routes), sleep=lambda _s: None, cache_dir=None, **kw
    )


# --- HttpClient -------------------------------------------------------------


def test_http_get_json_ok() -> None:
    client = _client({"https://x/y": {"ok": True}})
    assert client.get_json("https://x/y") == {"ok": True}


def test_http_adds_mailto_for_openalex() -> None:
    session = FakeSession({"https://x": {"ok": 1}})
    client = http.HttpClient(session=session, mailto="me@x.org", cache_dir=None)
    client.get_json("https://x")
    assert session.calls[0][1] is not None
    assert session.calls[0][1]["mailto"] == "me@x.org"


def test_http_retries_then_succeeds() -> None:
    session = FakeSession(
        {"https://x": [FakeResponse(429, {}), FakeResponse(200, {"ok": 1})]}
    )
    client = http.HttpClient(session=session, sleep=lambda _s: None, cache_dir=None)
    assert client.get_json("https://x") == {"ok": 1}
    assert len(session.calls) == 2


def test_http_gives_up_and_raises() -> None:
    session = FakeSession({"https://x": FakeResponse(503, {})})
    client = http.HttpClient(
        session=session, sleep=lambda _s: None, cache_dir=None, max_retries=2
    )
    with pytest.raises(http.HttpError, match="giving up"):
        client.get_json("https://x")


def test_http_4xx_is_fatal() -> None:
    client = _client({"https://x": FakeResponse(404, {})})
    with pytest.raises(http.HttpError, match="HTTP 404"):
        client.get_json("https://x")


def test_http_cache_avoids_second_call(tmp_path: Any) -> None:
    session = FakeSession({"https://x": {"n": 1}})
    client = http.HttpClient(session=session, cache_dir=tmp_path)
    assert client.get_json("https://x") == {"n": 1}
    assert client.get_json("https://x") == {"n": 1}
    assert len(session.calls) == 1  # second served from cache


# --- graph ------------------------------------------------------------------


def test_classify() -> None:
    assert graph._classify("W123")[0] == "openalex"
    assert graph._classify("10.1234/abc")[0] == "doi"
    assert graph._classify("doi:10.1234/abc") == ("doi", "10.1234/abc")
    assert graph._classify("arXiv:2205.11775")[0] == "arxiv"
    assert graph._classify("nonsense")[0] == "unknown"


_WORK = {
    "id": "https://openalex.org/W1",
    "doi": "https://doi.org/10.1234/abc",
    "display_name": "A Title",
    "publication_year": 2023,
    "cited_by_count": 42,
    "primary_location": {"source": {"display_name": "ICML"}},
    "authorships": [{"author": {"display_name": "D. Runje"}}],
    "abstract_inverted_index": {"Hello": [0], "world": [1]},
    "referenced_works": ["https://openalex.org/W9", "https://openalex.org/W8"],
}


def test_resolve_openalex() -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    rec = graph.resolve("W1", client=client)
    assert rec["resolved"] is True
    assert rec["openalex"] == "W1"
    assert rec["doi"] == "10.1234/abc"
    assert rec["year"] == 2023


def test_resolve_miss_is_not_fatal() -> None:
    client = _client({})  # 404 for everything
    rec = graph.resolve("W404", client=client)
    assert rec["resolved"] is False
    assert "reason" in rec


def test_enrich_work_reconstructs_abstract() -> None:
    rec = graph.enrich_work(_WORK)
    assert rec["abstract"] == "Hello world"
    assert rec["venue"] == "ICML"
    assert rec["authors"] == ["D. Runje"]


def test_cites_paginates() -> None:
    page1 = {
        "results": [{"id": "https://openalex.org/W2"}],
        "meta": {"next_cursor": "c2"},
    }
    page2 = {
        "results": [{"id": "https://openalex.org/W3"}],
        "meta": {"next_cursor": None},
    }
    client = _client({"https://api.openalex.org/works": [page1, page2]})
    rows = graph.cites("W1", client=client)
    assert [r["id"]["openalex"] for r in rows] == ["W2", "W3"]
    assert rows[0]["provenance"]["via"] == "openalex"


def test_cites_respects_max() -> None:
    page = {
        "results": [{"id": f"https://openalex.org/W{i}"} for i in range(5)],
        "meta": {"next_cursor": None},
    }
    client = _client({"https://api.openalex.org/works": page})
    assert len(graph.cites("W1", client=client, max_results=3)) == 3


def test_refs_reads_referenced_works() -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    assert graph.refs("W1", client=client) == ["W9", "W8"]


def test_enrich_with_context_degrades_without_key() -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    rec = graph.enrich(["W1"], client=client, with_context=True)[0]
    assert rec["degraded"] == ["context", "intent", "is_influential"]


# --- CLI (fake client injected via _lit_client) -----------------------------


def test_cli_resolve(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    monkeypatch.setattr(cli, "_lit_client", lambda: client)
    result = runner.invoke(app, ["literature", "resolve", "W1"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["openalex"] == "W1"


def test_cli_resolve_miss_exits_0_with_resolved_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_lit_client", lambda: _client({}))
    result = runner.invoke(app, ["literature", "resolve", "W404"])
    assert result.exit_code == 0  # resolve reports, never crashes
    assert json.loads(result.stdout)["resolved"] is False


def test_cli_refs_unresolved_exits_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_lit_client", lambda: _client({}))
    result = runner.invoke(app, ["literature", "refs", "W404"])
    assert result.exit_code == 1  # a consuming command needs a resolved id


def test_cli_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    monkeypatch.setattr(cli, "_lit_client", lambda: client)
    result = runner.invoke(app, ["literature", "refs", "W1"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["W9", "W8"]
