"""Integration tests: the full evidence gate over the 6-file corpus.

These tests may install ``basyx-python-sdk==2.0.1`` and restore ``~=2.2`` in the
project venv (ADR-021) and may use the network on the first run. The corpus is
read-only: every file is copied to ``tmp_path`` first.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aas_bridge.cli.main import app
from aas_bridge.engine import gate
from aas_bridge.engine.detect import detect_versions
from aas_bridge.engine.report import MigrationReport

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]

V30_CASES = [
    ("aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx", 22, 6),
    ("aas_v3-0/SimulatedAssetHTTP_IndustrialRobot_1.aasx", 20, 4),
    ("aas_v3-0/SimulatedAssetsHTTP_Plan_1.aasx", 19, 3),
]

V31_CASES = [
    "aas_v3-1/HumanWorker1.aasx",
    "aas_v3-1/LEGO_machine0.aasx",
    "aas_v3-1/SMIA_orchestrator.aasx",
]


def _copy(relative: str, tmp_path: Path) -> Path:
    destination = tmp_path / Path(relative).name
    shutil.copy2(REPO_ROOT / relative, destination)
    return destination


@pytest.mark.parametrize(("relative", "expected_total", "expected_submodels"), V30_CASES)
def test_full_gate_emits_corpus_v30_migration(
    relative: str,
    expected_total: int,
    expected_submodels: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AASBRIDGE_CACHE_DIR", str(tmp_path / "cache"))
    source = _copy(relative, tmp_path)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    report_path = tmp_path / "migration.report.json"

    outcome = gate.run_migration(source, report_path=report_path)

    assert outcome.status == "emitted"
    assert outcome.output_path is not None and outcome.output_path.is_file()
    assert outcome.output_path.name == f"{source.stem}-adapted.aasx"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha

    report = outcome.report
    assert report.outcome.status == "emitted"
    assert report.baseline is not None
    assert report.baseline.basyx_version == "2.0.1"
    assert report.baseline.total == expected_total
    assert report.baseline.counts == {
        "aas": 1,
        "submodels": expected_submodels,
        "concept_descriptions": 15,
    }
    assert report.gate is not None
    assert report.gate.result == "pass"
    assert report.gate.round_trip is True
    assert report.gate.target is not None
    assert report.gate.target.total == expected_total
    assert report.gate.target.basyx_version.startswith("2.2")
    assert report.rules_applied == ["v3_0_to_v3_1/namespace-relabel"]

    assert report_path.is_file()
    assert MigrationReport.from_json(report_path.read_text(encoding="utf-8")) == report

    recheck = detect_versions(outcome.output_path)
    assert recheck.consistent is True
    assert recheck.version_label == "3.1"

    cli_check = CliRunner().invoke(app, ["check", str(outcome.output_path), "--lang", "en"])
    assert cli_check.exit_code == 0
    assert "Detected: AAS 3.1" in cli_check.stdout


@pytest.mark.parametrize("relative", V31_CASES)
def test_already_migrated_corpus_files_are_a_first_class_result(
    relative: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AASBRIDGE_CACHE_DIR", str(tmp_path / "cache"))
    source = _copy(relative, tmp_path)
    before = hashlib.sha256(source.read_bytes()).hexdigest()

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("an already-migrated file must not swap basyx or run a loader")

    monkeypatch.setattr(gate, "_pip_install", forbidden)
    monkeypatch.setattr(gate, "_run_loader", forbidden)

    outcome = gate.run_migration(source)

    assert outcome.status == "no_migration_needed"
    assert outcome.output_path is None
    assert outcome.report.baseline is None
    assert outcome.report.gate is None
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()


def test_venv_is_left_at_the_target_dialect_after_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gate run must restore the venv to ~=2.2 even after a baseline swap."""
    monkeypatch.setenv("AASBRIDGE_CACHE_DIR", str(tmp_path / "cache"))
    source = _copy(V30_CASES[0][0], tmp_path)

    gate.run_migration(source)

    version = importlib.metadata.version("basyx-python-sdk")
    assert version.startswith("2.2"), f"venv left at basyx {version}, expected ~=2.2"
