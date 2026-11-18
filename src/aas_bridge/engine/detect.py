"""AAS version detection from AASX package parts.

Only namespace *declarations* are inspected: XML root attributes in both forms
(``xmlns="..."`` and ``xmlns:aas="..."``) are parsed with a streaming Expat
parser that stops at the root element. Versioned IRIs in value positions (for
example the IEC 61360 template ``.../DataSpecificationIEC61360/3/0``) are never
mistaken for declarations. JSON parts are detect-only via a top-level
``@context`` (basyx-written JSON carries no version marker, evidence §4.6 J3).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from xml.parsers import expat

from aas_bridge.engine.aasx_package import open_package, part_format
from aas_bridge.exceptions import DetectionError
from aas_bridge.registry.versions import label_for_iri

_AAS_NAMESPACE_RE = re.compile(r"^https://admin-shell\.io/aas/3/(?P<minor>\d+)$")


@dataclass(frozen=True)
class PartDetection:
    """Detected version information for one AAS-spec part."""

    part_name: str
    format: Literal["xml", "json"]
    declared_version: str | None
    version_label: str | None


@dataclass(frozen=True)
class DetectionResult:
    """Detected version information for a whole AASX package."""

    file: str
    parts: list[PartDetection]
    consistent: bool
    version_label: str | None


class _RootElementFound(Exception):
    """Internal signal used to stop Expat after the root element."""


def detect_versions(path: Path) -> DetectionResult:
    """Detect the AAS version declared by an AASX package.

    Raises:
        DetectionError: the input is not a readable AASX package, is not
            well-formed XML/JSON, or declares conflicting AAS namespaces.
    """
    package = open_package(path)
    parts: list[PartDetection] = []
    for part in package.spec_parts:
        fmt = part_format(part)
        if fmt == "xml":
            declared = _select_declared_version(
                _xml_declaration_versions(part.data, part.name), part.name
            )
        else:
            declared = _json_declared_version(part.data, part.name)
        parts.append(
            PartDetection(
                part_name=part.name,
                format=fmt,
                declared_version=declared,
                version_label=label_for_iri(declared) if declared is not None else None,
            )
        )

    labels = {part.version_label for part in parts}
    consistent = len(labels) == 1 and None not in labels
    version_label = next(iter(labels)) if consistent else None
    return DetectionResult(
        file=str(path),
        parts=parts,
        consistent=consistent,
        version_label=version_label,
    )


def _xml_declaration_versions(data: bytes, part_name: str) -> list[str]:
    parser = expat.ParserCreate()
    versions: list[str] = []

    def _start_element(_name: str, attrs: dict[str, str]) -> None:
        for attr_name, value in attrs.items():
            if (attr_name == "xmlns" or attr_name.startswith("xmlns:")) and _AAS_NAMESPACE_RE.match(
                value
            ):
                versions.append(value)
        raise _RootElementFound

    parser.StartElementHandler = _start_element
    try:
        parser.Parse(data, True)
    except _RootElementFound:
        pass
    except expat.ExpatError as exc:
        raise DetectionError(
            f"AAS part {part_name} is not well-formed XML ({exc}). "
            "Check that the package payload was not truncated or re-encoded."
        ) from exc
    return versions


def _select_declared_version(versions: list[str], part_name: str) -> str | None:
    unique: list[str] = []
    for version in versions:
        if version not in unique:
            unique.append(version)
    if len(unique) > 1:
        raise DetectionError(
            f"AAS part {part_name} declares conflicting AAS namespaces {unique}. "
            "A package must declare one AAS version; re-export it from a single toolchain."
        )
    return unique[0] if unique else None


def _json_declared_version(data: bytes, part_name: str) -> str | None:
    try:
        document = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DetectionError(
            f"AAS JSON part {part_name} is not readable JSON ({exc}). "
            "Check that the package payload was not truncated."
        ) from exc
    if not isinstance(document, dict):
        raise DetectionError(
            f"AAS JSON part {part_name} does not contain a top-level JSON object. "
            "AAS JSON packages are objects with an optional @context entry."
        )
    context = document.get("@context")
    if context is None:
        return None
    entries = context if isinstance(context, list) else [context]
    declared: list[str] = []
    for entry in entries:
        if isinstance(entry, str) and _AAS_NAMESPACE_RE.match(entry) and entry not in declared:
            declared.append(entry)
    if len(declared) > 1:
        raise DetectionError(
            f"AAS JSON part {part_name} declares conflicting @context versions {declared}. "
            "A package must declare one AAS version."
        )
    return declared[0] if declared else None
