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


# --- graph internals & CLI (coverage sweep, honest-scholar#16) ---------------


def test_classify_all_kinds() -> None:
    assert graph._classify("2205.11775")[0] == "arxiv"
    assert graph._classify("CorpusId:12345") == ("s2", "CorpusId:12345")
    assert graph._classify("0" * 40)[0] == "s2"
    assert graph._classify("https://doi.org/10.1234/x") == ("doi", "10.1234/x")


def test_helper_edges() -> None:
    assert graph._short_id(None) is None
    assert graph._strip_doi(None) is None
    assert graph._strip_doi("HTTPS://doi.org/10.1/x") == "10.1/x"
    assert graph._abstract({}) is None  # no inverted index


def test_resolve_arxiv_builds_doi_lookup() -> None:
    work = {
        "id": "https://openalex.org/W7",
        "display_name": "T",
        "publication_year": 2022,
    }
    client = _client(
        {"https://api.openalex.org/works/doi:10.48550/arXiv.2205.11775": work}
    )
    rec = graph.resolve("arXiv:2205.11775", client=client)
    assert rec["resolved"] is True
    assert rec["openalex"] == "W7"


def test_resolve_unknown_kind() -> None:
    rec = graph.resolve("not-an-id!!", client=_client({}))
    assert rec["resolved"] is False
    assert "unsupported" in rec["reason"]


def test_resolve_empty_body_is_miss() -> None:
    client = _client({"https://api.openalex.org/works/W1": {}})  # no 'id'
    assert graph.resolve("W1", client=client)["resolved"] is False


def test_cites_non_dict_page_stops() -> None:
    client = _client({"https://api.openalex.org/works": ["not-a-dict"]})
    assert graph.cites("W1", client=client) == []


def test_enrich_without_context() -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK})
    rec = graph.enrich(["W1"], client=client)[0]
    assert "degraded" not in rec
    assert rec["title"] == "A Title"


def test_enrich_with_context_and_key_no_degraded() -> None:
    client = _client({"https://api.openalex.org/works/W1": _WORK}, s2_key="k")
    rec = graph.enrich(["W1"], client=client, with_context=True)[0]
    assert "degraded" not in rec
    assert rec["context_snippet"] is None


def test_neighbors_both() -> None:
    oa = "https://api.openalex.org"
    w1 = {
        "id": f"{oa[:-1]}",
        "referenced_works": ["https://openalex.org/W9", "https://openalex.org/W8"],
    }
    w1["id"] = "https://openalex.org/W1"
    w2 = {
        "id": "https://openalex.org/W2",
        "referenced_works": ["https://openalex.org/W9", "https://openalex.org/W99"],
    }
    page_w1 = {
        "results": [{"id": "https://openalex.org/W2"}],
        "meta": {"next_cursor": None},
    }
    page_w9 = {
        "results": [{"id": "https://openalex.org/W2"}],
        "meta": {"next_cursor": None},
    }
    page_w8 = {
        "results": [{"id": "https://openalex.org/W3"}],
        "meta": {"next_cursor": None},
    }
    routes = {
        f"{oa}/works": [page_w1, page_w9, page_w8],
        f"{oa}/works/W1": w1,
        f"{oa}/works/W2": w2,
    }
    out = graph.neighbors("W1", client=_client(routes), kind="both", top=5, frontier=10)
    cocite = {n["openalex"] for n in out["cocitation"]}
    coupling = {n["openalex"] for n in out["coupling"]}
    assert cocite == {"W9", "W99"}
    assert coupling == {"W2", "W3"}
    assert out["capped"] is False


def test_cli_cites_and_neighbors(monkeypatch: pytest.MonkeyPatch) -> None:
    oa = "https://api.openalex.org"
    page = {
        "results": [{"id": "https://openalex.org/W2"}],
        "meta": {"next_cursor": None},
    }
    routes = {f"{oa}/works/W1": _WORK, f"{oa}/works": page, f"{oa}/works/W2": _WORK}
    monkeypatch.setattr(cli, "_lit_client", lambda: _client(routes))
    cites = runner.invoke(app, ["literature", "cites", "W1", "--max", "5"])
    assert cites.exit_code == 0
    assert json.loads(cites.stdout)[0]["id"]["openalex"] == "W2"
    nb = runner.invoke(
        app, ["literature", "neighbors", "W1", "--kind", "cocite", "--top", "3"]
    )
    assert nb.exit_code == 0
    assert "cocitation" in json.loads(nb.stdout)


def test_cli_enrich(monkeypatch: pytest.MonkeyPatch) -> None:
    routes = {"https://api.openalex.org/works/W1": _WORK}
    monkeypatch.setattr(cli, "_lit_client", lambda: _client(routes))
    result = runner.invoke(app, ["literature", "enrich", "W1", "--context"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["title"] == "A Title"


def test_cli_cites_unresolved_exits_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_lit_client", lambda: _client({}))
    assert runner.invoke(app, ["literature", "cites", "W404"]).exit_code == 1


def test_lit_client_builds_from_config(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
    monkeypatch.setenv("OPENALEX_MAILTO", "me@x.org")
    client = cli._lit_client()
    assert client.mailto == "me@x.org"


class _BadJSON(FakeResponse):
    def json(self) -> object:
        raise ValueError("not json")


def test_http_s2_key_branch() -> None:
    client = http.HttpClient(
        session=FakeSession({"https://s2": {"ok": 1}}), s2_key="secret", cache_dir=None
    )
    assert client.get_json("https://s2", s2=True) == {"ok": 1}


def test_http_non_json_raises() -> None:
    client = http.HttpClient(
        session=FakeSession({"https://x": _BadJSON(200, None)}), cache_dir=None
    )
    with pytest.raises(http.HttpError, match="non-JSON"):
        client.get_json("https://x")


def test_neighbors_cocite_skips_idless_citer_and_self_ref() -> None:
    oa = "https://api.openalex.org"
    # citer 1 has no openalex id (skipped); citer 2 cites only the anchor (skipped).
    page = {
        "results": [{"id": None}, {"id": "https://openalex.org/W2"}],
        "meta": {"next_cursor": None},
    }
    w2 = {
        "id": "https://openalex.org/W2",
        "referenced_works": ["https://openalex.org/W1"],
    }
    out = graph.neighbors(
        "W1",
        client=_client({f"{oa}/works": [page], f"{oa}/works/W2": w2}),
        kind="cocite",
        frontier=10,
    )
    assert out["cocitation"] == []


def test_neighbors_couple_only_skips_self_citer() -> None:
    oa = "https://api.openalex.org"
    w1 = {"id": f"{oa[:-1]}/W1", "referenced_works": ["https://openalex.org/W9"]}
    anchor_cites = {"results": [], "meta": {"next_cursor": None}}
    w9_cites = {
        "results": [
            {"id": "https://openalex.org/W1"},
            {"id": "https://openalex.org/W2"},
        ],
        "meta": {"next_cursor": None},
    }
    routes = {f"{oa}/works": [anchor_cites, w9_cites], f"{oa}/works/W1": w1}
    out = graph.neighbors("W1", client=_client(routes), kind="couple", frontier=10)
    assert out["coupling"] == [{"openalex": "W2", "score": 1}]  # self W1 skipped
    assert "cocitation" not in out
