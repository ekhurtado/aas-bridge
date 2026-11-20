"""Unit tests for the verified ecosystem registry (offline, no network)."""

from __future__ import annotations

import importlib.metadata
from datetime import date

import pytest

from aas_bridge.exceptions import ProbeError
from aas_bridge.probes.pypi import SmiaPinFact
from aas_bridge.registry.ecosystem import smia, specs


def _not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)


def _installed(monkeypatch: pytest.MonkeyPatch, version: str, requirements: list[str]) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda name: version)
    monkeypatch.setattr(importlib.metadata, "requires", lambda name: requirements)


def test_smia_release_table_matches_the_verified_evidence() -> None:
    assert len(smia.SMIA_RELEASES) == 10
    for version, release in smia.SMIA_RELEASES.items():
        assert release.smia_version == version
        assert release.basyx_pin.startswith(("==", "~=")), version
        assert date.fromisoformat(release.released), version
        assert release.source == smia.SOURCE_NOTE

    assert smia.SMIA_RELEASES["0.2.2"].basyx_pin == "==1.1.0"
    assert smia.SMIA_RELEASES["0.2.4"].basyx_pin == "==1.2.0"
    assert smia.SMIA_RELEASES["1.0.3"].basyx_pin == "~=1.2.1"
    assert smia.SMIA_RELEASES["1.0.3"].released == "2026-10-21"


@pytest.mark.parametrize(
    ("pin", "expected"),
    [
        ("~=1.2.1", ["3.0"]),
        ("==1.2.0", ["3.0"]),
        ("==1.1.0", ["3.0"]),
        ("~=2.0.1", ["3.0"]),
        ("~=2.2", ["3.1"]),
        ("==2.2.0", ["3.1"]),
        ("basyx-python-sdk~=1.2.1", ["3.0"]),
        ("~=3.0", []),
        ("", []),
        ("unknown", []),
    ],
)
def test_readable_aas_for_pin(pin: str, expected: list[str]) -> None:
    assert smia.readable_aas_for_pin(pin) == expected


def test_readable_aas_for_pin_returns_a_copy() -> None:
    smia.readable_aas_for_pin("~=1.2.1").append("9.9")
    assert smia.BASYX_AAS_READABILITY["1.x"] == ["3.0"]


def test_artifact_sources_match_the_verified_evidence() -> None:
    assert set(specs.ARTIFACT_SOURCES) == {"3.0", "3.1"}
    assert specs.ARTIFACT_SOURCES["3.0"].tag == "IDTA-01001-3-0-1_schemasV3.0.9"
    assert specs.ARTIFACT_SOURCES["3.0"].tag_date == "2024-11-15"
    assert specs.ARTIFACT_SOURCES["3.1"].tag == "v3.1.2"
    assert specs.ARTIFACT_SOURCES["3.1"].tag_date == "2025-11-10"
    for version in specs.ARTIFACT_SOURCES.values():
        assert version.licence == "CC-BY-4.0"
        assert "IDTA" in version.attribution
        paths = {artifact.kind: artifact.path for artifact in version.artifacts}
        assert paths["xsd"] == "schemas/xml/AAS.xsd"
        assert paths["json-schema"] == "schemas/json/aas.json"
    # The 3.0 line publishes schemas only; the changelog exists from 3.1 on
    # (probed 2026-11-19; ISS-014 human-approved option A).
    assert [artifact.kind for artifact in specs.ARTIFACT_SOURCES["3.0"].artifacts] == [
        "xsd",
        "json-schema",
    ]
    assert [artifact.kind for artifact in specs.ARTIFACT_SOURCES["3.1"].artifacts] == [
        "xsd",
        "json-schema",
        "changelog",
    ]
    changelog = specs.ARTIFACT_SOURCES["3.1"].artifacts[-1]
    assert changelog.path.endswith("changelog.adoc")

    assert specs.OFFICIAL_SOURCE.repo == "admin-shell-io/aas-specs-metamodel"
    assert specs.OFFICIAL_SOURCE.releases_feed.endswith("/releases")
    assert {"3.0", "3.1", "3.2"} == specs.KNOWN_AAS_LABELS


@pytest.mark.parametrize(
    ("tag", "name", "expected"),
    [
        ("v3.1.2", "IDTA-01001-3-1-2", ("3.1", False)),
        ("v3.2.0", "IDTA-01001-3-2-0", ("3.2", False)),
        (
            "IDTA-01001-3-0-1_schemasV3.0.9",
            "IDTA-01001-3-0-1_schemasV3.0.9",
            ("3.0", False),
        ),
        ("V3.0.5RC02", "Release candidate", ("3.0", True)),
        ("v3.0.2.RC01", "v3.0.2.RC01", ("3.0", True)),
        ("v3.3.0", "IDTA-01001-3-3-0", ("3.3", False)),
        ("metamodel-update", "Documentation only", None),
        ("", "", None),
    ],
)
def test_parse_official_release(tag: str, name: str, expected: tuple[str, bool] | None) -> None:
    assert specs.parse_official_release(tag, name) == expected


def test_resolve_smia_prefers_the_installed_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _installed(monkeypatch, "1.0.3", ["typer~=0.29", "basyx-python-sdk~=1.2.1"])

    resolution = smia.resolve_smia(None, probe=lambda version: pytest.fail("probe used"))

    assert resolution.status == "installed"
    assert resolution.smia_version == "1.0.3"
    assert resolution.basyx_pin == "~=1.2.1"
    assert resolution.readable_aas == ["3.0"]
    assert "importlib.metadata" in resolution.source_note


def test_resolve_smia_installed_without_a_basyx_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    _installed(monkeypatch, "0.9.0", ["typer~=0.29"])

    resolution = smia.resolve_smia(None, probe=None)

    assert resolution.status == "installed"
    assert resolution.basyx_pin is None
    assert resolution.readable_aas == []


def test_resolve_smia_uses_the_registry_table(monkeypatch: pytest.MonkeyPatch) -> None:
    _not_installed(monkeypatch)

    resolution = smia.resolve_smia("0.2.2", probe=lambda version: pytest.fail("probe used"))

    assert resolution.status == "registry"
    assert resolution.smia_version == "0.2.2"
    assert resolution.basyx_pin == "==1.1.0"
    assert resolution.readable_aas == ["3.0"]
    assert "2026-11-19" in resolution.source_note


def test_resolve_smia_falls_back_to_the_pypi_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    _not_installed(monkeypatch)
    requested: list[str] = []

    def probe(version: str) -> SmiaPinFact:
        requested.append(version)
        return SmiaPinFact("0.1.0", "~=1.1.0", "2024-12-01")

    resolution = smia.resolve_smia("0.1.0", probe=probe)

    assert requested == ["0.1.0"]
    assert resolution.status == "pypi"
    assert resolution.basyx_pin == "~=1.1.0"
    assert resolution.readable_aas == ["3.0"]
    assert "2024-12-01" in resolution.source_note


def test_resolve_smia_pypi_release_without_a_basyx_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    _not_installed(monkeypatch)

    resolution = smia.resolve_smia("0.1.0", probe=lambda version: SmiaPinFact("0.1.0", None, None))

    assert resolution.status == "pypi"
    assert resolution.basyx_pin is None
    assert resolution.readable_aas == []
    assert "no basyx" in resolution.source_note.lower()


def test_resolve_smia_degrades_when_the_probe_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _not_installed(monkeypatch)

    def failing(version: str) -> SmiaPinFact:
        raise ProbeError("PyPI request to https://pypi.org/pypi/smia/0.1.0/json timed out")

    resolution = smia.resolve_smia("0.1.0", probe=failing)

    assert resolution.status == "unverified"
    assert resolution.smia_version == "0.1.0"
    assert resolution.basyx_pin is None
    assert "timed out" in resolution.source_note


def test_resolve_smia_without_installed_smia_or_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _not_installed(monkeypatch)

    resolution = smia.resolve_smia(None, probe=None)

    assert resolution.status == "unverified"
    assert resolution.smia_version is None
    assert resolution.readable_aas == []
    assert "no installed SMIA" in resolution.source_note


def test_resolve_smia_unknown_version_without_a_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    _not_installed(monkeypatch)

    resolution = smia.resolve_smia("9.9.9", probe=None)

    assert resolution.status == "unverified"
    assert resolution.smia_version == "9.9.9"
    assert resolution.basyx_pin is None
