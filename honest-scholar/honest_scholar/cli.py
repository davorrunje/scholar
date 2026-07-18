"""The ``honest-scholar`` command-line interface.

A Typer command tree mirroring the plugin's skill verbs. ``doctor`` is
implemented; the domain sub-commands are typed stubs pending their tracking
issues (see ADR-0024 and ``docs/design/proposals/tooling-package.md``).
"""

from __future__ import annotations

import platform
import shutil
import subprocess  # nosec B404 - used only to read `--version` of trusted tools
from typing import Annotated

import typer

from honest_scholar import __version__

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


# --- dataset (honest-scholar#2 / #3) ----------------------------------------------
dataset = typer.Typer(
    help="Dataset manifest, retrieval and mirroring.", no_args_is_help=True
)
app.add_typer(dataset, name="dataset")


@dataset.command()
def register(name: str) -> None:
    """Register a dataset in the thin manifest.

    :param name: Dataset name to register.
    """
    _not_implemented(2)


@dataset.command()
def fetch(name: str) -> None:
    """Fetch a registered dataset via pooch.

    :param name: Dataset name to fetch.
    """
    _not_implemented(3)


@dataset.command()
def verify(name: str) -> None:
    """Verify a fetched dataset against its manifest checksums.

    :param name: Dataset name to verify.
    """
    _not_implemented(3)


@dataset.command()
def mirror(name: str) -> None:
    """Mirror a dataset to private storage via rclone.

    :param name: Dataset name to mirror.
    """
    _not_implemented(3)


@dataset.command()
def audit(name: str) -> None:
    """Audit a dataset's provenance and mirror state.

    :param name: Dataset name to audit.
    """
    _not_implemented(2)


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
