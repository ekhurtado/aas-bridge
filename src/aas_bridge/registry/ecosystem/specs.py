"""Official AAS metamodel artifact sources (verified 2026-11-19).

Facts trace to ``.ai/ECOSYSTEM_COMPATIBILITY.md`` §8: the GitHub repository
``admin-shell-io/aas-specs-metamodel`` (CC-BY-4.0), its Releases feed and the
stable per-version artifact paths. The module is pure: no network access and no
I/O; ``probes.artifacts`` performs the actual fetches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Literal

ArtifactKind = Literal["xsd", "json-schema", "changelog"]

#: CC-BY-4.0 attribution required for every fetched IDTA artifact (L2-15).
ATTRIBUTION: Final[str] = (
    "IDTA-01001 Metamodel of the Asset Administration Shell, "
    "(c) Industrial Digital Twin Association (IDTA), CC-BY-4.0"
)
LICENCE: Final[str] = "CC-BY-4.0"


@dataclass(frozen=True)
class ArtifactSpec:
    """One official artifact of a pinned AAS version tag."""

    kind: ArtifactKind
    path: str


@dataclass(frozen=True)
class VersionArtifacts:
    """Pinned tag, date and artifact list for one AAS version label."""

    aas_label: str
    tag: str
    tag_date: str
    artifacts: list[ArtifactSpec]
    licence: str
    attribution: str


_SCHEMA_ARTIFACTS: Final[tuple[ArtifactSpec, ...]] = (
    ArtifactSpec("xsd", "schemas/xml/AAS.xsd"),
    ArtifactSpec("json-schema", "schemas/json/aas.json"),
)

_CHANGELOG_ARTIFACT: Final[ArtifactSpec] = ArtifactSpec(
    "changelog", "documentation/IDTA-01001/modules/ROOT/pages/changelog.adoc"
)

# The metamodel schemas exist for every AAS line. The changelog is published only
# from the 3.1 line onwards: every verified 3.0 tag (IDTA-01001-3-0-1_schemasV3.0.9,
# ...V3.0.8, V3.0.7, v3.0.6, V3.0.5RC02) has no `documentation/` folder and returns
# HTTP 404 for it (probed 2026-11-19; ISS-014, human-approved option A).
ARTIFACT_SOURCES: Final[dict[str, VersionArtifacts]] = {
    "3.0": VersionArtifacts(
        aas_label="3.0",
        tag="IDTA-01001-3-0-1_schemasV3.0.9",
        tag_date="2024-11-15",
        artifacts=list(_SCHEMA_ARTIFACTS),
        licence=LICENCE,
        attribution=ATTRIBUTION,
    ),
    "3.1": VersionArtifacts(
        aas_label="3.1",
        tag="v3.1.2",
        tag_date="2025-11-10",
        artifacts=[*_SCHEMA_ARTIFACTS, _CHANGELOG_ARTIFACT],
        licence=LICENCE,
        attribution=ATTRIBUTION,
    ),
}


@dataclass(frozen=True)
class OfficialSource:
    """Machine-readable official release source of the AAS metamodel."""

    repo: str
    releases_feed: str
    raw_base: str


OFFICIAL_SOURCE: Final[OfficialSource] = OfficialSource(
    repo="admin-shell-io/aas-specs-metamodel",
    releases_feed=("https://api.github.com/repos/admin-shell-io/aas-specs-metamodel/releases"),
    raw_base="https://raw.githubusercontent.com/admin-shell-io/aas-specs-metamodel",
)

#: AAS metamodel lines known to the tool (evidence §3: 3.2.0 published Jul 2026).
KNOWN_AAS_LABELS: Final[set[str]] = {"3.0", "3.1", "3.2"}

_IDTA_TAG_RE = re.compile(r"IDTA-01001-(\d+)-(\d+)-")
_SEMVER_TAG_RE = re.compile(r"(?<![\d.])v?(\d+)\.(\d+)", re.IGNORECASE)
_PRERELEASE_RE = re.compile(r"(?:rc\d+|release\s+candidate|pre-?release)", re.IGNORECASE)


def parse_official_release(tag: str, name: str) -> tuple[str, bool] | None:
    """Map a release tag/name to ``(aas_label, prerelease)`` or ``None``.

    Examples: ``v3.1.2`` -> ``("3.1", False)``, ``IDTA-01001-3-2-0`` ->
    ``("3.2", False)``, ``IDTA-01001-3-0-1_schemasV3.0.9`` -> ``("3.0", False)``,
    ``V3.0.5RC02`` / ``v3.0.2.RC01`` -> prereleases of ``("3.0", True)``. Junk
    returns ``None`` so it can never be reported as a new AAS line.
    """
    prerelease = bool(_PRERELEASE_RE.search(tag or "") or _PRERELEASE_RE.search(name or ""))
    for text in (tag or "", name or ""):
        match = _IDTA_TAG_RE.search(text) or _SEMVER_TAG_RE.search(text)
        if match is not None:
            label = f"{int(match.group(1))}.{int(match.group(2))}"
            return label, prerelease
    return None
