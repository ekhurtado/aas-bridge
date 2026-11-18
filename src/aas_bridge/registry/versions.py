"""Canonical AAS version identifiers and their basyx dialects.

The values are evidence-backed by ``.ai/ECOSYSTEM_COMPATIBILITY.md`` §1 and §4:
basyx-python-sdk 2.0.x implements AAS 3.0 only, while 2.1+ implements AAS 3.1.
"""

from __future__ import annotations

from typing import Final

AAS_VERSION_IRIS: Final[dict[str, str]] = {
    "3.0": "https://admin-shell.io/aas/3/0",
    "3.1": "https://admin-shell.io/aas/3/1",
}

DIALECT_MAP: Final[dict[str, str]] = {
    "3.0": "basyx-python-sdk==2.0.1",
    "3.1": "basyx-python-sdk~=2.2",
}

#: Version label this Phase 1 release migrates AAS 3.0 packages to.
TARGET_VERSION_LABEL: Final[str] = "3.1"


def iri_for_label(label: str) -> str:
    """Return the AAS namespace IRI for a version label (``"3.0"``, ``"3.1"``)."""
    try:
        return AAS_VERSION_IRIS[label]
    except KeyError as exc:
        raise ValueError(
            f"Unknown AAS version label {label!r}; known labels: {sorted(AAS_VERSION_IRIS)}"
        ) from exc


def label_for_iri(iri: str) -> str | None:
    """Return the version label declaring ``iri``, or ``None`` if it is unknown."""
    for label, known_iri in AAS_VERSION_IRIS.items():
        if known_iri == iri:
            return label
    return None
