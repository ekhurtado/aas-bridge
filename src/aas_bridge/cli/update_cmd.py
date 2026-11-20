"""Typer command for ``aas-bridge update`` (thin wrapper over ``cli.actions``)."""

from __future__ import annotations

import typer

from aas_bridge.cli import actions, i18n

_HELP_LANG = i18n.default_language()


def update(
    lang: str | None = typer.Option(
        None,
        "--lang",
        help=i18n.translate("help.lang", _HELP_LANG),
    ),
) -> None:
    """Check the official AAS releases and fetch the pinned schema artifacts."""
    actions.configure_output_streams()
    language = actions.resolve_language(lang)
    raise typer.Exit(code=actions.execute_update(language))
