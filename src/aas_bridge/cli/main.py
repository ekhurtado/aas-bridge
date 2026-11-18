"""Typer CLI: ``aas-bridge check`` and ``aas-bridge migrate``.

The CLI is a thin frontend over the headless core: it maps exceptions to the
public exit-code table and renders the migration report. Every runtime string
comes from :mod:`aas_bridge.cli.i18n` in English or Spanish.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import NoReturn

import typer

from aas_bridge import __version__
from aas_bridge.cli import i18n
from aas_bridge.engine.detect import DetectionResult, detect_versions
from aas_bridge.engine.gate import MigrationOutcome, run_migration
from aas_bridge.engine.report import Metrics
from aas_bridge.exceptions import (
    AASBridgeError,
    DetectionError,
    EvidenceGateError,
    MigrationError,
    ProbeError,
)
from aas_bridge.registry.versions import TARGET_VERSION_LABEL

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_INPUT = 1
EXIT_USAGE = 2
EXIT_GATE = 3
EXIT_INTERNAL = 4

_HELP_LANG = i18n.default_language()


def _t(key: str, **parameters: object) -> str:
    return i18n.translate(key, _HELP_LANG, **parameters)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(i18n.translate("version", _HELP_LANG, version=__version__))
        raise typer.Exit(code=EXIT_OK)


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help=_t("app.help"),
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help=_t("help.version"),
    ),
) -> None:
    """AAS Bridge command-line interface."""
    _configure_output_streams()


@app.command(help=_t("help.check"))
def check(
    file: Path = typer.Argument(..., help=_t("help.file")),
    lang: str | None = typer.Option(None, "--lang", help=_t("help.lang")),
) -> None:
    """Inspect an AASX package and report its detected version."""
    _configure_output_streams()
    language = _resolve_language(lang)
    if not file.is_file():
        _fail(i18n.translate("error.file_not_found", language, path=file), EXIT_INPUT)
    try:
        detection = detect_versions(file)
    except DetectionError as exc:
        _fail(i18n.translate("error.detection", language, detail=exc), EXIT_INPUT)
    except AASBridgeError as exc:
        _fail(i18n.translate("error.unexpected", language, detail=exc), EXIT_INTERNAL)
    except Exception as exc:  # last-resort boundary: log the traceback, report exit 4
        logger.exception("Unexpected error while checking %s", file)
        _fail(i18n.translate("error.unexpected", language, detail=exc), EXIT_INTERNAL)
    _print_detection(file, detection, language)
    raise typer.Exit(code=EXIT_OK)


@app.command(help=_t("help.migrate"))
def migrate(
    file: Path = typer.Argument(..., help=_t("help.file")),
    lang: str | None = typer.Option(None, "--lang", help=_t("help.lang")),
    report: Path | None = typer.Option(None, "--report", help=_t("help.report")),
) -> None:
    """Migrate an AASX package through the evidence gate."""
    _configure_output_streams()
    language = _resolve_language(lang)
    if not file.is_file():
        _fail(i18n.translate("error.file_not_found", language, path=file), EXIT_INPUT)
    try:
        outcome = run_migration(file, report_path=report)
    except (DetectionError, MigrationError) as exc:
        _fail(i18n.translate("error.migration", language, detail=exc), EXIT_INPUT)
    except EvidenceGateError as exc:
        typer.echo(i18n.translate("error.gate", language, detail=exc), err=True)
        if report is not None and report.is_file():
            typer.echo(
                i18n.translate("migrate.report_written", language, path=report),
                err=True,
            )
        raise typer.Exit(code=EXIT_GATE) from None
    except ProbeError as exc:
        _fail(i18n.translate("error.gate", language, detail=exc), EXIT_GATE)
    except AASBridgeError as exc:
        _fail(i18n.translate("error.unexpected", language, detail=exc), EXIT_INTERNAL)
    except Exception as exc:  # last-resort boundary: log the traceback, report exit 4
        logger.exception("Unexpected error while migrating %s", file)
        _fail(i18n.translate("error.unexpected", language, detail=exc), EXIT_INTERNAL)
    _print_migration(outcome, language, report)
    raise typer.Exit(code=EXIT_OK)


def _configure_output_streams() -> None:
    """Force UTF-8 output so redirected Windows consoles do not crash.

    The catalog contains typography such as the em dash and the arrow, which a
    legacy cp1252 console cannot encode. Reconfiguring the standard streams makes
    ``aas-bridge check > file.txt`` and scripted evidence capture work on Windows.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError) as exc:
            logger.debug("Could not reconfigure an output stream to UTF-8: %s", exc)


def _resolve_language(lang: str | None) -> str:
    if lang is None:
        return i18n.default_language()
    normalized = lang.lower()
    if normalized not in i18n.SUPPORTED_LANGUAGES:
        raise typer.BadParameter(
            f"Unsupported language {lang!r}; choose one of: {', '.join(i18n.SUPPORTED_LANGUAGES)}"
        )
    return normalized


def _fail(message: str, code: int) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=code)


def _print_detection(file: Path, detection: DetectionResult, language: str) -> None:
    def translate(key: str, **params: object) -> str:
        return i18n.translate(key, language, **params)

    typer.echo(translate("check.title"))
    typer.echo(translate("check.file", file=file))
    if detection.version_label is None:
        details = "; ".join(
            f"{part.part_name}={part.declared_version or translate('check.detected_undetectable')}"
            for part in detection.parts
        )
        typer.echo(translate("check.inconsistent", details=details), err=True)
        raise typer.Exit(code=EXIT_INPUT)

    typer.echo(translate("check.detected", version=detection.version_label))
    typer.echo(translate("check.parts", count=len(detection.parts)))
    for part in detection.parts:
        typer.echo(
            translate(
                "check.part_line",
                part=part.part_name,
                format=part.format,
                version=part.declared_version or translate("check.detected_undetectable"),
            )
        )
    typer.echo(translate("check.target", version=TARGET_VERSION_LABEL))
    has_json = any(part.format == "json" for part in detection.parts)
    if detection.version_label == TARGET_VERSION_LABEL:
        typer.echo(translate("check.already_target", version=TARGET_VERSION_LABEL))
    elif not has_json:
        typer.echo(translate("check.upgrade_available"))
    if has_json:
        typer.echo(translate("check.json_detect_only"))


def _print_migration(outcome: MigrationOutcome, language: str, report_path: Path | None) -> None:
    def translate(key: str, **params: object) -> str:
        return i18n.translate(key, language, **params)

    report = outcome.report
    typer.echo(translate("migrate.title"))
    if report.outcome.status == "no_migration_needed":
        typer.echo(translate("migrate.status_no_migration", version=TARGET_VERSION_LABEL))
        typer.echo(translate("migrate.source", file=report.source.file))
        typer.echo(translate("migrate.no_output"))
    else:
        typer.echo(translate("migrate.status_emitted"))
        typer.echo(translate("migrate.source", file=report.source.file))
        if report.baseline is not None:
            typer.echo(_metrics_line("migrate.baseline", report.baseline, language))
        if report.gate is not None and report.gate.target is not None:
            typer.echo(_metrics_line("migrate.target", report.gate.target, language))
        typer.echo(translate("migrate.rules", rules=", ".join(report.rules_applied) or "-"))
        if report.gate is not None:
            result = translate(
                "migrate.gate_pass" if report.gate.result == "pass" else "migrate.gate_fail"
            )
            round_trip = translate(
                "migrate.round_trip_ok" if report.gate.round_trip else "migrate.round_trip_failed"
            )
            typer.echo(translate("migrate.gate", result=result, round_trip=round_trip))
        if report.outcome.output_file is not None:
            typer.echo(translate("migrate.output", path=report.outcome.output_file))
    if report_path is not None:
        typer.echo(translate("migrate.report_written", path=report_path))


def _metrics_line(key: str, metrics: Metrics, language: str) -> str:
    return i18n.translate(
        key,
        language,
        total=metrics.total,
        aas=metrics.counts.get("aas", 0),
        submodels=metrics.counts.get("submodels", 0),
        cd=metrics.counts.get("concept_descriptions", 0),
        version=metrics.basyx_version,
    )


if __name__ == "__main__":
    app()
