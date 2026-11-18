"""The evidence gate: baseline, transform, target load, round-trip, emit-only-on-pass.

Mechanism (ADR-021): the tool swaps ``basyx-python-sdk`` in the project venv and
runs every basyx load in a subprocess. The main process never imports basyx, so
the GUI/CLI in the same venv cannot keep a stale SDK in ``sys.modules``. The venv
is always restored to the target dialect in a ``finally`` block, baselines are
cached by (file sha256, dialect requirement), and gate executions are serialized
with an exclusive lock file.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from aas_bridge import __version__
from aas_bridge.engine.detect import DetectionResult, detect_versions
from aas_bridge.engine.report import (
    GateInfo,
    Metrics,
    MigrationReport,
    OutcomeInfo,
    SourceInfo,
    TargetInfo,
)
from aas_bridge.engine.transformer import transform
from aas_bridge.exceptions import EvidenceGateError, MigrationError, ProbeError
from aas_bridge.registry.versions import AAS_VERSION_IRIS, DIALECT_MAP, TARGET_VERSION_LABEL

logger = logging.getLogger(__name__)

BASELINE_LOADER_MODULE = "aas_bridge.engine._loaders.baseline_loader"
TARGET_LOADER_MODULE = "aas_bridge.engine._loaders.target_loader"
DIALECT_PROBE_MODULE = "aas_bridge.engine._loaders.dialect_probe"

TARGET_REQUIREMENT = DIALECT_MAP[TARGET_VERSION_LABEL]
TARGET_NAMESPACE = AAS_VERSION_IRIS[TARGET_VERSION_LABEL]

PIP_TIMEOUT_SECONDS = 600
LOADER_TIMEOUT_SECONDS = 120
LOCK_STALE_AFTER_SECONDS = 30 * 60
LOCK_FILE_NAME = "gate.lock"
CACHE_ENV_VAR = "AASBRIDGE_CACHE_DIR"


@dataclass(frozen=True)
class MigrationOutcome:
    """Public result of :func:`run_migration`."""

    status: Literal["emitted", "no_migration_needed", "refused"]
    report: MigrationReport
    output_path: Path | None


class _LoaderError(ProbeError):
    """A loader subprocess exited non-zero; the code distinguishes a 0-object load."""

    def __init__(self, message: str, returncode: int) -> None:
        super().__init__(message)
        self.returncode = returncode


def run_migration(
    source: Path,
    report_path: Path | None = None,
    generated_at: datetime | None = None,
) -> MigrationOutcome:
    """Run the full evidence-gated migration for one package.

    The input is never modified. The adapted file is emitted only when the target
    load reproduces the baseline and the round-trip succeeds.

    Raises:
        DetectionError: the input is not a readable AASX package.
        MigrationError: the version is undetectable/inconsistent or the migration
            cannot be planned (for example JSON parts).
        EvidenceGateError: the baseline is empty, the installed dialect does not
            match the registry target, or the target load differs from the baseline.
        ProbeError: pip or a loader subprocess failed; the message names both
            dialects and the exact recovery command.
    """
    source_path = Path(source)
    if not source_path.is_file():
        raise MigrationError(
            f"Input file not found: {source_path}. Provide the path to an existing .aasx package."
        )
    generated = generated_at if generated_at is not None else datetime.now(UTC)
    cache_dir = cache_directory()
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProbeError(
            f"Cannot create the gate cache directory {cache_dir} ({exc}). "
            "Set AASBRIDGE_CACHE_DIR to a writable directory."
        ) from exc

    with _exclusive_lock(cache_dir):
        return _run_migration_locked(source_path, report_path, generated, cache_dir)


def cache_directory() -> Path:
    """Return the baseline cache directory (``AASBRIDGE_CACHE_DIR`` overrides)."""
    override = os.environ.get(CACHE_ENV_VAR)
    if override:
        return Path(override)
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base / "aasbridge" / "cache"
    return Path.home() / ".cache" / "aasbridge"


def _run_migration_locked(
    source_path: Path,
    report_path: Path | None,
    generated: datetime,
    cache_dir: Path,
) -> MigrationOutcome:
    detection = detect_versions(source_path)
    if not detection.consistent or detection.version_label is None:
        raise MigrationError(_undetectable_message(source_path, detection))

    source_sha = _sha256_file(source_path)
    if detection.version_label == TARGET_VERSION_LABEL:
        report = _build_report(
            source_path=source_path,
            source_sha=source_sha,
            detection=detection,
            target=TargetInfo(
                version_label=TARGET_VERSION_LABEL,
                namespace=TARGET_NAMESPACE,
                basyx_version=None,
            ),
            rules_applied=[],
            baseline=None,
            gate=None,
            outcome=OutcomeInfo(status="no_migration_needed", output_file=None),
            generated=generated,
        )
        _write_report(report, report_path)
        return MigrationOutcome(status="no_migration_needed", report=report, output_path=None)

    source_label = detection.version_label
    if source_label not in DIALECT_MAP:
        raise MigrationError(
            f"No basyx dialect is registered for AAS {source_label}. "
            "Add the version to aas_bridge.registry.versions before migrating."
        )

    baseline_requirement = DIALECT_MAP[source_label]
    baseline = _obtain_baseline(source_path, source_sha, baseline_requirement, cache_dir)
    probe = _probe_dialect()
    verified_namespace = _verified_target_namespace(probe)
    target = TargetInfo(
        version_label=TARGET_VERSION_LABEL,
        namespace=verified_namespace,
        basyx_version=str(probe["basyx_version"]),
    )

    transform_result = transform(source_path, verified_namespace)
    adapted_path = transform_result.output_path

    try:
        target_payload = _run_loader(
            TARGET_LOADER_MODULE, [str(adapted_path)], LOADER_TIMEOUT_SECONDS
        )
    except _LoaderError as exc:
        adapted_path.unlink(missing_ok=True)
        if exc.returncode == 3:
            raise EvidenceGateError(
                f"Target dialect basyx {TARGET_REQUIREMENT} loaded 0 objects from "
                f"{adapted_path}. The adapted file was removed and not emitted."
            ) from exc
        raise ProbeError(
            f"Target load failed: {exc}\n"
            f"Baseline dialect: {baseline_requirement}. "
            f"Target dialect: {TARGET_REQUIREMENT}.\n"
            f"Manual recovery: {_recovery_command()}"
        ) from exc

    gate_info, differences = _evaluate_gate(baseline, target_payload)
    outcome = OutcomeInfo(
        status="emitted" if gate_info.result == "pass" else "refused",
        output_file=str(adapted_path) if gate_info.result == "pass" else None,
    )
    report = _build_report(
        source_path=source_path,
        source_sha=source_sha,
        detection=detection,
        target=target,
        rules_applied=[transform_result.rule_id],
        baseline=Metrics.from_dict(baseline),
        gate=gate_info,
        outcome=outcome,
        generated=generated,
    )

    if gate_info.result == "pass":
        _write_report(report, report_path)
        return MigrationOutcome(status="emitted", report=report, output_path=adapted_path)

    adapted_path.unlink(missing_ok=True)
    logger.error("Evidence gate refused %s: %s", source_path, "; ".join(differences))
    # The public contract raises on a failed gate; when a report path is given,
    # persist the refused report first so the fail-closed evidence survives.
    _write_report(report, report_path)
    error = EvidenceGateError(
        _gate_failure_message(source_path, differences, baseline, target_payload)
    )
    error.report = report  # type: ignore[attr-defined]
    raise error


def _obtain_baseline(
    source_path: Path,
    source_sha: str,
    requirement: str,
    cache_dir: Path,
) -> dict[str, Any]:
    cached = _read_cached_baseline(cache_dir, source_sha, requirement)
    if cached is not None:
        logger.info("Baseline cache hit for %s (%s)", source_path, requirement)
        return cached

    try:
        _pip_install(requirement)
        payload = _run_loader(BASELINE_LOADER_MODULE, [str(source_path)], LOADER_TIMEOUT_SECONDS)
    except _LoaderError as exc:
        if exc.returncode == 3:
            raise EvidenceGateError(
                f"Baseline dialect basyx {requirement} loaded 0 objects from "
                f"{source_path}. The detected version and the installable dialect "
                "disagree; no baseline exists, so no migration can be proven."
            ) from exc
        raise ProbeError(
            f"Baseline load failed: {exc}\n"
            f"Baseline dialect: {requirement}. Target dialect: {TARGET_REQUIREMENT}.\n"
            f"Manual recovery: {_recovery_command()}"
        ) from exc
    except ProbeError as exc:
        raise ProbeError(
            f"{exc}\nBaseline dialect: {requirement}. "
            f"Target dialect: {TARGET_REQUIREMENT}.\n"
            f"Manual recovery: {_recovery_command()}"
        ) from exc
    finally:
        _restore_target_dialect(requirement)

    missing = [key for key in _metric_keys() if key not in payload]
    if missing:
        raise ProbeError(
            f"baseline_loader output is missing {missing}. "
            "The installed basyx is incompatible with this tool build."
        )
    if int(payload["total"]) <= 0:
        raise EvidenceGateError(
            f"Baseline dialect basyx {requirement} loaded 0 objects from {source_path}. "
            "The adapted file will not be emitted."
        )
    _write_cached_baseline(cache_dir, source_sha, requirement, payload)
    return payload


def _read_cached_baseline(
    cache_dir: Path, source_sha: str, requirement: str
) -> dict[str, Any] | None:
    cache_path = cache_dir / _cache_file_name(source_sha, requirement)
    if not cache_path.is_file():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring unreadable baseline cache %s (%s)", cache_path, exc)
        return None
    if not isinstance(payload, dict) or payload.get("requirement") != requirement:
        return None
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict) or int(metrics.get("total", 0)) <= 0:
        return None
    if any(key not in metrics for key in _metric_keys()):
        return None
    return metrics


def _write_cached_baseline(
    cache_dir: Path, source_sha: str, requirement: str, metrics: Mapping[str, Any]
) -> None:
    cache_path = cache_dir / _cache_file_name(source_sha, requirement)
    temporary = cache_path.with_name(cache_path.name + ".tmp")
    payload = {
        "schema_version": 1,
        "requirement": requirement,
        "metrics": dict(metrics),
    }
    try:
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, cache_path)
    except OSError as exc:
        logger.warning("Could not write baseline cache %s (%s)", cache_path, exc)
        temporary.unlink(missing_ok=True)


def _cache_file_name(source_sha: str, requirement: str) -> str:
    safe_requirement = re.sub(r"[^A-Za-z0-9_.-]+", "_", requirement)
    return f"baseline-{source_sha}-{safe_requirement}.json"


def _probe_dialect() -> dict[str, Any]:
    try:
        payload = _run_loader(DIALECT_PROBE_MODULE, [], LOADER_TIMEOUT_SECONDS)
    except ProbeError as exc:
        raise ProbeError(
            f"Dialect probe failed: {exc}\nTarget dialect: {TARGET_REQUIREMENT}.\n"
            f"Manual recovery: {_recovery_command()}"
        ) from exc
    if not isinstance(payload.get("basyx_version"), str) or not isinstance(
        payload.get("ns_aas"), str
    ):
        raise ProbeError(
            "dialect_probe output does not contain basyx_version and ns_aas. "
            "The installed basyx is incompatible with this tool build."
        )
    return payload


def _verified_target_namespace(probe: Mapping[str, Any]) -> str:
    raw_namespace = str(probe["ns_aas"])
    iri = raw_namespace.strip("{}")
    if iri != TARGET_NAMESPACE:
        raise EvidenceGateError(
            f"The installed basyx reports the namespace {raw_namespace}, but the "
            f"registry target is {TARGET_NAMESPACE}. Refusing to transform against "
            f"an unverified dialect. Ensure {TARGET_REQUIREMENT} is installed with: "
            f"{_recovery_command()}"
        )
    return iri


def _evaluate_gate(
    baseline: Mapping[str, Any], target_payload: Mapping[str, Any]
) -> tuple[GateInfo, list[str]]:
    missing = [key for key in _metric_keys() if key not in target_payload]
    if missing:
        raise ProbeError(
            f"target_loader output is missing {missing}. "
            "The installed basyx is incompatible with this tool build."
        )
    round_trip = target_payload.get("round_trip")
    if not isinstance(round_trip, dict) or "ok" not in round_trip:
        raise ProbeError(
            "target_loader output does not contain a round_trip result. "
            "Refusing to trust an unverifiable load."
        )

    differences: list[str] = []
    target_total = int(target_payload["total"])
    if target_total <= 0:
        differences.append("target loaded 0 objects")
    if target_total != int(baseline["total"]):
        differences.append(f"total {baseline['total']} -> {target_total}")
    if dict(target_payload["counts"]) != dict(baseline["counts"]):
        differences.append(f"counts {baseline['counts']} -> {target_payload['counts']}")
    if target_payload["ids_sha256"] != baseline["ids_sha256"]:
        differences.append("identifiers hash changed")
    if target_payload["semantic_ids_sha256"] != baseline["semantic_ids_sha256"]:
        differences.append("semanticIds hash changed")
    if not bool(round_trip["ok"]):
        differences.append(f"round-trip mismatch {round_trip.get('differences', 'unknown')}")

    target_metrics = {key: target_payload[key] for key in _metric_keys()}
    gate_info = GateInfo(
        result="fail" if differences else "pass",
        target=Metrics.from_dict(target_metrics),
        round_trip=bool(round_trip["ok"]),
        message="; ".join(differences) if differences else None,
    )
    return gate_info, differences


def _build_report(
    *,
    source_path: Path,
    source_sha: str,
    detection: DetectionResult,
    target: TargetInfo,
    rules_applied: list[str],
    baseline: Metrics | None,
    gate: GateInfo | None,
    outcome: OutcomeInfo,
    generated: datetime,
) -> MigrationReport:
    return MigrationReport(
        tool_version=__version__,
        generated_at=generated,
        source=SourceInfo(file=str(source_path), sha256=source_sha),
        detected=detection,
        target=target,
        rules_applied=rules_applied,
        baseline=baseline,
        gate=gate,
        outcome=outcome,
    )


def _write_report(report: MigrationReport, report_path: Path | None) -> None:
    if report_path is None:
        return
    destination = Path(report_path)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_text(report.to_json(), encoding="utf-8")
        os.replace(temporary, destination)
    except OSError as exc:
        raise MigrationError(
            f"Could not write the migration report to {destination} ({exc}). "
            "Check the path and permissions; the package result is unchanged."
        ) from exc


def _undetectable_message(source_path: Path, detection: DetectionResult) -> str:
    details = ", ".join(
        f"{part.part_name}={part.declared_version or 'undetectable'}" for part in detection.parts
    )
    return (
        f"Cannot determine a single AAS version for {source_path} ({details}). "
        "A migration needs consistent AAS 3.0 declarations; re-export the package "
        "from a single toolchain and retry."
    )


def _gate_failure_message(
    source_path: Path,
    differences: list[str],
    baseline: Mapping[str, Any],
    target_payload: Mapping[str, Any],
) -> str:
    return (
        f"Evidence gate failed for {source_path}: {'; '.join(differences)}. "
        f"Baseline basyx {baseline['basyx_version']} produced {baseline['total']} "
        f"objects; target basyx {target_payload['basyx_version']} produced "
        f"{target_payload['total']}. The adapted file was removed and not emitted."
    )


def _metric_keys() -> tuple[str, ...]:
    return ("basyx_version", "total", "counts", "ids_sha256", "semantic_ids_sha256")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pip_install(requirement: str) -> None:
    command = [sys.executable, "-m", "pip", "install", "--no-input", requirement]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=PIP_TIMEOUT_SECONDS,
            check=False,
            env=_subprocess_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(
            f"pip install {requirement} timed out after {PIP_TIMEOUT_SECONDS}s."
        ) from exc
    except OSError as exc:
        raise ProbeError(f"Could not run pip install {requirement} ({exc}).") from exc
    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout or "").strip()
        raise ProbeError(
            f"pip install {requirement} failed with exit {completed.returncode}: {output}"
        )


def _restore_target_dialect(baseline_requirement: str) -> None:
    try:
        _pip_install(TARGET_REQUIREMENT)
    except ProbeError as exc:
        raise ProbeError(
            f"Could not restore the venv to {TARGET_REQUIREMENT} after the "
            f"{baseline_requirement} baseline: {exc}\n"
            f"Baseline dialect: {baseline_requirement}. "
            f"Target dialect: {TARGET_REQUIREMENT}.\n"
            f"Manual recovery: {_recovery_command()}"
        ) from exc


def _run_loader(module: str, arguments: Sequence[str], timeout: int) -> dict[str, Any]:
    command = [sys.executable, "-m", module, *arguments]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
            env=_subprocess_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"{module} timed out after {timeout}s for {arguments}.") from exc
    except OSError as exc:
        raise ProbeError(f"Could not run {module} ({exc}).") from exc

    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout or "").strip()
        raise _LoaderError(
            f"{module} exited {completed.returncode}: {output}", completed.returncode
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(
            f"{module} did not print valid JSON ({exc}): {completed.stdout[:500]!r}"
        ) from exc
    if not isinstance(payload, dict):
        raise ProbeError(f"{module} must print a JSON object, got {type(payload).__name__}.")
    return payload


def _subprocess_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    return environment


def _recovery_command() -> str:
    return f'{sys.executable} -m pip install "{TARGET_REQUIREMENT}"'


@contextmanager
def _exclusive_lock(cache_dir: Path) -> Iterator[None]:
    lock_path = cache_dir / LOCK_FILE_NAME
    descriptor = _acquire_lock_descriptor(lock_path)
    try:
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _acquire_lock_descriptor(lock_path: Path) -> int:
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        age = _lock_age_seconds(lock_path)
        if age is not None and age > LOCK_STALE_AFTER_SECONDS:
            logger.warning(
                "Breaking stale gate lock %s (age %.0fs > %ss)",
                lock_path,
                age,
                LOCK_STALE_AFTER_SECONDS,
            )
            lock_path.unlink(missing_ok=True)
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ProbeError(
                    f"Another AAS Bridge migration acquired the gate lock {lock_path}. "
                    "Wait for it to finish and retry."
                ) from exc
        else:
            raise ProbeError(
                f"Another AAS Bridge migration holds the gate lock {lock_path} "
                f"(age {age if age is not None else 'unknown'}s). Wait for it to "
                "finish and retry; delete the lock only if no migration is running."
            ) from None
    os.write(descriptor, f"pid={os.getpid()}\nstarted={time.time():.0f}\n".encode())
    return descriptor


def _lock_age_seconds(lock_path: Path) -> float | None:
    try:
        return time.time() - lock_path.stat().st_mtime
    except OSError:
        return None
