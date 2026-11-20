"""Unit tests for ``aas-bridge smia`` (offline, mocked probes and detection)."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aas_bridge.cli import actions, i18n
from aas_bridge.cli import main as cli
from aas_bridge.engine.detect import DetectionResult, PartDetection
from aas_bridge.exceptions import DetectionError
from aas_bridge.probes.pypi import SmiaPinFact

runner = CliRunner()


@pytest.fixture
def not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)


def _installed(monkeypatch: pytest.MonkeyPatch, version: str, pin: str | None) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda name: version)
    requirements = ["typer~=0.29"] + ([f"basyx-python-sdk{pin}"] if pin else [])
    monkeypatch.setattr(importlib.metadata, "requires", lambda name: requirements)


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


def _package(tmp_path: Path) -> Path:
    path = tmp_path / "package.aasx"
    path.write_bytes(b"placeholder")
    return path


def test_smia_reports_the_installed_distribution(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _installed(monkeypatch, "1.0.3", "~=1.2.1")

    code = actions.execute_smia(None, "en")

    assert code == 0
    text = capsys.readouterr().out
    assert "SMIA: 1.0.3" in text
    assert "installed in this environment" in text
    assert "basyx-python-sdk~=1.2.1" in text
    assert "Reads AAS: 3.0" in text
    assert "importlib.metadata" in text
    assert "What you can do" in text
    assert "not available yet (Phase 2)" in text


def test_smia_registry_branch_uses_the_static_table(
    not_installed: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(actions, "fetch_smia_pin", lambda version: pytest.fail("probe used"))

    code = actions.execute_smia(None, "en", prompt=lambda text, default="": "1.0.3")

    assert code == 0
    text = capsys.readouterr().out
    assert "SMIA: 1.0.3" in text
    assert "verified registry table" in text
    assert "Reads AAS: 3.0" in text


def test_smia_pypi_branch_uses_the_probe(
    not_installed: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    requested: list[str] = []

    def probe(version: str) -> SmiaPinFact:
        requested.append(version)
        return SmiaPinFact("0.1.0", "==1.1.0", "2024-12-01")

    monkeypatch.setattr(actions, "fetch_smia_pin", probe)

    code = actions.execute_smia(None, "en", prompt=lambda text, default="": "0.1.0")

    assert code == 0
    assert requested == ["0.1.0"]
    text = capsys.readouterr().out
    assert "PyPI release metadata" in text
    assert "2024-12-01" in text


def test_smia_unverified_is_visible_and_exit_zero(
    not_installed: None, capsys: pytest.CaptureFixture[str]
) -> None:
    code = actions.execute_smia(None, "en", prompt=lambda text, default: "")

    assert code == 0
    text = capsys.readouterr().out
    assert "Status: unverified" in text
    assert "basyx pin: unknown" in text
    assert "Reads AAS: unknown" in text
    assert "Cannot verify this SMIA version" in text


def test_smia_missing_file_is_exit_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _installed(monkeypatch, "1.0.3", "~=1.2.1")

    code = actions.execute_smia(tmp_path / "missing.aasx", "en")

    assert code == 1
    assert "File not found" in capsys.readouterr().err


def test_smia_detection_error_is_exit_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _installed(monkeypatch, "1.0.3", "~=1.2.1")

    def failing(path: Path) -> DetectionResult:
        raise DetectionError("not an AASX package")

    monkeypatch.setattr(actions, "detect_versions", failing)

    code = actions.execute_smia(_package(tmp_path), "en")

    assert code == 1
    assert "Cannot read the package" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("file_label", "readable", "expected"),
    [
        ("3.0", ["3.0"], "compatible — nothing to do"),
        ("3.0", ["3.1"], "run `aas-bridge migrate"),
        ("3.1", ["3.0"], "downgrade V3.1→V3.0 is not available yet (Phase 2)"),
        ("3.2", ["3.1"], "incompatible"),
    ],
)
def test_smia_verdict_branches(
    file_label: str,
    readable: list[str],
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from aas_bridge.registry.ecosystem.smia import SmiaResolution

    resolution = SmiaResolution(
        status="installed",
        smia_version="1.0.3",
        basyx_pin="~=1.2.1",
        readable_aas=readable,
        source_note="importlib.metadata (offline)",
    )
    monkeypatch.setattr(actions, "resolve_smia", lambda version, probe: resolution)
    monkeypatch.setattr(actions, "detect_versions", lambda path: _detection(file_label))

    code = actions.execute_smia(_package(tmp_path), "en")

    assert code == 0
    text = capsys.readouterr().out
    assert f"Detected: AAS {file_label}" in text
    assert expected in text


def test_smia_undetectable_file_is_exit_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _installed(monkeypatch, "1.0.3", "~=1.2.1")
    monkeypatch.setattr(actions, "detect_versions", lambda path: _detection(None))

    code = actions.execute_smia(_package(tmp_path), "en")

    assert code == 1
    text = capsys.readouterr()
    assert "undetectable" in text.out
    assert "aas-bridge check" in text.err


def test_verdict_is_unverified_when_the_smia_version_is_unknown(
    not_installed: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(actions, "detect_versions", lambda path: _detection("3.0"))

    code = actions.execute_smia(_package(tmp_path), "en", prompt=lambda text, default: "")

    assert code == 0
    assert "the SMIA version is unverified" in capsys.readouterr().out


def test_smia_command_prompts_and_accepts_a_version_via_the_runner(
    not_installed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(actions, "fetch_smia_pin", lambda version: pytest.fail("probe used"))

    result = runner.invoke(cli.app, ["smia", "--lang", "en"], input="1.0.3\n")

    assert result.exit_code == 0
    assert "SMIA: 1.0.3" in result.stdout


def test_smia_command_enter_skips_the_prompt(
    not_installed: None,
) -> None:
    result = runner.invoke(cli.app, ["smia", "--lang", "es"], input="\n")

    assert result.exit_code == 0
    assert "Estado: sin verificar" in result.stdout


def test_smia_spanish_rendering(monkeypatch: pytest.MonkeyPatch) -> None:
    _installed(monkeypatch, "1.0.3", "~=1.2.1")

    result = runner.invoke(cli.app, ["smia", "--lang", "es"])

    assert result.exit_code == 0
    assert "guía de SMIA" in result.stdout
    assert "instalada en este entorno" in result.stdout
    assert "Lee AAS: 3.0" in result.stdout
    assert "Conversión descendente AAS 3.1 → 3.0" in result.stdout


@pytest.mark.parametrize("lang", ["en", "es"])
def test_smia_invalid_language_uses_the_catalog(lang: str) -> None:
    expected = i18n.translate(
        "error.unsupported_language",
        i18n.default_language(),
        value="fr",
        supported=", ".join(i18n.SUPPORTED_LANGUAGES),
    )

    result = runner.invoke(cli.app, ["smia", "--lang", "fr"])

    assert result.exit_code == 2
    assert expected in (result.stdout + (result.stderr or ""))


def test_new_smia_keys_are_complete_in_both_locales() -> None:
    keys = [key for key in i18n.MESSAGES if key.startswith(("smia.", "help.smia"))]
    assert keys, "no smia keys found"
    for key in keys:
        assert set(i18n.MESSAGES[key]) == set(i18n.SUPPORTED_LANGUAGES), key
        assert all(i18n.MESSAGES[key][language].strip() for language in i18n.SUPPORTED_LANGUAGES)


def test_smia_help_is_registered() -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "smia" in result.stdout
