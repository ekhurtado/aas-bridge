"""Apply approved registry rules to AASX packages without mutating the input."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from aas_bridge.engine.aasx_package import (
    PackagePart,
    open_package,
    part_format,
    rebuild_package,
)
from aas_bridge.exceptions import DetectionError, MigrationError
from aas_bridge.registry.rules.v3_0_to_v3_1 import (
    RULE_ID,
    SOURCE_NAMESPACE,
    relabel_declarations,
)
from aas_bridge.registry.versions import label_for_iri

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransformResult:
    """Outcome of a package transformation."""

    output_path: Path
    rule_id: str
    parts_touched: list[str]


def transform(
    source: Path,
    target_ns: str,
    output_dir: Path | None = None,
) -> TransformResult:
    """Rewrite AAS 3.0 namespace declarations to ``target_ns``.

    The input is only ever opened for reading. The adapted package is written as
    ``<stem>-adapted.aasx`` next to the input (or inside ``output_dir``) and is
    verified part-by-part before it is returned.

    Raises:
        MigrationError: the target namespace is unknown, a JSON AAS part is
            present (detect-only scope, TD-001), an XML part does not declare the
            rule's source namespace, the rebuild would change untouched bytes, or
            no approved rule matches.
    """
    source_path = Path(source)
    target_label = label_for_iri(target_ns)
    if target_label is None:
        raise MigrationError(
            f"Unknown target namespace {target_ns!r}. "
            "Use an AAS IRI registered in aas_bridge.registry.versions."
        )
    if target_ns == SOURCE_NAMESPACE:
        raise MigrationError(
            f"Target namespace {target_ns!r} equals the source namespace; nothing to transform."
        )

    try:
        package = open_package(source_path)
    except DetectionError as exc:
        raise MigrationError(f"Cannot transform {source_path}: {exc}") from exc

    replacements: dict[str, bytes] = {}
    parts_touched: list[str] = []
    for part in package.spec_parts:
        if part_format(part) == "json":
            raise MigrationError(_json_part_message(part, source_path))
        relabeled = relabel_declarations(part.data, target_ns)
        if relabeled.declarations == 0:
            raise MigrationError(
                f"AAS part {part.name} in {source_path} does not declare "
                f"{SOURCE_NAMESPACE}. Rule {RULE_ID} only upgrades AAS 3.0 parts; "
                "verify the detected version before migrating."
            )
        replacements[part.name] = relabeled.data
        parts_touched.append(part.name)
        logger.debug("Relabelled %s declaration(s) in %s", relabeled.declarations, part.name)

    if not replacements:
        raise MigrationError(
            f"{source_path} has no XML AAS-spec part to transform. "
            "Check the package layout with 'aas-bridge check'."
        )

    destination = Path(output_dir) if output_dir is not None else source_path.parent
    output_path = destination / f"{source_path.stem}-adapted.aasx"
    if output_path.resolve() == source_path.resolve():
        raise MigrationError(
            f"Refusing to overwrite the input {source_path}. Choose another output directory."
        )

    rebuild_package(source_path, output_path, replacements)
    logger.info(
        "Wrote %s (rule %s, target %s, parts %s)",
        output_path,
        RULE_ID,
        target_label,
        parts_touched,
    )
    return TransformResult(output_path=output_path, rule_id=RULE_ID, parts_touched=parts_touched)


def _json_part_message(part: PackagePart, source_path: Path) -> str:
    return (
        f"AAS part {part.name} in {source_path} is JSON. JSON migration is out of "
        "scope in this release (detect-only, TD-001): the current evidence gate "
        "cannot prove a JSON rewrite because basyx ignores @context. Export the "
        "package as XML or wait for the JSON evidence cycle."
    )
