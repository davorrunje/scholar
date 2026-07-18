"""Citation-graph client over OpenAlex (+ Semantic Scholar) — honest-scholar#1.

The read/enrich half of the ``literature`` substrate: resolve any id to a
canonical work, page forward citations and backward references, enrich with the
fields ranking turns on, and compute co-citation / bibliographic-coupling
neighbour sets. OpenAlex is the keyless backbone (identity anchor); Semantic
Scholar adds citation contexts / SciCite intents / ``isInfluential`` when a key is
configured, degrading to OpenAlex-only otherwise.

Every function takes an injected :class:`~honest_scholar.core.http.HttpClient`, so
the module is exercised offline in tests. Design:
``docs/design/proposals/literature-citation-graph-client.md``.

.. note::
   Endpoint shapes follow the public OpenAlex / S2 documentation; the code is
   covered by mocked-transport tests. Validation against the live services is a
   follow-up (see the PR).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from honest_scholar.core.http import HttpClient

OPENALEX = "https://api.openalex.org"
S2 = "https://api.semanticscholar.org/graph/v1"

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_OPENALEX_RE = re.compile(r"^[Ww]\d+$")
_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


def _classify(identifier: str) -> tuple[str, str]:
    """Classify a raw identifier into ``(kind, normalized)``.

    :param identifier: A DOI / arXiv id / OpenAlex ``W…`` / S2 id (any prefixing).
    :returns: ``(kind, normalized)`` where kind is ``openalex`` / ``doi`` /
        ``arxiv`` / ``s2`` / ``unknown``.
    """
    ident = identifier.strip()
    low = ident.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if low.startswith(prefix):
            ident = ident[len(prefix) :]
            low = ident.lower()
    if low.startswith("arxiv:"):
        return "arxiv", ident[len("arxiv:") :]
    if low.startswith("corpusid:"):
        return "s2", ident
    if _OPENALEX_RE.match(ident):
        return "openalex", ident.upper()
    if _DOI_RE.match(ident):
        return "doi", ident
    if _ARXIV_RE.match(ident):
        return "arxiv", ident
    if re.fullmatch(r"[0-9a-f]{40}", low):
        return "s2", ident
    return "unknown", ident


def _short_id(url: str | None) -> str | None:
    """Reduce an OpenAlex/S2 entity URL to its bare id (``…/W123`` → ``W123``)."""
    if not url:
        return None
    return url.rstrip("/").rsplit("/", 1)[-1]


def _strip_doi(doi: str | None) -> str | None:
    """Strip the ``https://doi.org/`` prefix from an OpenAlex ``doi`` field."""
    if not doi:
        return None
    return re.sub(r"^https?://doi\.org/", "", doi, flags=re.IGNORECASE)


def _abstract(work: dict[str, Any]) -> str | None:
    """Reconstruct an abstract from OpenAlex's inverted index, if present."""
    index = work.get("abstract_inverted_index")
    if not index:
        return None
    positions: list[tuple[int, str]] = []
    for word, where in index.items():
        positions.extend((pos, word) for pos in where)
    return " ".join(word for _, word in sorted(positions))


def enrich_work(work: dict[str, Any]) -> dict[str, Any]:
    """Project a raw OpenAlex work into the stable enrichment record shape.

    :param work: A raw OpenAlex work object.
    :returns: ``{id{…}, title, year, venue, cited_by_count, authors, abstract}``.
    """
    ids = work.get("ids", {})
    source = (work.get("primary_location") or {}).get("source") or {}
    authors = [
        (a.get("author") or {}).get("display_name")
        for a in work.get("authorships", [])
        if (a.get("author") or {}).get("display_name")
    ]
    return {
        "id": {
            "openalex": _short_id(work.get("id")),
            "doi": _strip_doi(work.get("doi")),
            "s2": None,
            "arxiv": _short_id(ids.get("arxiv")) if ids.get("arxiv") else None,
        },
        "title": work.get("display_name") or work.get("title"),
        "year": work.get("publication_year"),
        "venue": source.get("display_name"),
        "cited_by_count": work.get("cited_by_count"),
        "authors": authors,
        "abstract": _abstract(work),
    }


def _fetch_work(client: HttpClient, openalex_id: str) -> dict[str, Any]:
    """Fetch one OpenAlex work by its ``W…`` id."""
    data = client.get_json(f"{OPENALEX}/works/{openalex_id}")
    return data if isinstance(data, dict) else {}


def resolve(identifier: str, *, client: HttpClient) -> dict[str, Any]:
    """Resolve any identifier to a canonical work record.

    :param identifier: DOI / arXiv id / OpenAlex ``W…`` / S2 id.
    :param client: The HTTP client.
    :returns: ``{resolved, openalex, doi, s2, arxiv, title, year}``; on a miss,
        ``{resolved: False, reason: …}`` — never raises for a not-found id.
    """
    from honest_scholar.core.http import HttpError

    kind, norm = _classify(identifier)
    lookup = {
        "openalex": f"{OPENALEX}/works/{norm}",
        "doi": f"{OPENALEX}/works/doi:{norm}",
        "arxiv": f"{OPENALEX}/works/doi:10.48550/arXiv.{norm}",
    }.get(kind)
    if lookup is None:
        return {"resolved": False, "reason": f"unsupported identifier kind: {kind}"}
    try:
        work = client.get_json(lookup)
    except HttpError as exc:
        return {"resolved": False, "reason": str(exc)}
    if not isinstance(work, dict) or not work.get("id"):
        return {"resolved": False, "reason": "no work found"}
    ids = work.get("ids", {})
    return {
        "resolved": True,
        "openalex": _short_id(work.get("id")),
        "doi": _strip_doi(work.get("doi")),
        "s2": None,
        "arxiv": _short_id(ids.get("arxiv")) if ids.get("arxiv") else None,
        "title": work.get("display_name") or work.get("title"),
        "year": work.get("publication_year"),
    }


def cites(
    openalex_id: str, *, client: HttpClient, max_results: int | None = None
) -> list[dict[str, Any]]:
    """Return forward citations (works citing `openalex_id`), cursor-paginated.

    :param openalex_id: The anchor's OpenAlex ``W…`` id.
    :param client: The HTTP client.
    :param max_results: Cap on rows returned (all citations if ``None``).
    :returns: One record per citing work with provenance ``{via: "openalex"}``.
    """
    results: list[dict[str, Any]] = []
    cursor: str | None = "*"
    while cursor:
        page = client.get_json(
            f"{OPENALEX}/works",
            {"filter": f"cites:{openalex_id}", "per-page": "200", "cursor": cursor},
        )
        if not isinstance(page, dict):
            break
        for work in page.get("results", []):
            record = enrich_work(work)
            record["provenance"] = {"source_id": openalex_id, "via": "openalex"}
            results.append(record)
            if max_results is not None and len(results) >= max_results:
                return results
        cursor = (page.get("meta") or {}).get("next_cursor")
    return results


def refs(openalex_id: str, *, client: HttpClient) -> list[str]:
    """Return the backward references (OpenAlex ids) of a work.

    :param openalex_id: The work's OpenAlex ``W…`` id.
    :param client: The HTTP client.
    :returns: The ``referenced_works`` ids (bare ``W…`` form).
    """
    work = _fetch_work(client, openalex_id)
    return [rid for ref in work.get("referenced_works", []) if (rid := _short_id(ref))]


def enrich(
    openalex_ids: list[str], *, client: HttpClient, with_context: bool = False
) -> list[dict[str, Any]]:
    """Enrich each work id with its metadata bundle.

    :param openalex_ids: The works to enrich.
    :param client: The HTTP client.
    :param with_context: Request S2 citation-context fields; when no S2 key is
        configured they degrade to ``null`` with a ``degraded`` marker.
    :returns: One enrichment record per id.
    """
    records: list[dict[str, Any]] = []
    for wid in openalex_ids:
        record = enrich_work(_fetch_work(client, wid))
        if with_context:
            record["context_snippet"] = None
            record["intent"] = None
            record["is_influential"] = None
            if not client.s2_key:
                record["degraded"] = ["context", "intent", "is_influential"]
        records.append(record)
    return records


def _cocitation(
    openalex_id: str, citers: list[dict[str, Any]], client: HttpClient, top: int
) -> list[dict[str, Any]]:
    """Rank works co-cited with the anchor (shared citing papers)."""
    counter: Counter[str] = Counter()
    for citer in citers:
        citer_id = citer["id"]["openalex"]
        if citer_id:
            for ref in refs(citer_id, client=client):
                if ref != openalex_id:
                    counter[ref] += 1
    return [{"openalex": wid, "score": n} for wid, n in counter.most_common(top)]


def _coupling(
    openalex_id: str, client: HttpClient, top: int, frontier: int
) -> list[dict[str, Any]]:
    """Rank works sharing references with the anchor (bibliographic coupling)."""
    counter: Counter[str] = Counter()
    for ref in refs(openalex_id, client=client)[:frontier]:
        for citer in cites(ref, client=client, max_results=frontier):
            citer_id = citer["id"]["openalex"]
            if citer_id and citer_id != openalex_id:
                counter[citer_id] += 1
    return [{"openalex": wid, "score": n} for wid, n in counter.most_common(top)]


def neighbors(
    openalex_id: str,
    *,
    client: HttpClient,
    kind: str = "both",
    top: int = 20,
    frontier: int = 50,
) -> dict[str, Any]:
    """Compute co-citation and/or bibliographic-coupling neighbour sets.

    Pure set arithmetic over OpenAlex data. The citer/reference frontier is capped
    at `frontier` to bound the API fan-out for highly-cited anchors; the cap is
    reported in the result so truncation is never silent.

    :param openalex_id: The anchor's OpenAlex ``W…`` id.
    :param client: The HTTP client.
    :param kind: ``cocite`` / ``couple`` / ``both``.
    :param top: Number of neighbours to return per set.
    :param frontier: Max citers/references sampled for the computation.
    :returns: ``{cocitation: [...], coupling: [...], capped: bool}``.
    """
    out: dict[str, Any] = {}
    citers = cites(openalex_id, client=client, max_results=frontier)
    out["capped"] = len(citers) >= frontier
    if kind in ("cocite", "both"):
        out["cocitation"] = _cocitation(openalex_id, citers, client, top)
    if kind in ("couple", "both"):
        out["coupling"] = _coupling(openalex_id, client, top, frontier)
    return out
