"""Tests for the stable migration report and its golden fixture."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aas_bridge.engine.detect import DetectionResult, PartDetection
from aas_bridge.engine.report import (
    REPORT_KEYS,
    SCHEMA_VERSION,
    GateInfo,
    Metrics,
    MigrationReport,
    OutcomeInfo,
    SourceInfo,
    TargetInfo,
)
from aas_bridge.exceptions import MigrationError

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "golden" / "report_v3_0_to_v3_1.json"
FIXED_TIME = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)
CORPUS_FILE = "aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx"
CORPUS_SHA256 = "6045f61cc67eb2a26f3e536301eaa5409845c9162606f624d24915105a6e5f4b"
BASELINE_IDS_SHA256 = "e8d964b3df1b1294186f173aafda82e89d416305115f363f84244af8d4a3919b"
BASELINE_SEMANTIC_IDS_SHA256 = "3ab2ff66eb62bce540fcf2d872db8ba452859f6e0f2d3ce834c8954ededb4ffa"
AAS_PART = "/aasx/IndustrialRobot_ABB_CeDRI/IndustrialRobot_ABB_CeDRI.aas.xml"
COUNTS = {"aas": 1, "submodels": 6, "concept_descriptions": 15}


def build_golden_report() -> MigrationReport:
    """Build the canned report that the golden fixture captures."""
    baseline = Metrics(
        basyx_version="2.0.1",
        total=22,
        counts=dict(COUNTS),
        ids_sha256=BASELINE_IDS_SHA256,
        semantic_ids_sha256=BASELINE_SEMANTIC_IDS_SHA256,
    )
    target_metrics = Metrics(
        basyx_version="2.2.0",
        total=22,
        counts=dict(COUNTS),
        ids_sha256=BASELINE_IDS_SHA256,
        semantic_ids_sha256=BASELINE_SEMANTIC_IDS_SHA256,
    )
    return MigrationReport(
        tool_version="0.1.0",
        generated_at=FIXED_TIME,
        source=SourceInfo(file=CORPUS_FILE, sha256=CORPUS_SHA256),
        detected=DetectionResult(
            file=CORPUS_FILE,
            parts=[
                PartDetection(
                    part_name=AAS_PART,
                    format="xml",
                    declared_version="https://admin-shell.io/aas/3/0",
                    version_label="3.0",
                )
            ],
            consistent=True,
            version_label="3.0",
        ),
        target=TargetInfo(
            version_label="3.1",
            namespace="https://admin-shell.io/aas/3/1",
            basyx_version="2.2.0",
        ),
        rules_applied=["v3_0_to_v3_1/namespace-relabel"],
        baseline=baseline,
        gate=GateInfo(result="pass", target=target_metrics, round_trip=True),
        outcome=OutcomeInfo(
            status="emitted",
            output_file="CeDRI_PunchingMachine_instanceA-adapted.aasx",
        ),
    )


def test_golden_report_matches_fixture() -> None:
    assert build_golden_report().to_json() == GOLDEN_PATH.read_text(encoding="utf-8")


def test_golden_source_hash_matches_corpus() -> None:
    payload = (REPO_ROOT / CORPUS_FILE).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == CORPUS_SHA256


def test_json_round_trip() -> None:
    report = build_golden_report()

    restored = MigrationReport.from_json(report.to_json())

    assert restored == report


def test_serialization_is_deterministic() -> None:
    report = build_golden_report()

    assert report.to_json() == report.to_json()
    assert report.to_dict() == report.to_dict()


def test_key_order_and_schema_version() -> None:
    data = json.loads(build_golden_report().to_json())

    assert tuple(data) == REPORT_KEYS
    assert data["schema_version"] == SCHEMA_VERSION


def test_no_nan_or_infinity() -> None:
    payload = build_golden_report().to_json()

    assert "NaN" not in payload
    assert "Infinity" not in payload


def test_refused_report_serializes_with_the_same_schema() -> None:
    emitted = build_golden_report()
    assert emitted.gate is not None
    refused = replace(
        emitted,
        gate=replace(emitted.gate, result="fail", message="counts differ"),
        outcome=OutcomeInfo(status="refused", output_file=None),
    )

    data = json.loads(refused.to_json())

    assert tuple(data) == REPORT_KEYS
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["outcome"] == {"status": "refused", "output_file": None}
    assert data["gate"]["result"] == "fail"
    assert data["gate"]["target"] is not None
    assert MigrationReport.from_json(refused.to_json()) == refused


def test_no_migration_report_serializes_null_sections() -> None:
    report = MigrationReport(
        tool_version="0.1.0",
        generated_at=FIXED_TIME,
        source=SourceInfo(file="aas_v3-1/SMIA_orchestrator.aasx", sha256="0" * 64),
        detected=DetectionResult(
            file="aas_v3-1/SMIA_orchestrator.aasx",
            parts=[
                PartDetection(
                    part_name="/aasx/data.xml",
                    format="xml",
                    declared_version="https://admin-shell.io/aas/3/1",
                    version_label="3.1",
                )
            ],
            consistent=True,
            version_label="3.1",
        ),
        target=TargetInfo(
            version_label="3.1",
            namespace="https://admin-shell.io/aas/3/1",
            basyx_version=None,
        ),
        rules_applied=[],
        baseline=None,
        gate=None,
        outcome=OutcomeInfo(status="no_migration_needed", output_file=None),
    )

    data = json.loads(report.to_json())

    assert data["baseline"] is None
    assert data["gate"] is None
    assert data["outcome"] == {"status": "no_migration_needed", "output_file": None}
    assert MigrationReport.from_json(report.to_json()) == report


def test_unknown_schema_is_rejected() -> None:
    data = json.loads(build_golden_report().to_json())
    data["schema_version"] = 99

    with pytest.raises(MigrationError, match="schema_version"):
        MigrationReport.from_json(json.dumps(data))


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(MigrationError, match="not valid JSON"):
        MigrationReport.from_json("{not json")
