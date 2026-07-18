"""The ``honest-scholar`` command-line interface.

A Typer command tree mirroring the plugin's skill verbs. ``doctor`` is
implemented; the domain sub-commands are typed stubs pending their tracking
issues (see ADR-0024 and ``docs/design/proposals/tooling-package.md``).
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess  # nosec B404 - used only to read `--version` of trusted tools
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from honest_scholar import __version__
from honest_scholar.literature import graph as graph_mod

if TYPE_CHECKING:
    from honest_scholar.core.http import HttpClient

app = typer.Typer(
    name="honest-scholar",
    help="Supporting tooling for the honest-scholar research-workflow plugin.",
    no_args_is_help=True,
    add_completion=False,
)


def _not_implemented(issue: int) -> None:
    """Emit the standard not-yet-implemented notice and exit.

    :param issue: The tracking issue number in the ``honest-scholar`` repo.
    :raises typer.Exit: Always, with code 2.
    """
    typer.echo(f"not yet implemented — see honest-scholar#{issue}")
    raise typer.Exit(code=2)


def _version_callback(value: bool) -> None:
    """Print the package version and exit when ``--version`` is given.

    :param value: Whether the ``--version`` flag was supplied.
    :raises typer.Exit: With code 0 after printing, when `value` is true.
    """
    if value:
        typer.echo(__version__)
        raise typer.Exit(code=0)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the honest-scholar version and exit.",
        ),
    ] = False,
) -> None:
    """honest-scholar — research-workflow tooling CLI."""


def _tool_report(name: str) -> str:
    """Report the presence and version of an external tool on ``PATH``.

    Absence is reported, not treated as an error.

    :param name: Executable name to look up via :func:`shutil.which`.
    :returns: A human-readable one-line status string.
    """
    path = shutil.which(name)
    if path is None:
        return f"{name}: not found"
    try:
        proc = subprocess.run(  # nosec B603 - `path` resolved from PATH; fixed args
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - defensive
        return f"{name}: found ({path}), version unknown"
    output = (proc.stdout or proc.stderr).strip().splitlines()
    detail = output[0] if output else "version unknown"
    return f"{name}: {detail} ({path})"


@app.command()
def doctor() -> None:
    """Report the local environment: Python, ``uv`` and ``rclone``.

    Prints a short diagnostic report. Missing optional tools (``uv``,
    ``rclone``) are reported, not treated as failures. Always exits 0.
    """
    typer.echo("honest-scholar doctor")
    typer.echo(f"  honest-scholar: {__version__}")
    typer.echo(f"  python: {platform.python_version()} ({platform.platform()})")
    typer.echo(f"  {_tool_report('uv')}")
    typer.echo(f"  {_tool_report('rclone')}")
    raise typer.Exit(code=0)


# --- literature (honest-scholar#1) ------------------------------------------------
literature = typer.Typer(
    help="Citation-graph and metadata tools.", no_args_is_help=True
)
app.add_typer(literature, name="literature")


def _lit_client() -> HttpClient:
    """Build the literature HTTP client from config + environment.

    Reads ``literature.mailto`` from ``.honest-scholar/config.yml`` (polite pool)
    and ``S2_API_KEY`` from the environment; caches responses under
    ``.honest-scholar/cache/http``. Tests monkeypatch this to inject a fake client.
    """
    from honest_scholar.core.config import load_config
    from honest_scholar.core.http import HttpClient

    config = load_config()
    lit = config.get("literature")
    mailto = lit.get("mailto") if isinstance(lit, dict) else None
    return HttpClient(
        cache_dir=Path(".honest-scholar/cache/http"),
        mailto=mailto or os.environ.get("OPENALEX_MAILTO"),
        s2_key=os.environ.get("S2_API_KEY"),
    )


def _openalex_id(client: HttpClient, identifier: str) -> str:
    """Resolve `identifier` to an OpenAlex id, or exit 1 if it cannot resolve."""
    record = graph_mod.resolve(identifier, client=client)
    if not record.get("resolved") or not record.get("openalex"):
        typer.echo(
            f"could not resolve {identifier!r}: {record.get('reason')}", err=True
        )
        raise typer.Exit(code=1)
    return str(record["openalex"])


@literature.command()
def resolve(identifier: str) -> None:
    """Resolve an identifier (DOI, arXiv id, OpenAlex/S2 id) to a canonical work.

    :param identifier: The identifier to resolve.
    """
    typer.echo(
        json.dumps(graph_mod.resolve(identifier, client=_lit_client()), indent=2)
    )
    raise typer.Exit(code=0)


@literature.command()
def cites(
    identifier: str,
    max_results: Annotated[int, typer.Option("--max", help="Cap on rows.")] = 0,
) -> None:
    """List works that cite the given work (JSON array).

    :param identifier: The work identifier.
    :param max_results: Optional cap on the number of rows (0 = all).
    """
    client = _lit_client()
    rows = graph_mod.cites(
        _openalex_id(client, identifier),
        client=client,
        max_results=max_results or None,
    )
    typer.echo(json.dumps(rows, indent=2))
    raise typer.Exit(code=0)


@literature.command()
def refs(identifier: str) -> None:
    """List the backward references (OpenAlex ids) of the given work.

    :param identifier: The work identifier.
    """
    client = _lit_client()
    typer.echo(
        json.dumps(graph_mod.refs(_openalex_id(client, identifier), client=client))
    )
    raise typer.Exit(code=0)


@literature.command()
def enrich(
    identifiers: list[str],
    with_context: Annotated[bool, typer.Option("--context")] = False,
) -> None:
    """Enrich one or more works with their metadata bundle (JSON array).

    :param identifiers: The work identifiers to enrich.
    :param with_context: Request S2 citation-context fields (degrades w/o a key).
    """
    client = _lit_client()
    ids = [_openalex_id(client, ident) for ident in identifiers]
    rows = graph_mod.enrich(ids, client=client, with_context=with_context)
    typer.echo(json.dumps(rows, indent=2))
    raise typer.Exit(code=0)


@literature.command()
def neighbors(
    identifier: str,
    kind: Annotated[
        str, typer.Option("--kind", help="cocite | couple | both.")
    ] = "both",
    top: Annotated[int, typer.Option("--top")] = 20,
) -> None:
    """List co-citation / bibliographic-coupling neighbours of the given work.

    :param identifier: The work identifier.
    :param kind: ``cocite`` / ``couple`` / ``both``.
    :param top: Number of neighbours per set.
    """
    client = _lit_client()
    result = graph_mod.neighbors(
        _openalex_id(client, identifier), client=client, kind=kind, top=top
    )
    typer.echo(json.dumps(result, indent=2))
    raise typer.Exit(code=0)


# --- dataset (honest-scholar#2 manifest / #3 retrieval) ---------------------------
dataset = typer.Typer(
    help="Dataset manifest, retrieval and mirroring.", no_args_is_help=True
)
app.add_typer(dataset, name="dataset")


@dataset.command()
def validate(
    manifest: Annotated[
        str, typer.Argument(help="Path to the manifest to validate.")
    ] = "datasets.yml",
) -> None:
    """Validate a ``datasets.yml`` manifest (the register/audit gate).

    :param manifest: Path to the manifest to validate.
    """
    _not_implemented(2)


@dataset.command()
def ingest(croissant: str) -> None:
    """Ingest a published Croissant JSON-LD file to bootstrap a manifest entry.

    :param croissant: Path to the Croissant JSON-LD file.
    """
    _not_implemented(2)


@dataset.command()
def emit(identifier: str) -> None:
    """Emit a Croissant JSON-LD file for a manifest entry.

    :param identifier: The dataset id to emit (or ``--all`` in a later revision).
    """
    _not_implemented(2)


@dataset.command()
def fetch(identifier: str) -> None:
    """Fetch a registered dataset through the resolution chain (pooch/rclone).

    :param identifier: The dataset id to fetch.
    """
    _not_implemented(3)


@dataset.command()
def verify(identifier: str) -> None:
    """Verify on-disk bytes against the manifest SHA-256 (offline).

    :param identifier: The dataset id to verify.
    """
    _not_implemented(3)


@dataset.command()
def mirror(identifier: str) -> None:
    """Populate/refresh the private rclone mirror for a dataset.

    :param identifier: The dataset id to mirror.
    """
    _not_implemented(3)


@dataset.command()
def audit(
    identifier: Annotated[
        str, typer.Argument(help="Optional dataset id; whole manifest if omitted.")
    ] = "",
) -> None:
    """Audit fixity, mirror presence and manifest completeness.

    :param identifier: Optional dataset id; audits the whole manifest if omitted.
    """
    _not_implemented(3)


# --- defend (honest-scholar#4) ----------------------------------------------------
defend = typer.Typer(help="Defensibility record helpers.", no_args_is_help=True)
app.add_typer(defend, name="defend")


@defend.command()
def record(claim: str) -> None:
    """Record a defensibility entry for a claim or decision.

    :param claim: The claim or decision to record.
    """
    _not_implemented(4)


# --- backlog (honest-scholar#5) ---------------------------------------------------
backlog = typer.Typer(help="Exploration backlog management.", no_args_is_help=True)
app.add_typer(backlog, name="backlog")


@backlog.command()
def park(item: str) -> None:
    """Park a raw one-line idea as a backlog row before it is lost.

    :param item: The one-line idea (its origin/provenance is required).
    """
    _not_implemented(5)


@backlog.command()
def add(item: str) -> None:
    """Add an item to the exploration backlog.

    :param item: The backlog item description.
    """
    _not_implemented(5)


@backlog.command(name="list")
def list_() -> None:
    """List the current exploration backlog."""
    _not_implemented(5)


@backlog.command()
def rank() -> None:
    """Rank the exploration backlog by priority."""
    _not_implemented(5)


@backlog.command()
def promote(item: str) -> None:
    """Promote a backlog item to an active investigation.

    :param item: The backlog item identifier.
    """
    _not_implemented(5)


@backlog.command()
def drop(item: str) -> None:
    """Drop an item from the exploration backlog.

    :param item: The backlog item identifier.
    """
    _not_implemented(5)


if __name__ == "__main__":  # pragma: no cover
    app()
