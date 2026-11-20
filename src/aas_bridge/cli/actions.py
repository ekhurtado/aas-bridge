"""Shared command implementations used by the Typer CLI and the REPL.

Each ``execute_*`` function prints through ``typer.echo`` and **returns** the exit
code instead of raising ``typer.Exit``; the REPL depends on that so a failing
command never terminates the session. The Typer commands are thin wrappers that
raise ``typer.Exit`` with the returned code.

Library code never prints (CONVENTIONS §3): printing stays in this CLI layer.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import typer

from aas_bridge import __version__
from aas_bridge.cli import i18n
from aas_bridge.engine.detect import DetectionResult, detect_versions
from aas_bridge.engine.gate import MigrationOutcome, run_migration
from aas_bridge.engine.report import Metrics, MigrationReport
from aas_bridge.exceptions import (
    AASBridgeError,
    DetectionError,
    EvidenceGateError,
    MigrationError,
    ProbeError,
)
from aas_bridge.probes.artifacts import (
    FetchedArtifact,
    OfficialRelease,
    fetch_artifacts,
    fetch_official_releases,
)
from aas_bridge.probes.pypi import SmiaPinFact, fetch_smia_pin
from aas_bridge.registry.data_dir import resolve_registry_dir
from aas_bridge.registry.ecosystem.smia import SmiaResolution, resolve_smia
from aas_bridge.registry.ecosystem.specs import (
    ARTIFACT_SOURCES,
    KNOWN_AAS_LABELS,
    OFFICIAL_SOURCE,
)
from aas_bridge.registry.versions import TARGET_VERSION_LABEL

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_INPUT = 1
EXIT_USAGE = 2
EXIT_GATE = 3
EXIT_INTERNAL = 4


def configure_output_streams() -> None:
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


def resolve_language(lang: str | None) -> str:
    """Return the requested language, or the system default; ``BadParameter`` otherwise.

    The invalid-value message comes from the i18n catalog in the default
    language, so the usage error is never English-only (ISS-011).
    """
    if lang is None:
        return i18n.default_language()
    normalized = lang.lower()
    if normalized not in i18n.SUPPORTED_LANGUAGES:
        raise typer.BadParameter(
            i18n.translate(
                "error.unsupported_language",
                i18n.default_language(),
                value=lang,
                supported=", ".join(i18n.SUPPORTED_LANGUAGES),
            )
        )
    return normalized


def echo_error(message: str) -> None:
    """Print an error line to stderr."""
    typer.echo(message, err=True)


def _fail(message: str, code: int) -> int:
    echo_error(message)
    return code


def _translate(language: str) -> Callable[..., str]:
    def translate(key: str, **params: object) -> str:
        return i18n.translate(key, language, **params)

    return translate


# --------------------------------------------------------------------------- smia


def execute_smia(
    file: Path | None,
    language: str,
    *,
    probe: Callable[[str], SmiaPinFact] | None = None,
    prompt: Callable[..., str] | None = None,
) -> int:
    """Produce the SMIA guidance and, when ``file`` is given, a per-file verdict."""
    translate = _translate(language)
    if file is not None and not Path(file).is_file():
        return _fail(translate("error.file_not_found", path=file), EXIT_INPUT)

    probe_fn = probe if probe is not None else fetch_smia_pin
    resolution = resolve_smia(None, None)
    if resolution.status == "unverified" and resolution.smia_version is None:
        prompt_fn = prompt if prompt is not None else typer.prompt
        entered = prompt_fn(translate("smia.prompt"), default="")
        if entered and entered.strip():
            resolution = resolve_smia(entered.strip(), probe_fn)

    _print_smia_resolution(resolution, language)
    if file is None:
        _print_smia_guide(language)
        return EXIT_OK

    package = Path(file)
    try:
        detection = detect_versions(package)
    except DetectionError as exc:
        return _fail(translate("error.detection", detail=exc), EXIT_INPUT)
    except AASBridgeError as exc:
        return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)
    except Exception as exc:  # last-resort boundary: log the traceback, report exit 4
        logger.exception("Unexpected error while inspecting %s for SMIA guidance", package)
        return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)

    typer.echo(translate("smia.file", file=package))
    if detection.version_label is None:
        typer.echo(translate("smia.detected_undetectable"))
        typer.echo(
            translate("smia.verdict_undetectable", file=package),
            err=True,
        )
        return EXIT_INPUT

    typer.echo(translate("smia.detected", version=detection.version_label))
    typer.echo(_smia_verdict(resolution, detection.version_label, package, language))
    return EXIT_OK


def _print_smia_resolution(resolution: SmiaResolution, language: str) -> None:
    translate = _translate(language)
    typer.echo(translate("smia.title"))
    if resolution.smia_version is None:
        typer.echo(translate("smia.version_unknown"))
    else:
        typer.echo(translate("smia.version", version=resolution.smia_version))
    typer.echo(
        translate(
            "smia.status",
            status=translate(f"smia.status_{resolution.status}"),
        )
    )
    if resolution.basyx_pin is None:
        typer.echo(translate("smia.basyx_pin_unknown"))
    else:
        typer.echo(translate("smia.basyx_pin", pin=f"basyx-python-sdk{resolution.basyx_pin}"))
    if resolution.readable_aas:
        typer.echo(translate("smia.reads", labels=", ".join(resolution.readable_aas)))
    else:
        typer.echo(translate("smia.reads_unknown"))
    typer.echo(translate("smia.source", note=resolution.source_note))
    if resolution.status == "unverified":
        typer.echo(translate("smia.unverified_hint"))


def _print_smia_guide(language: str) -> None:
    translate = _translate(language)
    typer.echo(translate("smia.guide_title"))
    typer.echo(translate("smia.guide_check"))
    typer.echo(translate("smia.guide_migrate"))
    typer.echo(translate("smia.guide_downgrade"))


def _smia_verdict(resolution: SmiaResolution, file_label: str, package: Path, language: str) -> str:
    translate = _translate(language)
    readable = resolution.readable_aas
    if not readable:
        return translate("smia.verdict_unverified")
    if file_label in readable:
        return translate("smia.verdict_compatible")
    if file_label == "3.0" and "3.1" in readable:
        return translate("smia.verdict_upgrade", labels=", ".join(readable), file=package)
    if file_label == "3.1" and "3.0" in readable:
        return translate("smia.verdict_downgrade", file=package)
    return translate(
        "smia.verdict_incompatible",
        labels=", ".join(readable),
        version=file_label,
    )


# ------------------------------------------------------------------ check/migrate


def execute_check(
    file: Path,
    language: str,
    *,
    detect: Callable[[Path], DetectionResult] | None = None,
) -> int:
    """Inspect an AASX package and print its diagnosis; returns the exit code."""
    translate = _translate(language)
    detect_fn = detect if detect is not None else detect_versions
    source = Path(file)
    if not source.is_file():
        return _fail(translate("error.file_not_found", path=file), EXIT_INPUT)
    try:
        detection = detect_fn(source)
    except DetectionError as exc:
        return _fail(translate("error.detection", detail=exc), EXIT_INPUT)
    except AASBridgeError as exc:
        return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)
    except Exception as exc:  # last-resort boundary: log the traceback, report exit 4
        logger.exception("Unexpected error while checking %s", source)
        return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)
    return print_detection(source, detection, language)


def execute_migrate(
    file: Path,
    language: str,
    report: Path | None = None,
    *,
    migrate: Callable[..., MigrationOutcome] | None = None,
) -> int:
    """Run the evidence-gated migration and print its summary; returns the exit code."""
    translate = _translate(language)
    migrate_fn = migrate if migrate is not None else run_migration
    source = Path(file)
    if not source.is_file():
        return _fail(translate("error.file_not_found", path=file), EXIT_INPUT)

    engine_report, report_problem = _prepare_report_path(report)
    try:
        try:
            outcome = migrate_fn(source, report_path=engine_report)
        except (DetectionError, MigrationError) as exc:
            return _fail(translate("error.migration", detail=exc), EXIT_INPUT)
        except EvidenceGateError as exc:
            typer.echo(translate("error.gate", detail=exc), err=True)
            _handle_refusal_report(exc, report, engine_report, report_problem, language)
            return EXIT_GATE
        except ProbeError as exc:
            return _fail(translate("error.gate", detail=exc), EXIT_GATE)
        except AASBridgeError as exc:
            return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)
        except Exception as exc:  # last-resort boundary: log the traceback, report exit 4
            logger.exception("Unexpected error while migrating %s", source)
            return _fail(translate("error.unexpected", detail=exc), EXIT_INTERNAL)

        if report is not None and engine_report != Path(report):
            # The requested path was unwritable at pre-flight; the engine wrote a
            # temporary report so the gate result survives (ISS-012). Try the user
            # copy now and report the failure without masking the migration.
            problem = _persist_report(outcome.report, Path(report))
            if problem is not None:
                print_migration(outcome, language, None)
                echo_error(translate("migrate.report_write_failed", path=report, reason=problem))
                return EXIT_INPUT
        print_migration(outcome, language, report)
        return EXIT_OK
    finally:
        if engine_report is not None and report is not None and engine_report != Path(report):
            Path(engine_report).unlink(missing_ok=True)


def _prepare_report_path(report: Path | None) -> tuple[Path | None, str | None]:
    """Return the path handed to the engine and the writability problem, if any.

    When the requested ``--report`` path is unwritable, the engine receives a
    temporary writable path: its refusal report is persisted *before* it raises
    the gate error, so an unwritable path would otherwise mask the gate error
    (ISS-012).
    """
    if report is None:
        return None, None
    destination = Path(report)
    problem = _report_write_problem(destination)
    if problem is None:
        return destination, None
    descriptor, raw_path = tempfile.mkstemp(prefix="aasbridge-report-", suffix=".json")
    os.close(descriptor)
    return Path(raw_path), problem


def _report_write_problem(report: Path) -> str | None:
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        probe = report.with_name(report.name + ".probe")
        probe.write_bytes(b"")
        probe.unlink()
    except OSError as exc:
        return str(exc)
    return None


def _handle_refusal_report(
    error: EvidenceGateError,
    report: Path | None,
    engine_report: Path | None,
    report_problem: str | None,
    language: str,
) -> None:
    translate = _translate(language)
    if report is None:
        return
    destination = Path(report)
    if report_problem is None and engine_report == destination and destination.is_file():
        echo_error(translate("migrate.report_written", path=destination))
        return
    refusal = getattr(error, "report", None)
    problem = _persist_report(refusal, destination)
    if problem is None:
        echo_error(translate("migrate.report_written", path=destination))
    else:
        echo_error(translate("migrate.report_write_failed", path=destination, reason=problem))


def _persist_report(report: MigrationReport | None, path: Path) -> str | None:
    if report is None:
        return "no report was produced"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(report.to_json(), encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        return str(exc)
    return None


# ------------------------------------------------------------------- update


MANIFEST_SCHEMA_VERSION = 1
COVERED_PAIRS = ["3.0->3.1"]


def execute_update(
    language: str,
    *,
    releases_probe: Callable[..., list[OfficialRelease]] | None = None,
    artifacts_probe: Callable[..., list[FetchedArtifact]] | None = None,
    registry_dir: Path | None = None,
    generated_at: datetime | None = None,
) -> int:
    """Check the official releases, fetch the pinned artifacts and write the manifest.

    Offline is a degraded state, not an error: the command prints it, still
    writes the manifest and returns ``0`` (L1-14). Fetching never creates or
    activates a migration rule (ADR-012); it only writes the data directory.
    """
    translate = _translate(language)
    releases_fn = releases_probe if releases_probe is not None else fetch_official_releases
    artifacts_fn = artifacts_probe if artifacts_probe is not None else fetch_artifacts
    directory = Path(registry_dir) if registry_dir is not None else resolve_registry_dir()
    generated = generated_at if generated_at is not None else datetime.now(UTC)

    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _fail(
            translate("update.directory_error", path=directory, detail=exc),
            EXIT_INTERNAL,
        )

    typer.echo(translate("update.title"))
    typer.echo(translate("update.source", repo=OFFICIAL_SOURCE.repo))
    releases: list[OfficialRelease] = []
    online = True
    try:
        releases = list(releases_fn())
    except ProbeError as exc:
        online = False
        typer.echo(translate("update.status_offline"))
        echo_error(translate("update.offline_note", detail=exc))
    else:
        typer.echo(translate("update.status_online"))

    covered = sorted(ARTIFACT_SOURCES)
    known_uncovered = sorted(KNOWN_AAS_LABELS - set(covered))
    new_labels = sorted(
        {
            release.aas_label
            for release in releases
            if release.aas_label is not None
            and not release.prerelease
            and release.aas_label not in KNOWN_AAS_LABELS
        }
    )
    prereleases = [release.tag for release in releases if release.prerelease]
    typer.echo(translate("update.covered", labels=", ".join(covered)))
    typer.echo(translate("update.covered_pairs", pairs=", ".join(COVERED_PAIRS)))
    typer.echo(
        translate(
            "update.known_uncovered",
            labels=", ".join(known_uncovered) if known_uncovered else "-",
        )
    )
    if new_labels:
        typer.echo(translate("update.new_labels", labels=", ".join(new_labels)))
    else:
        typer.echo(translate("update.no_new"))
    if prereleases:
        typer.echo(translate("update.prereleases", tags=", ".join(prereleases)))

    fetched: list[FetchedArtifact] = []
    for label in covered:
        if not online:
            fetched.extend(_offline_artifacts(label))
            continue
        try:
            fetched.extend(artifacts_fn(label, directory))
        except ProbeError as exc:
            echo_error(translate("update.label_failed", label=label, detail=exc))
            fetched.extend(_failed_artifacts(label))

    typer.echo(translate("update.artifacts_title"))
    for entry in fetched:
        status = translate(f"update.status_{entry.status}")
        if entry.status in ("fetched", "cached"):
            path = directory / entry.aas_label / Path(entry.url).name
            typer.echo(
                translate(
                    "update.artifact_line",
                    status=status,
                    label=entry.aas_label,
                    kind=entry.kind,
                    path=path,
                )
            )
        else:
            typer.echo(
                translate(
                    "update.artifact_status_line",
                    status=status,
                    label=entry.aas_label,
                    kind=entry.kind,
                )
            )

    manifest = _build_manifest(
        directory=directory,
        generated=generated,
        online=online,
        releases=releases,
        covered=covered,
        known_uncovered=known_uncovered,
        new_labels=new_labels,
        fetched=fetched,
    )
    manifest_path = directory / "manifest.json"
    try:
        _write_json_atomic(manifest_path, manifest)
    except OSError as exc:
        return _fail(
            translate("update.manifest_error", path=manifest_path, detail=exc),
            EXIT_INTERNAL,
        )

    typer.echo(translate("update.registry_dir", path=directory))
    typer.echo(translate("update.manifest", path=manifest_path))
    typer.echo(translate("update.no_rule_note"))
    return EXIT_OK


def _build_manifest(
    *,
    directory: Path,
    generated: datetime,
    online: bool,
    releases: list[OfficialRelease],
    covered: list[str],
    known_uncovered: list[str],
    new_labels: list[str],
    fetched: list[FetchedArtifact],
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "tool_version": __version__,
        "generated_at": generated.isoformat(),
        "registry_dir": str(directory),
        "check": {
            "online": online,
            "releases_seen": [
                {
                    "tag": release.tag,
                    "name": release.name,
                    "published": release.published,
                    "aas_label": release.aas_label,
                    "prerelease": release.prerelease,
                }
                for release in releases
            ],
            "covered_labels": covered,
            "covered_pairs": list(COVERED_PAIRS),
            "known_uncovered": known_uncovered,
            "new_labels": new_labels,
        },
        "artifacts": [
            {
                "kind": entry.kind,
                "aas_label": entry.aas_label,
                "tag": entry.tag,
                "url": entry.url,
                "sha256": entry.sha256,
                "size": entry.size,
                "fetched_at": entry.fetched_at,
                "status": entry.status,
                "licence": ARTIFACT_SOURCES[entry.aas_label].licence,
                "attribution": ARTIFACT_SOURCES[entry.aas_label].attribution,
            }
            for entry in fetched
        ],
    }


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _offline_artifacts(label: str) -> list[FetchedArtifact]:
    return _pending_artifacts(label, "skipped_offline")


def _failed_artifacts(label: str) -> list[FetchedArtifact]:
    return _pending_artifacts(label, "failed")


def _pending_artifacts(
    label: str, status: Literal["failed", "skipped_offline"]
) -> list[FetchedArtifact]:
    version = ARTIFACT_SOURCES[label]
    return [
        FetchedArtifact(
            kind=spec.kind,
            aas_label=label,
            tag=version.tag,
            url=f"{OFFICIAL_SOURCE.raw_base}/{version.tag}/{spec.path}",
            sha256=None,
            size=None,
            fetched_at=None,
            status=status,
        )
        for spec in version.artifacts
    ]


# ------------------------------------------------------------------- shared output


def print_detection(file: Path, detection: DetectionResult, language: str) -> int:
    """Print the ``check`` diagnosis; returns the exit code."""
    translate = _translate(language)
    typer.echo(translate("check.title"))
    typer.echo(translate("check.file", file=file))
    if detection.version_label is None:
        details = "; ".join(
            f"{part.part_name}={part.declared_version or translate('check.detected_undetectable')}"
            for part in detection.parts
        )
        echo_error(translate("check.inconsistent", details=details))
        return EXIT_INPUT

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
    return EXIT_OK


def print_migration(outcome: MigrationOutcome, language: str, report_path: Path | None) -> None:
    """Print the ``migrate`` summary derived from the migration report."""
    translate = _translate(language)
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
