"""Typer command for ``aas-bridge smia`` (thin wrapper over ``cli.actions``)."""

from __future__ import annotations

from pathlib import Path

import typer

from aas_bridge.cli import actions, i18n

_HELP_LANG = i18n.default_language()


def smia(
    file: Path | None = typer.Argument(
        None,
        help=i18n.translate("help.file_optional", _HELP_LANG),
    ),
    lang: str | None = typer.Option(
        None,
        "--lang",
        help=i18n.translate("help.lang", _HELP_LANG),
    ),
) -> None:
    """Show which AAS versions your SMIA release can read."""
    actions.configure_output_streams()
    language = actions.resolve_language(lang)
    raise typer.Exit(code=actions.execute_smia(file, language))
