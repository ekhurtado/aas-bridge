"""Unit tests for the evidence gate (pip and subprocesses mocked, offline)."""

from __future__ import annotations

import hashlib
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from aas_bridge.engine import gate
from aas_bridge.engine.report import MigrationReport
from aas_bridge.exceptions import EvidenceGateError, MigrationError, ProbeError

REPO_ROOT = Path(__file__).resolve().parents[2]
V30 = "aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx"
V31 = "aas_v3-1/SMIA_orchestrator.aasx"
FIXED_TIME = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)

BASELINE: dict[str, Any] = {
    "basyx_version": "2.0.1",
    "total": 22,
    "counts": {"aas": 1, "submodels": 6, "concept_descriptions": 15},
    "ids_sha256": "baseline-ids",
    "semantic_ids_sha256": "baseline-semantic-ids",
}
TARGET: dict[str, Any] = {
    **BASELINE,
    "basyx_version": "2.2.0",
}
PROBE: dict[str, Any] = {
    "basyx_version": "2.2.0",
    "ns_aas": "{https://admin-shell.io/aas/3/1}",
    "ns_aas_iri": "https://admin-shell.io/aas/3/1",
}


def _copy(relative: str, tmp_path: Path) -> Path:
    destination = tmp_path / Path(relative).name
    shutil.copy2(REPO_ROOT / relative, destination)
    return destination


def _loader(
    *,
    baseline: dict[str, Any] | None = None,
    target: dict[str, Any] | None = None,
    probe: dict[str, Any] | None = None,
    round_trip_ok: bool = True,
):
    baseline_payload = dict(baseline or BASELINE)
    target_payload = dict(target or TARGET)
    probe_payload = dict(probe or PROBE)

    def run(module: str, arguments: list[str], timeout: int) -> dict[str, Any]:
        if module == gate.DIALECT_PROBE_MODULE:
            return probe_payload
        if module == gate.BASELINE_LOADER_MODULE:
            return baseline_payload
        if module == gate.TARGET_LOADER_MODULE:
            return {
                **target_payload,
                "round_trip": {
                    "ok": round_trip_ok,
                    "differences": [] if round_trip_ok else ["total"],
                    "metrics": target_payload,
                },
            }
        raise AssertionError(f"unexpected loader module {module}")

    return run


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    cache_dir: Path,
    *,
    pip=None,
    loader=None,
) -> list[str]:
    calls: list[str] = []
    if pip is None:

        def pip(requirement: str) -> None:
            calls.append(requirement)

    monkeypatch.setenv("AASBRIDGE_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(gate, "_pip_install", pip)
    monkeypatch.setattr(gate, "_run_loader", loader or _loader())
    return calls


def test_no_migration_shortcut_does_not_probe_or_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V31, tmp_path)
    monkeypatch.setenv("AASBRIDGE_CACHE_DIR", str(tmp_path / "cache"))

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no swap or loader may run for an already-migrated file")

    monkeypatch.setattr(gate, "_pip_install", forbidden)
    monkeypatch.setattr(gate, "_run_loader", forbidden)

    outcome = gate.run_migration(source, generated_at=FIXED_TIME)

    assert outcome.status == "no_migration_needed"
    assert outcome.output_path is None
    assert outcome.report.baseline is None
    assert outcome.report.gate is None
    assert outcome.report.outcome.status == "no_migration_needed"
    assert outcome.report.generated_at == FIXED_TIME
    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()


def test_cache_miss_swaps_and_hit_skips_the_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)
    cache_dir = tmp_path / "cache"
    calls = _install_fakes(monkeypatch, cache_dir)

    first = gate.run_migration(source, report_path=tmp_path / "report.json")

    assert first.status == "emitted"
    assert calls == [gate.DIALECT_MAP["3.0"], gate.TARGET_REQUIREMENT]
    assert first.report.baseline is not None
    assert first.report.baseline.basyx_version == "2.0.1"
    assert first.report.gate is not None
    assert first.report.gate.result == "pass"
    assert first.report.gate.round_trip is True
    assert first.output_path is not None and first.output_path.is_file()
    assert list(cache_dir.glob("baseline-*.json"))
    report_file = tmp_path / "report.json"
    assert MigrationReport.from_json(report_file.read_text(encoding="utf-8")) == first.report

    calls.clear()
    second = gate.run_migration(source)

    assert second.status == "emitted"
    assert calls == []
    assert second.report.baseline is not None


def test_fresh_lock_blocks_a_second_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    lock = cache_dir / gate.LOCK_FILE_NAME
    lock.write_text("pid=other\n", encoding="utf-8")
    _install_fakes(monkeypatch, cache_dir)

    with pytest.raises(ProbeError, match="holds the gate lock"):
        gate.run_migration(source)

    lock.unlink()


def test_stale_lock_is_broken(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _copy(V30, tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    lock = cache_dir / gate.LOCK_FILE_NAME
    lock.write_text("pid=dead\n", encoding="utf-8")
    stale = time.time() - gate.LOCK_STALE_AFTER_SECONDS - 60
    os.utime(lock, (stale, stale))
    _install_fakes(monkeypatch, cache_dir)

    outcome = gate.run_migration(source)

    assert outcome.status == "emitted"
    assert not lock.exists()


def test_pip_failure_names_both_dialects_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)

    def pip_failure(requirement: str) -> None:
        raise ProbeError("network down")

    _install_fakes(monkeypatch, tmp_path / "cache", pip=pip_failure)

    with pytest.raises(ProbeError) as excinfo:
        gate.run_migration(source)

    message = str(excinfo.value)
    assert gate.DIALECT_MAP["3.0"] in message
    assert gate.TARGET_REQUIREMENT in message
    assert "Manual recovery" in message


def test_mismatched_target_metrics_are_not_emitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)
    report_path = tmp_path / "refused.report.json"
    target = {**TARGET, "total": 21}
    _install_fakes(monkeypatch, tmp_path / "cache", loader=_loader(target=target))

    with pytest.raises(EvidenceGateError) as excinfo:
        gate.run_migration(source, report_path=report_path)

    assert "total 22 -> 21" in str(excinfo.value)
    assert "not emitted" in str(excinfo.value)
    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()
    report = excinfo.value.report  # type: ignore[attr-defined]
    assert report.outcome.status == "refused"
    assert report.gate is not None and report.gate.result == "fail"
    assert report_path.is_file()
    persisted = MigrationReport.from_json(report_path.read_text(encoding="utf-8"))
    assert persisted.outcome.status == "refused"
    assert persisted.gate is not None and persisted.gate.result == "fail"


def test_refusal_report_is_not_written_without_a_report_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)
    target = {**TARGET, "total": 21}
    _install_fakes(monkeypatch, tmp_path / "cache", loader=_loader(target=target))

    with pytest.raises(EvidenceGateError):
        gate.run_migration(source)

    assert not list(tmp_path.glob("*.report.json"))


def test_unverified_dialect_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _copy(V30, tmp_path)
    probe = {
        "basyx_version": "2.0.1",
        "ns_aas": "{https://admin-shell.io/aas/3/0}",
        "ns_aas_iri": "https://admin-shell.io/aas/3/0",
    }
    _install_fakes(monkeypatch, tmp_path / "cache", loader=_loader(probe=probe))

    with pytest.raises(EvidenceGateError, match="unverified dialect"):
        gate.run_migration(source)

    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()


def test_failed_round_trip_is_not_emitted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _copy(V30, tmp_path)
    _install_fakes(monkeypatch, tmp_path / "cache", loader=_loader(round_trip_ok=False))

    with pytest.raises(EvidenceGateError, match="round-trip mismatch"):
        gate.run_migration(source)

    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()


def test_empty_baseline_is_a_gate_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _copy(V30, tmp_path)

    def loader(module: str, arguments: list[str], timeout: int) -> dict[str, Any]:
        if module == gate.BASELINE_LOADER_MODULE:
            raise gate._LoaderError("loaded 0 objects", 3)
        return _loader()(module, arguments, timeout)

    _install_fakes(monkeypatch, tmp_path / "cache", loader=loader)

    with pytest.raises(EvidenceGateError, match="loaded 0 objects"):
        gate.run_migration(source)


def test_empty_target_is_a_gate_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _copy(V30, tmp_path)

    def loader(module: str, arguments: list[str], timeout: int) -> dict[str, Any]:
        if module == gate.TARGET_LOADER_MODULE:
            raise gate._LoaderError("loaded 0 objects", 3)
        return _loader()(module, arguments, timeout)

    _install_fakes(monkeypatch, tmp_path / "cache", loader=loader)

    with pytest.raises(EvidenceGateError, match="loaded 0 objects"):
        gate.run_migration(source)

    assert not (tmp_path / f"{source.stem}-adapted.aasx").exists()


def test_input_is_never_mutated_by_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy(V30, tmp_path)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    _install_fakes(monkeypatch, tmp_path / "cache")

    outcome = gate.run_migration(source)

    assert outcome.status == "emitted"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_missing_input_is_a_migration_error(tmp_path: Path) -> None:
    with pytest.raises(MigrationError, match="not found"):
        gate.run_migration(tmp_path / "missing.aasx")
