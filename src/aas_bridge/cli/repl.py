"""Standard-library interactive shell (REPL) over ``cli.actions``.

No third-party dependency: ``input()`` reads the line and ``shlex`` tokenizes it
with ``posix=False`` so Windows backslash paths survive; one level of matched
quotes is stripped to support paths with spaces. The REPL only dispatches: every
command implementation lives in :mod:`aas_bridge.cli.actions`. Command failures
print an error line and the loop continues; the process exits ``0`` on
``exit``/``quit``, EOF or Ctrl+C.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable
from pathlib import Path

import typer

from aas_bridge import __version__
from aas_bridge.cli import actions, i18n

PROMPT = "aas-bridge> "

_HELP_LINES = (
    "repl.help_check",
    "repl.help_migrate",
    "repl.help_smia",
    "repl.help_update",
    "repl.help_lang",
    "repl.help_version",
    "repl.help_help",
    "repl.help_exit",
)

_HELP_BY_COMMAND = {
    "check": "repl.help_check",
    "migrate": "repl.help_migrate",
    "smia": "repl.help_smia",
    "update": "repl.help_update",
    "lang": "repl.help_lang",
    "version": "repl.help_version",
    "help": "repl.help_help",
    "exit": "repl.help_exit",
    "quit": "repl.help_exit",
}


def tokenize(line: str) -> list[str]:
    """Split a REPL line preserving backslashes and stripping one quote level."""
    tokens = shlex.split(line, posix=False)
    return [_strip_one_quote(token) for token in tokens]


def run_repl(
    *,
    language: str | None = None,
    input_fn: Callable[[str], str] = input,
) -> int:
    """Run the interactive shell until ``exit``/``quit``, EOF or Ctrl+C."""
    session = language if language is not None else i18n.default_language()
    typer.echo(i18n.translate("repl.banner_title", session, version=__version__))
    typer.echo(i18n.translate("repl.banner_hint", session))
    while True:
        try:
            line = input_fn(PROMPT)
        except (EOFError, KeyboardInterrupt):
            typer.echo("")
            return actions.EXIT_OK
        stripped = line.strip()
        if not stripped:
            continue
        try:
            tokens = tokenize(stripped)
        except ValueError as exc:
            typer.echo(
                i18n.translate("repl.parse_error", session, detail=exc),
                err=True,
            )
            continue
        if not tokens:
            continue
        try:
            next_language = _dispatch(tokens, session)
        except KeyboardInterrupt:
            typer.echo("")
            return actions.EXIT_OK
        if next_language is None:  # sentinel for exit
            return actions.EXIT_OK
        session = next_language


def _dispatch(tokens: list[str], language: str) -> str | None:
    command = tokens[0].lower()
    arguments = tokens[1:]
    if command in ("exit", "quit"):
        return None
    if command == "help":
        _print_help(arguments, language)
        return language
    if command == "version":
        typer.echo(i18n.translate("version", language, version=__version__))
        return language
    if command == "lang":
        return _change_language(arguments, language)
    if command == "check":
        package = _single_file(arguments, "check", language)
        if package is not None:
            actions.execute_check(package, language)
        return language
    if command == "migrate":
        parsed = _migrate_arguments(arguments, language)
        if parsed is not None:
            package, report = parsed
            actions.execute_migrate(package, language, report)
        return language
    if command == "smia":
        package = _optional_file(arguments, language)
        if package is not None or not arguments:
            actions.execute_smia(package, language)
        return language
    if command == "update":
        if arguments:
            _usage("repl.usage_update", language)
        else:
            actions.execute_update(language)
        return language
    typer.echo(
        i18n.translate("repl.unknown_command", language, command=tokens[0]),
        err=True,
    )
    return language


def _print_help(arguments: list[str], language: str) -> None:
    if not arguments:
        typer.echo(i18n.translate("repl.help_title", language))
        for help_key in _HELP_LINES:
            typer.echo(i18n.translate(help_key, language))
        return
    command_key = _HELP_BY_COMMAND.get(arguments[0].lower())
    if command_key is None:
        typer.echo(
            i18n.translate("repl.unknown_command", language, command=arguments[0]),
            err=True,
        )
        return
    typer.echo(i18n.translate(command_key, language))


def _change_language(arguments: list[str], language: str) -> str:
    if not arguments:
        typer.echo(i18n.translate("repl.language_current", language, language=language))
        return language
    value = arguments[0].lower()
    if value not in i18n.SUPPORTED_LANGUAGES:
        typer.echo(
            i18n.translate("repl.language_invalid", language, value=arguments[0]),
            err=True,
        )
        return language
    typer.echo(i18n.translate("repl.language_set", language, language=value))
    return value


def _single_file(arguments: list[str], command: str, language: str) -> Path | None:
    if len(arguments) != 1:
        _usage(f"repl.usage_{command}", language)
        return None
    return Path(arguments[0])


def _optional_file(arguments: list[str], language: str) -> Path | None:
    if not arguments:
        return None
    if len(arguments) != 1:
        _usage("repl.usage_smia", language)
        return None
    return Path(arguments[0])


def _migrate_arguments(arguments: list[str], language: str) -> tuple[Path, Path | None] | None:
    if not arguments:
        _usage("repl.usage_migrate", language)
        return None
    package = Path(arguments[0])
    rest = arguments[1:]
    if not rest:
        return package, None
    if len(rest) == 2 and rest[0] == "--report":
        return package, Path(rest[1])
    _usage("repl.usage_migrate", language)
    return None


def _usage(key: str, language: str) -> None:
    typer.echo(
        i18n.translate(
            "repl.usage",
            language,
            usage=i18n.translate(key, language),
        ),
        err=True,
    )


def _strip_one_quote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
        return token[1:-1]
    return token
