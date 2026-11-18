"""Auto rule: relabel AAS namespace declarations from AAS 3.0 to AAS 3.1.

The transformation is intentionally declarative and string-level: only XML
namespace declaration attributes whose value is the AAS 3.0 environment IRI are
rewritten. Versioned external IRIs in value positions (for example the IEC 61360
data-specification template ``.../DataSpecificationIEC61360/3/0``) are never
touched. Proven lossless on the real corpus by `.ai/ECOSYSTEM_COMPATIBILITY.md`
§4.3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

RULE_ID = "v3_0_to_v3_1/namespace-relabel"
RULE_KIND = "auto"
SOURCE_VERSION_LABEL = "3.0"
SOURCE_NAMESPACE = "https://admin-shell.io/aas/3/0"
TARGET_VERSION_LABEL = "3.1"

_DECLARATION_PATTERN = re.compile(
    rb"(xmlns(?::[A-Za-z_][A-Za-z0-9_.-]*)?\s*=\s*)([\"'])"
    + re.escape(SOURCE_NAMESPACE.encode("utf-8"))
    + rb"\2"
)


@dataclass(frozen=True)
class RelabelResult:
    """Result of rewriting the AAS namespace declarations of one XML part."""

    data: bytes
    declarations: int


def relabel_declarations(data: bytes, target_namespace: str) -> RelabelResult:
    """Replace every AAS 3.0 namespace declaration with ``target_namespace``.

    Both forms are supported (default ``xmlns="..."`` and prefixed
    ``xmlns:aas="..."``); the original quoting style, BOM and every other byte
    are preserved.
    """
    target_bytes = target_namespace.encode("utf-8")
    declarations = 0

    def _replace(match: re.Match[bytes]) -> bytes:
        nonlocal declarations
        declarations += 1
        quote = match.group(2)
        return match.group(1) + quote + target_bytes + quote

    return RelabelResult(data=_DECLARATION_PATTERN.sub(_replace, data), declarations=declarations)
