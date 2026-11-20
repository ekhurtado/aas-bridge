"""Unit tests for the Typer CLI (engine mocked, no basyx swap)."""

from __future__ import annotations

import io
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from aas_bridge.cli import i18n
from aas_bridge.cli import main as cli
from aas_bridge.engine.detect import DetectionResult, PartDetection
from aas_bridge.engine.gate import MigrationOutcome
from aas_bridge.engine.report import (
    GateInfo,
    Metrics,
    MigrationReport,
    OutcomeInfo,
    SourceInfo,
    TargetInfo,
)
from aas_bridge.exceptions import DetectionError, EvidenceGateError, MigrationError, ProbeError

runner = CliRunner()
FIXED_TIME = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)
COUNTS = {"aas": 1, "submodels": 6, "concept_descriptions": 15}


def _package(tmp_path: Path) -> Path:
    path = tmp_path / "package.aasx"
    path.write_bytes(b"placeholder")
    return path


def _detection(label: str | None) -> DetectionResult:
    declared = None if label is None else f"https://admin-shell.io/aas/3/{label[-1]}"
    return DetectionResult(
        file="package.aasx",
        parts=[
            PartDetection(
                part_name="/aasx/data.xml",
                format="xml",
                declared_version=declared,
                version_label=label,
            )
        ],
        consistent=label is not None,
        version_label=label,
    )


def _report(
    status: str = "emitted", output_file: str | None = "package-adapted.aasx"
) -> MigrationReport:
    baseline = Metrics("2.0.1", 22, dict(COUNTS), "ids", "semantic-ids")
    target = Metrics("2.2.0", 22, dict(COUNTS), "ids", "semantic-ids")
    return MigrationReport(
        tool_version="0.1.0",
        generated_at=FIXED_TIME,
        source=SourceInfo(file="package.aasx", sha256="0" * 64),
        detected=_detection("3.0"),
        target=TargetInfo(
            version_label="3.1",
            namespace="https://admin-shell.io/aas/3/1",
            basyx_version="2.2.0" if status == "emitted" else None,
        ),
        rules_applied=["v3_0_to_v3_1/namespace-relabel"] if status == "emitted" else [],
        baseline=baseline if status == "emitted" else None,
        gate=GateInfo("pass", target, True) if status == "emitted" else None,
        outcome=OutcomeInfo(status=status, output_file=output_file),
    )


def _invoke(args: list[str]) -> Any:
    return runner.invoke(cli.app, args)


def _text(result: Any) -> str:
    return result.stdout + result.stderr


def test_catalog_is_complete_in_both_locales() -> None:
    for key, locales in i18n.MESSAGES.items():
        assert set(locales) == set(i18n.SUPPORTED_LANGUAGES), key
        assert all(locales[language].strip() for language in i18n.SUPPORTED_LANGUAGES), key


def test_version_flag() -> None:
    result = _invoke(["--version"])

    assert result.exit_code == 0
    assert "aas-bridge 0.2.0" in _text(result)


def test_check_reports_upgrade_in_english(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "detect_versions", lambda path: _detection("3.0"))

    result = _invoke(["check", str(_package(tmp_path)), "--lang", "en"])

    assert result.exit_code == 0
    text = _text(result)
    assert "Detected: AAS 3.0" in text
    assert "Target: AAS 3.1" in text
    assert "Upgrade available: yes" in text


def test_check_reports_upgrade_in_spanish(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "detect_versions", lambda path: _detection("3.0"))

    result = _invoke(["check", str(_package(tmp_path)), "--lang", "es"])

    assert result.exit_code == 0
    text = _text(result)
    assert "Detectado: AAS 3.0" in text
    assert "Actualización disponible: sí" in text


def test_check_already_migrated_is_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "detect_versions", lambda path: _detection("3.1"))

    result = _invoke(["check", str(_package(tmp_path)), "--lang", "es"])

    assert result.exit_code == 0
    assert "Ya es AAS 3.1 — no se necesita migración" in _text(result)


def test_check_undetectable_is_exit_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "detect_versions", lambda path: _detection(None))

    result = _invoke(["check", str(_package(tmp_path)), "--lang", "en"])

    assert result.exit_code == 1
    assert "No migration can be planned" in _text(result)


def test_check_missing_file_is_exit_1(tmp_path: Path) -> None:
    result = _invoke(["check", str(tmp_path / "missing.aasx"), "--lang", "en"])

    assert result.exit_code == 1
    assert "File not found" in _text(result)


def test_check_detection_error_is_exit_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_detection(path: Path) -> DetectionResult:
        raise DetectionError("not an AASX package")

    monkeypatch.setattr(cli, "detect_versions", raise_detection)

    result = _invoke(["check", str(_package(tmp_path)), "--lang", "en"])

    assert result.exit_code == 1
    assert "Cannot read the package" in _text(result)


def test_migrate_prints_summary_and_forwards_report_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_migration(
        source: Path, report_path: Path | None = None, generated_at: Any = None
    ) -> MigrationOutcome:
        captured["source"] = source
        captured["report_path"] = report_path
        return MigrationOutcome(
            status="emitted", report=_report(), output_path=tmp_path / "package-adapted.aasx"
        )

    monkeypatch.setattr(cli, "run_migration", fake_migration)
    report_path = tmp_path / "report.json"

    result = _invoke(
        ["migrate", str(_package(tmp_path)), "--lang", "en", "--report", str(report_path)]
    )

    assert result.exit_code == 0
    text = _text(result)
    assert "Status: migrated" in text
    assert "Baseline: 22 objects (1 AAS / 6 SM / 15 CD) with basyx 2.0.1" in text
    assert "Gate: PASS (round-trip OK)" in text
    assert "Output: " in text
    assert "Report: " in text
    assert captured["report_path"] == report_path


def test_migrate_no_migration_is_exit_0_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_migration(source: Path, report_path: Path | None = None, **kwargs: Any):
        return MigrationOutcome(
            status="no_migration_needed",
            report=_report(status="no_migration_needed", output_file=None),
            output_path=None,
        )

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(["migrate", str(_package(tmp_path)), "--lang", "es"])

    assert result.exit_code == 0
    text = _text(result)
    assert "ya es AAS 3.1 — no se necesita migración" in text
    assert "No se ha escrito ningún fichero de salida" in text


@pytest.mark.parametrize(
    ("lang", "expected"),
    [("en", "Migration refused"), ("es", "Migración rechazada")],
)
def test_migrate_json_parts_are_exit_1_in_both_locales(
    lang: str, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_migration(source: Path, report_path: Path | None = None, **kwargs: Any):
        raise MigrationError("AAS part is JSON; detect-only scope (TD-001).")

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(["migrate", str(_package(tmp_path)), "--lang", lang])

    assert result.exit_code == 1
    text = _text(result)
    assert expected in text
    assert "TD-001" in text


@pytest.mark.parametrize("error", [EvidenceGateError("mismatch"), ProbeError("pip failed")])
def test_migrate_gate_failures_are_exit_3(
    error: Exception, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_migration(source: Path, report_path: Path | None = None, **kwargs: Any):
        raise error

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(["migrate", str(_package(tmp_path)), "--lang", "en"])

    assert result.exit_code == 3
    assert "Evidence gate failed" in _text(result)


def test_migrate_refused_with_report_prints_the_persisted_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_file = tmp_path / "refused.report.json"

    def fake_migration(source: Path, report_path: Path | None = None, **kwargs: Any):
        assert report_path == report_file
        report_file.write_text('{"schema_version": 1}', encoding="utf-8")
        raise EvidenceGateError("mismatch")

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(
        [
            "migrate",
            str(_package(tmp_path)),
            "--lang",
            "en",
            "--report",
            str(report_file),
        ]
    )

    assert result.exit_code == 3
    text = _text(result)
    assert "Evidence gate failed" in text
    assert f"Report: {report_file}" in text


def test_migrate_missing_file_is_exit_1(tmp_path: Path) -> None:
    result = _invoke(["migrate", str(tmp_path / "missing.aasx"), "--lang", "en"])

    assert result.exit_code == 1


def test_usage_error_is_exit_2(tmp_path: Path) -> None:
    result = _invoke(["migrate"])

    assert result.exit_code == 2


def test_invalid_language_is_exit_2(tmp_path: Path) -> None:
    result = _invoke(["check", str(_package(tmp_path)), "--lang", "fr"])

    assert result.exit_code == 2


def test_check_output_survives_a_cp1252_stream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redirected Windows consoles must not crash on the em dash/arrow glyphs."""
    monkeypatch.setattr(cli, "detect_versions", lambda path: _detection("3.0"))
    stdout_buffer = io.BytesIO()
    stderr_buffer = io.BytesIO()
    stdout = io.TextIOWrapper(stdout_buffer, encoding="cp1252", errors="strict")
    stderr = io.TextIOWrapper(stderr_buffer, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    with pytest.raises(typer.Exit) as excinfo:
        cli.check(_package(tmp_path), "en")

    assert excinfo.value.exit_code == 0
    stdout.flush()
    text = stdout_buffer.getvalue().decode("utf-8")
    assert "Upgrade available: yes" in text
    assert "AAS 3.0" in text


# --------------------------------------------------------- SPEC-003 new commands


def test_smia_command_unverified_is_exit_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from aas_bridge.cli import actions
    from aas_bridge.registry.ecosystem.smia import SmiaResolution

    monkeypatch.setattr(
        actions,
        "resolve_smia",
        lambda version, probe: SmiaResolution(
            "unverified", "1.0.3", None, [], "no installed SMIA metadata"
        ),
    )

    result = _invoke(["smia", "--lang", "en"])

    assert result.exit_code == 0
    text = _text(result)
    assert "Status: unverified" in text
    assert "basyx pin: unknown" in text


def test_smia_command_missing_file_is_exit_1(tmp_path: Path) -> None:
    result = _invoke(["smia", str(tmp_path / "missing.aasx"), "--lang", "en"])

    assert result.exit_code == 1
    assert "File not found" in _text(result)


def test_smia_invalid_language_is_exit_2_from_the_catalog(tmp_path: Path) -> None:
    expected = i18n.translate(
        "error.unsupported_language",
        i18n.default_language(),
        value="fr",
        supported=", ".join(i18n.SUPPORTED_LANGUAGES),
    )

    result = _invoke(["smia", "--lang", "fr"])

    assert result.exit_code == 2
    assert expected in _text(result)


def test_update_command_offline_is_exit_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from aas_bridge.cli import actions

    def offline() -> object:
        raise ProbeError("Cannot reach GitHub (timed out)")

    registry = tmp_path / "registry"
    monkeypatch.setattr(actions, "fetch_official_releases", offline)
    monkeypatch.setattr(actions, "resolve_registry_dir", lambda: registry)

    result = _invoke(["update", "--lang", "en"])

    assert result.exit_code == 0
    text = _text(result)
    assert "offline — degraded" in text
    assert "skipped (offline)" in text
    assert (registry / "manifest.json").is_file()


def test_update_command_unwritable_registry_is_exit_4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from aas_bridge.cli import actions

    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(actions, "resolve_registry_dir", lambda: blocker / "registry")

    result = _invoke(["update", "--lang", "en"])

    assert result.exit_code == 4
    assert "Cannot create the registry directory" in _text(result)


def test_iss011_usage_message_lives_in_both_locales() -> None:
    for language in i18n.SUPPORTED_LANGUAGES:
        assert i18n.MESSAGES["error.unsupported_language"][language].strip()

    expected = i18n.translate(
        "error.unsupported_language",
        i18n.default_language(),
        value="xx",
        supported=", ".join(i18n.SUPPORTED_LANGUAGES),
    )
    result = _invoke(["check", "file.aasx", "--lang", "xx"])

    assert result.exit_code == 2
    assert expected in _text(result)


def test_iss012_unwritable_report_keeps_exit_3_and_notes_the_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    unwritable = blocker / "report.json"
    seen: dict[str, Any] = {}

    def fake_migration(
        source: Path, report_path: Path | None = None, **kwargs: Any
    ) -> MigrationOutcome:
        seen["report_path"] = report_path
        error = EvidenceGateError("target load differs from the baseline")
        error.report = _report()  # type: ignore[attr-defined]
        raise error

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(
        [
            "migrate",
            str(_package(tmp_path)),
            "--lang",
            "en",
            "--report",
            str(unwritable),
        ]
    )

    assert result.exit_code == 3
    text = _text(result)
    assert "Evidence gate failed" in text
    assert "The report could not be written to" in text
    assert "Migration refused" not in text
    assert seen["report_path"] != unwritable


def test_iss012_unwritable_report_on_success_is_exit_1_with_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    unwritable = blocker / "report.json"

    def fake_migration(
        source: Path, report_path: Path | None = None, **kwargs: Any
    ) -> MigrationOutcome:
        return MigrationOutcome(
            status="emitted", report=_report(), output_path=tmp_path / "package-adapted.aasx"
        )

    monkeypatch.setattr(cli, "run_migration", fake_migration)

    result = _invoke(
        [
            "migrate",
            str(_package(tmp_path)),
            "--lang",
            "en",
            "--report",
            str(unwritable),
        ]
    )

    assert result.exit_code == 1
    text = _text(result)
    assert "Status: migrated" in text
    assert "The report could not be written to" in text
