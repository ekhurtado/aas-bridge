"""Unit tests for ``aas-bridge update`` (fake probes, no network)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aas_bridge import __version__
from aas_bridge.cli import actions
from aas_bridge.exceptions import ProbeError
from aas_bridge.probes.artifacts import FetchedArtifact, OfficialRelease
from aas_bridge.registry.ecosystem.specs import ARTIFACT_SOURCES

FIXED_TIME = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
RELEASES = [
    OfficialRelease("v3.2.0", "IDTA-01001-3-2-0", "2026-07-21", "3.2", False),
    OfficialRelease("v3.1.2", "IDTA-01001-3-1-2", "2025-11-10", "3.1", False),
    OfficialRelease("IDTA-01001-3-0-1_schemasV3.0.9", "schemas 3.0.9", "2024-11-15", "3.0", False),
    OfficialRelease("V3.0.5RC02", "V3.0.5RC02", "2022-09-12", "3.0", True),
]


def _artifact_entries(label: str, status: str = "fetched") -> list[FetchedArtifact]:
    version = ARTIFACT_SOURCES[label]
    return [
        FetchedArtifact(
            kind=spec.kind,
            aas_label=label,
            tag=version.tag,
            url=f"https://raw.githubusercontent.com/x/{version.tag}/{spec.path}",
            sha256=f"{label}-{spec.kind}-sha",
            size=1234,
            fetched_at="2026-11-19T12:00:00+00:00",
            status=status,
        )
        for spec in version.artifacts
    ]


def _artifacts_probe(label: str, directory: Path) -> list[FetchedArtifact]:
    return _artifact_entries(label)


def test_update_online_writes_the_full_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry = tmp_path / "registry"

    code = actions.execute_update(
        "en",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=_artifacts_probe,
        registry_dir=registry,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "Status: online" in output
    assert "Covered AAS versions: 3.0, 3.1" in output
    assert "Covered migration pairs: 3.0->3.1" in output
    assert "Known but not covered: 3.2" in output
    assert "NEW AAS versions: none" in output
    assert "V3.0.5RC02" in output
    assert output.count("[fetched]") == 5
    assert "no migration rule is created" in output

    manifest = json.loads((registry / "manifest.json").read_text(encoding="utf-8"))
    assert list(manifest) == [
        "schema_version",
        "tool_version",
        "generated_at",
        "registry_dir",
        "check",
        "artifacts",
    ]
    assert manifest["schema_version"] == 1
    assert manifest["tool_version"] == __version__
    assert manifest["generated_at"] == FIXED_TIME.isoformat()
    assert manifest["registry_dir"] == str(registry)
    check = manifest["check"]
    assert list(check) == [
        "online",
        "releases_seen",
        "covered_labels",
        "covered_pairs",
        "known_uncovered",
        "new_labels",
    ]
    assert check["online"] is True
    assert check["covered_labels"] == ["3.0", "3.1"]
    assert check["covered_pairs"] == ["3.0->3.1"]
    assert check["known_uncovered"] == ["3.2"]
    assert check["new_labels"] == []
    assert len(check["releases_seen"]) == 4
    assert list(check["releases_seen"][0]) == [
        "tag",
        "name",
        "published",
        "aas_label",
        "prerelease",
    ]

    artifacts = manifest["artifacts"]
    assert len(artifacts) == 5
    assert list(artifacts[0]) == [
        "kind",
        "aas_label",
        "tag",
        "url",
        "sha256",
        "size",
        "fetched_at",
        "status",
        "licence",
        "attribution",
    ]
    assert [entry["aas_label"] for entry in artifacts] == ["3.0"] * 2 + ["3.1"] * 3
    assert [entry["kind"] for entry in artifacts] == [
        "xsd",
        "json-schema",
        "xsd",
        "json-schema",
        "changelog",
    ]
    assert all(entry["status"] == "fetched" for entry in artifacts)
    assert all(entry["licence"] == "CC-BY-4.0" for entry in artifacts)
    assert all("IDTA" in entry["attribution"] for entry in artifacts)


def test_update_reports_a_new_aas_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    releases = RELEASES + [
        OfficialRelease("v3.3.0", "IDTA-01001-3-3-0", "2026-12-01", "3.3", False)
    ]

    code = actions.execute_update(
        "en",
        releases_probe=lambda: releases,
        artifacts_probe=_artifacts_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    assert "NEW AAS versions (ingest pending — Phase 4): 3.3" in capsys.readouterr().out
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["check"]["new_labels"] == ["3.3"]


def test_update_prereleases_are_never_new(tmp_path: Path) -> None:
    releases = RELEASES + [OfficialRelease("v3.4.0RC01", "3.4 RC", "2027-01-01", "3.4", True)]

    actions.execute_update(
        "en",
        releases_probe=lambda: releases,
        artifacts_probe=_artifacts_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["check"]["new_labels"] == []


def test_update_offline_is_degraded_but_exit_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def offline() -> list[OfficialRelease]:
        raise ProbeError("Cannot reach GitHub (timed out)")

    def artifacts_must_not_run(label: str, directory: Path) -> list[FetchedArtifact]:
        raise AssertionError("artifacts must not be fetched while offline")

    registry = tmp_path / "registry"

    code = actions.execute_update(
        "en",
        releases_probe=offline,
        artifacts_probe=artifacts_must_not_run,
        registry_dir=registry,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    output = capsys.readouterr()
    assert "Status: offline — degraded" in output.out
    assert "Cannot reach GitHub" in output.err
    assert output.out.count("[skipped (offline)]") == 5

    manifest = json.loads((registry / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["check"]["online"] is False
    assert manifest["check"]["releases_seen"] == []
    assert all(entry["status"] == "skipped_offline" for entry in manifest["artifacts"])
    assert all(entry["sha256"] is None for entry in manifest["artifacts"])


def test_update_artifact_failure_does_not_abort_the_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_probe(label: str, directory: Path) -> list[FetchedArtifact]:
        if label == "3.1":
            raise ProbeError("HTTP 404 while downloading schemas/xml/AAS.xsd")
        return _artifact_entries(label)

    code = actions.execute_update(
        "en",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=failing_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    output = capsys.readouterr()
    assert "Cannot fetch the AAS 3.1 artifacts" in output.err
    assert output.out.count("[failed]") == 3
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    statuses = [entry["status"] for entry in manifest["artifacts"]]
    assert statuses == ["fetched"] * 2 + ["failed"] * 3


def test_update_manifest_is_deterministic(tmp_path: Path) -> None:
    actions.execute_update(
        "en",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=_artifacts_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )
    first = (tmp_path / "manifest.json").read_bytes()
    actions.execute_update(
        "en",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=_artifacts_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )
    second = (tmp_path / "manifest.json").read_bytes()

    assert first == second
    actions.execute_update(
        "en",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=_artifacts_probe,
        registry_dir=tmp_path,
        generated_at=FIXED_TIME + timedelta(minutes=1),
    )
    third = (tmp_path / "manifest.json").read_bytes()
    assert third != first
    assert b'"generated_at": "2026-11-19T12:01:00+00:00"' in third


def test_update_creates_the_registry_directory_on_demand(tmp_path: Path) -> None:
    registry = tmp_path / "nested" / "registry"

    code = actions.execute_update(
        "es",
        releases_probe=lambda: list(RELEASES),
        artifacts_probe=_artifacts_probe,
        registry_dir=registry,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    assert (registry / "manifest.json").is_file()


def test_update_offline_in_spanish(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def offline() -> list[OfficialRelease]:
        raise ProbeError("timed out")

    code = actions.execute_update(
        "es",
        releases_probe=offline,
        artifacts_probe=lambda label, directory: _artifact_entries(label),
        registry_dir=tmp_path,
        generated_at=FIXED_TIME,
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "Estado: sin conexión — degradado" in output
    assert "Versiones de AAS cubiertas: 3.0, 3.1" in output
    assert "omitido (sin conexión)" in output
