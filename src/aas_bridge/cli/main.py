"""Typer CLI entry point for ``aas-bridge``.

Five commands: ``check``, ``migrate``, ``smia``, ``update`` and ``shell``. A
bare ``aas-bridge`` invocation opens the interactive shell. The commands are
thin wrappers: every implementation lives in :mod:`aas_bridge.cli.actions`, and
the REPL dispatches to the same functions. Every runtime string comes from
:mod:`aas_bridge.cli.i18n` in English or Spanish.
"""

from __future__ import annotations

from pathlib import Path

import typer

from aas_bridge import __version__
from aas_bridge.cli import actions, i18n, repl
from aas_bridge.cli.smia_cmd import smia as smia_command
from aas_bridge.cli.update_cmd import update as update_command
from aas_bridge.engine.detect import detect_versions
from aas_bridge.engine.gate import run_migration

EXIT_OK = actions.EXIT_OK
EXIT_INPUT = actions.EXIT_INPUT
EXIT_USAGE = actions.EXIT_USAGE
EXIT_GATE = actions.EXIT_GATE
EXIT_INTERNAL = actions.EXIT_INTERNAL

_HELP_LANG = i18n.default_language()


def _t(key: str, **parameters: object) -> str:
    return i18n.translate(key, _HELP_LANG, **parameters)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(i18n.translate("version", _HELP_LANG, version=__version__))
        raise typer.Exit(code=EXIT_OK)


app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
    help=_t("app.help"),
)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help=_t("help.version"),
    ),
) -> None:
    """AAS Bridge command-line interface."""
    actions.configure_output_streams()
    if ctx.invoked_subcommand is None:
        raise typer.Exit(code=repl.run_repl())


@app.command(help=_t("help.check"))
def check(
    file: Path = typer.Argument(..., help=_t("help.file")),
    lang: str | None = typer.Option(None, "--lang", help=_t("help.lang")),
) -> None:
    """Inspect an AASX package and report its detected version."""
    actions.configure_output_streams()
    language = actions.resolve_language(lang)
    raise typer.Exit(code=actions.execute_check(file, language, detect=detect_versions))


@app.command(help=_t("help.migrate"))
def migrate(
    file: Path = typer.Argument(..., help=_t("help.file")),
    lang: str | None = typer.Option(None, "--lang", help=_t("help.lang")),
    report: Path | None = typer.Option(None, "--report", help=_t("help.report")),
) -> None:
    """Migrate an AASX package through the evidence gate."""
    actions.configure_output_streams()
    language = actions.resolve_language(lang)
    raise typer.Exit(code=actions.execute_migrate(file, language, report, migrate=run_migration))


@app.command(name="shell", help=_t("help.shell"))
def shell() -> None:
    """Open the interactive shell."""
    actions.configure_output_streams()
    raise typer.Exit(code=repl.run_repl())


app.command(name="smia", help=_t("help.smia"))(smia_command)
app.command(name="update", help=_t("help.update"))(update_command)


if __name__ == "__main__":
    app()
