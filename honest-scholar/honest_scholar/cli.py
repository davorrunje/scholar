"""The ``honest-scholar`` command-line interface.

A Typer command tree mirroring the plugin's skill verbs. ``doctor`` is
implemented; the domain sub-commands are typed stubs pending their tracking
issues (see ADR-0024 and ``docs/design/proposals/tooling-package.md``).
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess  # nosec B404 - used only to read `--version` of trusted tools
from typing import Annotated

import typer

from honest_scholar import __version__
from honest_scholar.exploration import backlog as backlog_mod

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


@literature.command()
def resolve(identifier: str) -> None:
    """Resolve an identifier (DOI, arXiv id, title) to a canonical work.

    :param identifier: The identifier to resolve.
    """
    _not_implemented(1)


@literature.command()
def cites(identifier: str) -> None:
    """List works that cite the given work.

    :param identifier: The work identifier.
    """
    _not_implemented(1)


@literature.command()
def refs(identifier: str) -> None:
    """List the references of the given work.

    :param identifier: The work identifier.
    """
    _not_implemented(1)


@literature.command()
def enrich(identifier: str) -> None:
    """Enrich a work's metadata from external sources.

    :param identifier: The work identifier.
    """
    _not_implemented(1)


@literature.command()
def neighbors(identifier: str) -> None:
    """List citation-graph neighbors of the given work.

    :param identifier: The work identifier.
    """
    _not_implemented(1)


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
