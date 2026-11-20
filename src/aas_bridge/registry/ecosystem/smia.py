"""Verified SMIA release knowledge and the basyx -> readable-AAS rules.

Every fact encoded here traces to ``.ai/ECOSYSTEM_COMPATIBILITY.md`` §1 (basyx
namespace matrix) and §7 (SMIA releases on PyPI, fetched 2026-11-19). The module
is pure: no network access and no I/O on import.

The static table keeps the tool useful offline. A PyPI probe can be injected
into :func:`resolve_smia` to cover releases that are not in the table yet; the
installed distribution metadata is authoritative when SMIA lives in the current
environment.

``SmiaResolution.source_note`` is a technical provenance token in English (for
example ``"importlib.metadata (offline)"``), not a translated sentence: the CLI
renders its own bilingual labels and prints the token as a detail.
"""

from __future__ import annotations

import importlib.metadata
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

from aas_bridge.exceptions import ProbeError

if TYPE_CHECKING:  # pragma: no cover - import used only for type checking
    from aas_bridge.probes.pypi import SmiaPinFact

SMIA_DISTRIBUTION: Final[str] = "smia"
BASYX_DISTRIBUTION: Final[str] = "basyx-python-sdk"

#: Dated provenance of :data:`SMIA_RELEASES`.
SOURCE_NOTE: Final[str] = "PyPI JSON API, fetched 2026-11-19"
REGISTRY_SOURCE_NOTE: Final[str] = "registry table 2026-11-19"


@dataclass(frozen=True)
class SmiaRelease:
    """One published SMIA release and the basyx pin it declares."""

    smia_version: str
    basyx_pin: str
    released: str
    source: str


SMIA_RELEASES: Final[dict[str, SmiaRelease]] = {
    release.smia_version: release
    for release in (
        SmiaRelease("0.2.2", "==1.1.0", "2025-02-27", SOURCE_NOTE),
        SmiaRelease("0.2.4", "==1.2.0", "2025-07-01", SOURCE_NOTE),
        SmiaRelease("0.3.0", "~=1.2.1", "2025-07-22", SOURCE_NOTE),
        SmiaRelease("0.3.1", "~=1.2.1", "2025-12-10", SOURCE_NOTE),
        SmiaRelease("0.3.2", "~=1.2.1", "2026-03-03", SOURCE_NOTE),
        SmiaRelease("0.3.4", "~=1.2.1", "2026-06-28", SOURCE_NOTE),
        SmiaRelease("0.3.5", "~=1.2.1", "2026-07-27", SOURCE_NOTE),
        SmiaRelease("1.0.0", "~=1.2.1", "2026-07-29", SOURCE_NOTE),
        SmiaRelease("1.0.2", "~=1.2.1", "2026-10-08", SOURCE_NOTE),
        SmiaRelease("1.0.3", "~=1.2.1", "2026-10-21", SOURCE_NOTE),
    )
}

#: basyx pin series -> AAS labels that dialect can read (evidence §1).
BASYX_AAS_READABILITY: Final[dict[str, list[str]]] = {
    "1.x": ["3.0"],
    "2.0.x": ["3.0"],
    ">=2.1": ["3.1"],
}

_PIN_VERSION_RE = re.compile(r"(\d+)(?:\.(\d+))?")
_DISTRIBUTION_PREFIX_RE = re.compile(r"^basyx-python-sdk\s*", re.IGNORECASE)


def readable_aas_for_pin(pin_spec: str) -> list[str]:
    """Return the AAS labels readable by the basyx dialect of ``pin_spec``.

    ``pin_spec`` is a version specifier such as ``"~=1.2.1"`` or ``"==2.2.0"``;
    an optional ``basyx-python-sdk`` prefix is tolerated. An unknown or
    unparsable specifier returns an empty list (fail-closed, never a guess).
    """
    specifier = _DISTRIBUTION_PREFIX_RE.sub("", pin_spec.strip())
    if not specifier:
        return []
    match = _PIN_VERSION_RE.search(specifier)
    if match is None:
        return []
    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) is not None else None
    if major == 1:
        return list(BASYX_AAS_READABILITY["1.x"])
    if major == 2 and minor == 0:
        return list(BASYX_AAS_READABILITY["2.0.x"])
    if major == 2 and minor is not None and minor >= 1:
        return list(BASYX_AAS_READABILITY[">=2.1"])
    return []


@dataclass(frozen=True)
class SmiaResolution:
    """Outcome of resolving one SMIA version to its basyx pin and AAS labels."""

    status: Literal["installed", "registry", "pypi", "unverified"]
    smia_version: str | None
    basyx_pin: str | None
    readable_aas: list[str]
    source_note: str


def resolve_smia(
    version_label: str | None,
    probe: Callable[[str], SmiaPinFact] | None,
) -> SmiaResolution:
    """Resolve a SMIA version to its basyx pin and readable AAS labels.

    Order: (1) the SMIA installed in the current environment (authoritative and
    offline), (2) the static verified table, (3) the injected PyPI probe for the
    exact version, (4) an ``unverified`` result with an actionable note. Never
    raises for a missing SMIA; a failing probe degrades to ``unverified`` with
    the probe error in the source note (offline is a visible state).
    """
    installed = _installed_smia()
    if installed is not None:
        smia_version, pin = installed
        return SmiaResolution(
            status="installed",
            smia_version=smia_version,
            basyx_pin=pin,
            readable_aas=readable_aas_for_pin(pin or ""),
            source_note="importlib.metadata (offline)",
        )

    label = (version_label or "").strip()
    if not label:
        return SmiaResolution(
            status="unverified",
            smia_version=None,
            basyx_pin=None,
            readable_aas=[],
            source_note="no installed SMIA and no version provided",
        )

    release = SMIA_RELEASES.get(label)
    if release is not None:
        return SmiaResolution(
            status="registry",
            smia_version=release.smia_version,
            basyx_pin=release.basyx_pin,
            readable_aas=readable_aas_for_pin(release.basyx_pin),
            source_note=REGISTRY_SOURCE_NOTE,
        )

    if probe is not None:
        try:
            fact = probe(label)
        except ProbeError as exc:
            return SmiaResolution(
                status="unverified",
                smia_version=label,
                basyx_pin=None,
                readable_aas=[],
                source_note=f"PyPI probe failed ({exc})",
            )
        uploaded = fact.uploaded or "upload date unknown"
        note = f"PyPI JSON API, uploaded {uploaded}"
        if fact.basyx_pin is None:
            note += ": no basyx-python-sdk requirement declared"
        return SmiaResolution(
            status="pypi",
            smia_version=fact.smia_version,
            basyx_pin=fact.basyx_pin,
            readable_aas=readable_aas_for_pin(fact.basyx_pin or ""),
            source_note=note,
        )

    return SmiaResolution(
        status="unverified",
        smia_version=label,
        basyx_pin=None,
        readable_aas=[],
        source_note="no installed SMIA, no registry entry and no PyPI probe",
    )


def _installed_smia() -> tuple[str, str | None] | None:
    """Return ``(version, basyx_pin)`` for the installed SMIA, or ``None``.

    Only the current environment is inspected (documented limitation): the CLI
    runs inside the environment whose SMIA the user wants to diagnose.
    """
    try:
        version = importlib.metadata.version(SMIA_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        return None
    try:
        requirements = importlib.metadata.requires(SMIA_DISTRIBUTION) or []
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - race only
        requirements = []
    pin: str | None = None
    for requirement in requirements:
        if requirement.lower().startswith(BASYX_DISTRIBUTION):
            pin = _pin_from_requirement(requirement)
            break
    return version, pin


def _pin_from_requirement(requirement: str) -> str | None:
    """Extract the specifier of a ``requires_dist`` basyx entry."""
    specifier = requirement.split(";", 1)[0].strip()
    specifier = _DISTRIBUTION_PREFIX_RE.sub("", specifier).strip()
    return specifier or None
