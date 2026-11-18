"""Stable migration report (JSON schema version 1).

The report is the persistent evidence artefact of a migration: the source hash,
the per-part detection, the baseline and target metrics and the gate verdict. It
is deterministic (fixed key order, ISO 8601 timestamps, no NaN/Infinity) so it
can be committed as a golden fixture and compared byte-for-byte.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from aas_bridge.engine.detect import DetectionResult, PartDetection
from aas_bridge.exceptions import MigrationError

SCHEMA_VERSION = 1

REPORT_KEYS = (
    "schema_version",
    "tool_version",
    "generated_at",
    "source",
    "detected",
    "target",
    "rules_applied",
    "baseline",
    "gate",
    "outcome",
)


@dataclass(frozen=True)
class SourceInfo:
    """Identity of the migrated input file."""

    file: str
    sha256: str


@dataclass(frozen=True)
class TargetInfo:
    """Target version and the dialect that validated it."""

    version_label: str
    namespace: str
    basyx_version: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_label": self.version_label,
            "namespace": self.namespace,
            "basyx_version": self.basyx_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TargetInfo:
        return cls(
            version_label=data["version_label"],
            namespace=data["namespace"],
            basyx_version=data["basyx_version"],
        )


@dataclass(frozen=True)
class Metrics:
    """Load metrics used to compare a baseline against a migrated package."""

    basyx_version: str
    total: int
    counts: dict[str, int]
    ids_sha256: str
    semantic_ids_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "basyx_version": self.basyx_version,
            "total": self.total,
            "counts": {
                "aas": self.counts.get("aas", 0),
                "submodels": self.counts.get("submodels", 0),
                "concept_descriptions": self.counts.get("concept_descriptions", 0),
            },
            "ids_sha256": self.ids_sha256,
            "semantic_ids_sha256": self.semantic_ids_sha256,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Metrics:
        return cls(
            basyx_version=data["basyx_version"],
            total=data["total"],
            counts=dict(data["counts"]),
            ids_sha256=data["ids_sha256"],
            semantic_ids_sha256=data["semantic_ids_sha256"],
        )


@dataclass(frozen=True)
class GateInfo:
    """Evidence-gate verdict and the target metrics it was based on."""

    result: Literal["pass", "fail"]
    target: Metrics | None
    round_trip: bool
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "target": self.target.to_dict() if self.target is not None else None,
            "round_trip": self.round_trip,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GateInfo:
        target = data["target"]
        return cls(
            result=data["result"],
            target=Metrics.from_dict(target) if target is not None else None,
            round_trip=data["round_trip"],
            message=data["message"],
        )


@dataclass(frozen=True)
class OutcomeInfo:
    """Final status of the migration and the emitted file, if any."""

    status: Literal["emitted", "no_migration_needed", "refused"]
    output_file: str | None

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "output_file": self.output_file}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutcomeInfo:
        return cls(status=data["status"], output_file=data["output_file"])


@dataclass(frozen=True)
class MigrationReport:
    """Stable, serialisable evidence report for one migration attempt."""

    tool_version: str
    generated_at: datetime
    source: SourceInfo
    detected: DetectionResult
    target: TargetInfo
    rules_applied: list[str]
    baseline: Metrics | None
    gate: GateInfo | None
    outcome: OutcomeInfo
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "generated_at": _isoformat(self.generated_at),
            "source": {"file": self.source.file, "sha256": self.source.sha256},
            "detected": {
                "version_label": self.detected.version_label,
                "consistent": self.detected.consistent,
                "parts": [_part_to_dict(part) for part in self.detected.parts],
            },
            "target": self.target.to_dict(),
            "rules_applied": list(self.rules_applied),
            "baseline": self.baseline.to_dict() if self.baseline is not None else None,
            "gate": self.gate.to_dict() if self.gate is not None else None,
            "outcome": self.outcome.to_dict(),
        }

    def to_json(self) -> str:
        """Serialise the report with stable key order and no NaN/Infinity."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, allow_nan=False) + "\n"

    @classmethod
    def from_json(cls, payload: str) -> MigrationReport:
        """Reconstruct a report from its JSON representation."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise MigrationError(
                f"Report is not valid JSON ({exc}). Check that the file was not truncated."
            ) from exc
        if not isinstance(data, dict):
            raise MigrationError("Report JSON must be an object at the top level.")
        schema_version = data.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            raise MigrationError(
                f"Unsupported report schema_version {schema_version!r}; "
                f"this build reads version {SCHEMA_VERSION}."
            )
        try:
            detected_data = data["detected"]
            source_data = data["source"]
            parts = [
                PartDetection(
                    part_name=part["part_name"],
                    format=part["format"],
                    declared_version=part["declared_version"],
                    version_label=part["version_label"],
                )
                for part in detected_data["parts"]
            ]
            baseline_data = data["baseline"]
            gate_data = data["gate"]
            outcome_data = data["outcome"]
            return cls(
                tool_version=data["tool_version"],
                generated_at=datetime.fromisoformat(data["generated_at"]),
                source=SourceInfo(file=source_data["file"], sha256=source_data["sha256"]),
                detected=DetectionResult(
                    file=source_data["file"],
                    parts=parts,
                    consistent=detected_data["consistent"],
                    version_label=detected_data["version_label"],
                ),
                target=TargetInfo.from_dict(data["target"]),
                rules_applied=list(data["rules_applied"]),
                baseline=Metrics.from_dict(baseline_data) if baseline_data is not None else None,
                gate=GateInfo.from_dict(gate_data) if gate_data is not None else None,
                outcome=OutcomeInfo.from_dict(outcome_data),
                schema_version=schema_version,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MigrationError(
                f"Report is missing or has an invalid field ({exc}). "
                "Regenerate it with 'aas-bridge migrate --report'."
            ) from exc


def _part_to_dict(part: PartDetection) -> dict[str, Any]:
    return {
        "part_name": part.part_name,
        "format": part.format,
        "declared_version": part.declared_version,
        "version_label": part.version_label,
    }


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def empty_counts() -> dict[str, int]:
    """Return zeroed object counts in the report's canonical key order."""
    return {"aas": 0, "submodels": 0, "concept_descriptions": 0}
