"""The ``honest-scholar`` command-line interface.

A Typer command tree mirroring the plugin's skill verbs. ``doctor`` is
implemented; the domain sub-commands are typed stubs pending their tracking
issues (see ADR-0024 and ``docs/design/proposals/tooling-package.md``).
"""

from __future__ import annotations

import dataclasses
import json
import os
import platform
import shutil
import subprocess  # nosec B404 - used only to read `--version` of trusted tools
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from honest_scholar import __version__
from honest_scholar.dataset import manifest as manifest_mod
from honest_scholar.defend import record as record_mod
from honest_scholar.exploration import backlog as backlog_mod
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

    Prints a JSON report ``{ok, errors, warnings}`` and exits non-zero on any
    hard error.

    :param manifest: Path to the manifest to validate.
    :raises typer.Exit: Code 1 on a malformed manifest or any validation error.
    """
    try:
        parsed = manifest_mod.load(manifest)
    except manifest_mod.ManifestError as exc:
        typer.echo(json.dumps({"ok": False, "errors": [str(exc)], "warnings": []}))
        raise typer.Exit(code=1) from exc
    report = manifest_mod.validate(parsed)
    typer.echo(
        json.dumps(
            {"ok": report.ok, "errors": report.errors, "warnings": report.warnings},
            indent=2,
        )
    )
    raise typer.Exit(code=0 if report.ok else 1)


@dataset.command()
def ingest(croissant: str) -> None:
    """Ingest a published Croissant JSON-LD file to bootstrap a draft entry.

    Prints the draft registry entry as JSON, with the human-owned fields it could
    not fill listed under ``_needs_human`` (the caller confirms them on register).

    :param croissant: Path to the Croissant JSON-LD file.
    :raises typer.Exit: Code 1 if the file is unreadable or has no ``name``.
    """
    try:
        doc = json.loads(Path(croissant).read_text(encoding="utf-8"))
        entry = manifest_mod.entry_from_croissant(doc)
    except (OSError, json.JSONDecodeError, manifest_mod.ManifestError) as exc:
        typer.echo(f"ingest failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    draft = dataclasses.asdict(entry)
    draft["_needs_human"] = [
        name
        for name in ("license", "tier", "access", "datasheet", "sensitivity")
        if draft.get(name) is None
    ]
    typer.echo(json.dumps(draft, indent=2))
    raise typer.Exit(code=0)


@dataset.command()
def emit(
    identifier: str,
    manifest: Annotated[
        str, typer.Option(help="Path to the manifest to read.")
    ] = "datasets.yml",
) -> None:
    """Emit a Croissant JSON-LD document for a manifest entry.

    :param identifier: The dataset id to emit (``--all`` for the whole registry).
    :param manifest: Path to the manifest to read.
    :raises typer.Exit: Code 1 if the manifest is malformed or the id is unknown.
    """
    try:
        parsed = manifest_mod.load(manifest)
    except manifest_mod.ManifestError as exc:
        typer.echo(f"emit failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if identifier == "--all":
        typer.echo(
            json.dumps(
                [manifest_mod.croissant_for(e) for e in parsed.datasets], indent=2
            )
        )
        raise typer.Exit(code=0)
    for entry in parsed.datasets:
        if entry.id == identifier:
            typer.echo(json.dumps(manifest_mod.croissant_for(entry), indent=2))
            raise typer.Exit(code=0)
    typer.echo(f"emit failed: no entry with id {identifier!r}", err=True)
    raise typer.Exit(code=1)


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


def _parse_acks(acks: str) -> list[dict[str, str]]:
    """Parse ``"gap::by||gap2::by2"`` into per-gap acknowledgement dicts."""
    result: list[dict[str, str]] = []
    for item in filter(None, (a.strip() for a in acks.split("||"))):
        gap, _, by = item.partition("::")
        result.append({"gap": gap.strip(), "by": by.strip()})
    return result


@defend.command()
def record(
    artifact: Annotated[
        str, typer.Option("--artifact", help="Target markdown artifact.")
    ],
    target: Annotated[
        str, typer.Option("--target", help="claim | cited-work | methodology.")
    ],
    gaps: Annotated[
        str, typer.Option("--gaps", help="Observed gap facts, '||'-separated.")
    ] = "",
    signed_off_by: Annotated[str, typer.Option("--signed-off-by")] = "",
    override: Annotated[bool, typer.Option("--override")] = False,
    acks: Annotated[
        str, typer.Option("--acks", help="Per-gap sign-offs, 'gap::name||…'.")
    ] = "",
    transcript: Annotated[
        str, typer.Option("--transcript", help="Transcript file, or '-' for stdin.")
    ] = "",
    log_dir: Annotated[str, typer.Option("--log-dir")] = str(
        record_mod.DEFAULT_LOG_DIR
    ),
) -> None:
    """Record a ``defend`` examination: patch understanding + append the log.

    Writes ``status.understanding`` into the artifact frontmatter and appends the
    outcome to the accountability log. Records observed facts only — never a
    verdict, score, or answer key.

    :param artifact: The examined markdown artifact.
    :param target: ``claim`` / ``cited-work`` / ``methodology``.
    :param gaps: Observed gap facts, ``||``-separated (empty means no gaps).
    :param signed_off_by: Named human; required when gaps are waved through.
    :param override: A blanket logged override of the surfaced gaps.
    :param acks: Per-gap acknowledgements, ``gap::name``, ``||``-separated.
    :param transcript: Transcript file path, or ``-`` for stdin.
    :param log_dir: Directory for the accountability log.
    :raises typer.Exit: Code 1 on a guard violation or malformed artifact.
    """
    gap_list = [g.strip() for g in gaps.split("||") if g.strip()]
    transcript_text: str | None = None
    if transcript == "-":
        transcript_text = sys.stdin.read()
    elif transcript:
        transcript_text = Path(transcript).read_text(encoding="utf-8")
    try:
        result = record_mod.record(
            artifact,
            target,
            gap_list,
            signed_off_by=signed_off_by or None,
            override=override,
            acknowledgements=_parse_acks(acks),
            transcript=transcript_text,
            log_dir=log_dir,
        )
    except (record_mod.RecordError, OSError) as exc:
        typer.echo(f"defend record failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        json.dumps(
            {
                "outcome": result.outcome,
                "artifact": str(result.artifact),
                "log_entry": str(result.log_entry),
                "transcript": str(result.transcript) if result.transcript else None,
            },
            indent=2,
        )
    )
    raise typer.Exit(code=0)


# --- backlog (honest-scholar#5) ---------------------------------------------------
backlog = typer.Typer(help="Exploration backlog management.", no_args_is_help=True)
app.add_typer(backlog, name="backlog")

_BacklogPath = Annotated[str, typer.Option("--backlog", help="Path to the backlog.")]
_LevelOpt = Annotated[str, typer.Option("--level", help="hypothesis | paper.")]


def _open_backlog(path: str, level: str) -> backlog_mod.Backlog:
    """Validate `level` and load the backlog at `path`.

    :raises typer.Exit: Code 2 on an invalid level.
    """
    if level not in ("hypothesis", "paper"):
        typer.echo(f"--level must be 'hypothesis' or 'paper', got {level!r}", err=True)
        raise typer.Exit(code=2)
    return backlog_mod.Backlog.load(path, level)  # type: ignore[arg-type]


def _emit_row(row: dict[str, str]) -> None:
    """Print one backlog row as JSON and exit 0."""
    typer.echo(json.dumps(row, indent=2))
    raise typer.Exit(code=0)


@backlog.command()
def park(
    one_line: str,
    provenance: Annotated[str, typer.Option("--provenance", help="Origin, verbatim.")],
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
    row_id: Annotated[str, typer.Option("--id", help="Explicit row id.")] = "",
) -> None:
    """Park a raw one-line idea as a ``parked`` backlog row.

    :param one_line: The one-line idea.
    :param provenance: Its origin (verbatim); required.
    :param backlog_path: Path to the backlog table.
    :param level: Backlog level (``hypothesis`` or ``paper``).
    :param row_id: Optional explicit id.
    :raises typer.Exit: Code 1 on a guard violation.
    """
    board = _open_backlog(backlog_path, level)
    try:
        row = board.park(one_line, provenance, row_id=row_id or None)
    except backlog_mod.BacklogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    board.save(backlog_path)
    _emit_row(row)


@backlog.command()
def add(
    one_line: str,
    provenance: Annotated[str, typer.Option("--provenance", help="Origin, verbatim.")],
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
    row_id: Annotated[str, typer.Option("--id", help="Explicit row id.")] = "",
) -> None:
    """Add a ``candidate`` row (realizes the ``generate`` verb).

    :param one_line: The one-line idea.
    :param provenance: Its origin (verbatim); required.
    :param backlog_path: Path to the backlog table.
    :param level: Backlog level (``hypothesis`` or ``paper``).
    :param row_id: Optional explicit id.
    :raises typer.Exit: Code 1 on a guard violation.
    """
    board = _open_backlog(backlog_path, level)
    try:
        row = board.add(one_line, provenance, row_id=row_id or None)
    except backlog_mod.BacklogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    board.save(backlog_path)
    _emit_row(row)


@backlog.command(name="list")
def list_(
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
    status: Annotated[str, typer.Option("--status", help="Filter by status.")] = "",
) -> None:
    """List backlog rows as JSON (read-only), optionally filtered by status.

    :param backlog_path: Path to the backlog table.
    :param level: Backlog level.
    :param status: Optional status filter.
    """
    board = _open_backlog(backlog_path, level)
    rows = board.listing(status=status or None)
    typer.echo(json.dumps(rows, indent=2))
    raise typer.Exit(code=0)


@backlog.command()
def rank(
    row_id: str,
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
    eig: Annotated[str, typer.Option("--eig")] = "",
    feas: Annotated[str, typer.Option("--feas")] = "",
    interest: Annotated[str, typer.Option("--interest")] = "",
    frame: Annotated[str, typer.Option("--frame")] = "",
) -> None:
    """Score a row and set it ``ranked`` (advises; never selects).

    :param row_id: The row to rank.
    :param backlog_path: Path to the backlog table.
    :param level: Backlog level.
    :param eig: Expected-information-gain score (hypothesis level).
    :param feas: Feasibility score.
    :param interest: Interest score.
    :param frame: gap-spotting / problematization (hypothesis level).
    :raises typer.Exit: Code 1 on a guard violation.
    """
    board = _open_backlog(backlog_path, level)
    scores = {
        k: v
        for k, v in (
            ("EIG", eig),
            ("feas", feas),
            ("interest", interest),
            ("frame", frame),
        )
        if v
    }
    try:
        row = board.rank(row_id, **scores)
    except backlog_mod.BacklogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    board.save(backlog_path)
    _emit_row(row)


@backlog.command()
def promote(
    row_id: str,
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
) -> None:
    """Mark a ``ranked`` row ``promoted`` (an explicit human pick).

    Flips the row's status and saves the backlog. Scaffolding the next-stage
    artifact is a follow-up step (``scaffold_hypothesis`` / ``scaffold_paper``).

    :param row_id: The row to promote.
    :param backlog_path: Path to the backlog table.
    :param level: Backlog level.
    :raises typer.Exit: Code 1 on a guard violation.
    """
    board = _open_backlog(backlog_path, level)
    try:
        row = board.promote(row_id)
    except backlog_mod.BacklogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    board.save(backlog_path)
    _emit_row(row)


@backlog.command()
def drop(
    row_id: str,
    reason: Annotated[str, typer.Option("--reason", help="Why it is dropped.")],
    backlog_path: _BacklogPath = "backlog.md",
    level: _LevelOpt = "hypothesis",
) -> None:
    """Retire a row as ``dropped`` with a recorded reason (never deletes it).

    :param row_id: The row to drop.
    :param reason: Why it is dropped; required (file-drawer discipline).
    :param backlog_path: Path to the backlog table.
    :param level: Backlog level.
    :raises typer.Exit: Code 1 on a guard violation.
    """
    board = _open_backlog(backlog_path, level)
    try:
        row = board.drop(row_id, reason)
    except backlog_mod.BacklogError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    board.save(backlog_path)
    _emit_row(row)


if __name__ == "__main__":  # pragma: no cover
    app()
