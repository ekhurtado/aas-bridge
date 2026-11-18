"""AASX (OPC/ZIP) package I/O with byte-preserving rebuilds.

The readers are deliberately independent from basyx: the main process never
imports the SDK, so package inspection and the V3.0 -> V3.1 rewrite stay pure
``zipfile``/``pyecma376-2`` work. Validity is judged later by the evidence gate
in a subprocess.
"""

from __future__ import annotations

import logging
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pyecma376_2

from aas_bridge.exceptions import DetectionError, MigrationError

logger = logging.getLogger(__name__)

RELATIONSHIP_TYPE_AASX_ORIGIN = "http://admin-shell.io/aasx/relationships/aasx-origin"
RELATIONSHIP_TYPE_AAS_SPEC = "http://admin-shell.io/aasx/relationships/aas-spec"
RELATIONSHIP_TYPE_AAS_SPEC_SPLIT = "http://admin-shell.io/aasx/relationships/aas-spec-split"

#: Deprecated ``www.`` forms that basyx still accepts with a warning.
DEPRECATED_RELATIONSHIP_TYPE_AASX_ORIGIN = (
    "http://www.admin-shell.io/aasx/relationships/aasx-origin"
)
DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC = "http://www.admin-shell.io/aasx/relationships/aas-spec"
DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC_SPLIT = (
    "http://www.admin-shell.io/aasx/relationships/aas-spec-split"
)

AASX_ORIGIN_RELATIONSHIP_TYPES = frozenset(
    {RELATIONSHIP_TYPE_AASX_ORIGIN, DEPRECATED_RELATIONSHIP_TYPE_AASX_ORIGIN}
)
AAS_SPEC_RELATIONSHIP_TYPES = frozenset(
    {RELATIONSHIP_TYPE_AAS_SPEC, DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC}
)
AAS_SPEC_SPLIT_RELATIONSHIP_TYPES = frozenset(
    {RELATIONSHIP_TYPE_AAS_SPEC_SPLIT, DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC_SPLIT}
)

DEPRECATED_RELATIONSHIP_TYPES = frozenset(
    {
        DEPRECATED_RELATIONSHIP_TYPE_AASX_ORIGIN,
        DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC,
        DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC_SPLIT,
    }
)


@dataclass(frozen=True)
class PackagePart:
    """An AAS-spec part of an AASX package."""

    name: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class AASXPackage:
    """The readable AAS-spec content of an AASX package."""

    path: Path
    origin_part: str
    spec_parts: tuple[PackagePart, ...]


def normalize_part_name(name: str) -> str:
    """Return the absolute OPC part name (leading ``/``) for a ZIP entry name."""
    return "/" + name.lstrip("/")


def part_format(part: PackagePart) -> Literal["xml", "json"]:
    """Classify an AAS-spec part as XML or JSON from its content type and name."""
    content_type = part.content_type.lower()
    if "json" in content_type or part.name.lower().endswith(".json"):
        return "json"
    return "xml"


def open_package(path: Path | str) -> AASXPackage:
    """Open an AASX package and read its AAS-spec parts.

    Raises:
        DetectionError: the file is not an OPC/ZIP package, has no aasx-origin
            relationship, contains unsafe or duplicate entries, or has no
            aas-spec parts.
    """
    package_path = Path(path)
    if not package_path.is_file():
        raise DetectionError(
            f"Input file not found: {package_path}. Provide the path to an existing .aasx package."
        )

    try:
        reader = pyecma376_2.ZipPackageReader(package_path)
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        raise DetectionError(
            f"{package_path} is not a readable OPC/ZIP package ({exc}). "
            "Check that the file is a valid .aasx package."
        ) from exc

    try:
        _check_zip_entry_names(reader, package_path)
        origin_part = _find_origin_part(reader, package_path)
        spec_parts = _read_spec_parts(reader, origin_part, package_path)
    except DetectionError:
        raise
    except (KeyError, ValueError, OSError, zipfile.BadZipFile) as exc:
        raise DetectionError(
            f"{package_path} is not a readable AASX package ({exc}). "
            "Check that the package relationships and content types are intact."
        ) from exc
    finally:
        reader.close()

    if not spec_parts:
        raise DetectionError(
            f"{package_path} has no AAS-spec parts. "
            "Check that the package contains an AASX payload referenced from the "
            "aasx-origin relationships."
        )

    return AASXPackage(path=package_path, origin_part=origin_part, spec_parts=tuple(spec_parts))


def rebuild_package(
    source: Path | str,
    output: Path | str,
    replacements: Mapping[str, bytes],
) -> None:
    """Rebuild ``source`` into ``output`` replacing only the given parts.

    ``replacements`` keys are absolute part names (``/aasx/data.xml``). Every
    other ZIP entry is copied with its original payload and metadata. The output
    is verified before the function returns; on any mismatch it is removed and
    a :class:`MigrationError` is raised, so a partial or lossy package is never
    left behind.
    """
    source_path = Path(source)
    output_path = Path(output)
    normalized = {normalize_part_name(name): data for name, data in replacements.items()}

    try:
        with zipfile.ZipFile(source_path, "r") as source_zip:
            infos = source_zip.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise MigrationError(
                    f"{source_path} contains duplicate ZIP entries; refusing to rebuild "
                    "an ambiguous package."
                )
            missing = set(normalized) - {normalize_part_name(name) for name in names}
            if missing:
                raise MigrationError(
                    f"Cannot replace missing part(s) {sorted(missing)} in {source_path}. "
                    "The package layout changed while it was being transformed."
                )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output_path, "w") as output_zip:
                for info in infos:
                    part_name = normalize_part_name(info.filename)
                    data = normalized.get(part_name)
                    if data is None:
                        data = source_zip.read(info)
                    output_zip.writestr(_clone_zip_info(info), data)
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        output_path.unlink(missing_ok=True)
        raise MigrationError(
            f"Could not rebuild {source_path} into {output_path} ({exc}). "
            "The output was removed; the input was not modified."
        ) from exc

    try:
        _verify_rebuild(source_path, output_path, normalized)
    except MigrationError:
        output_path.unlink(missing_ok=True)
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        output_path.unlink(missing_ok=True)
        raise MigrationError(
            f"Could not verify the rebuild of {source_path} ({exc}). "
            "The output was removed; the input was not modified."
        ) from exc


def _check_zip_entry_names(reader: zipfile.ZipFile, package_path: Path) -> None:
    names = [info.filename for info in reader.infolist()]
    if len(names) != len(set(names)):
        raise DetectionError(
            f"{package_path} contains duplicate ZIP entries. "
            "Re-export the package with a single entry per part."
        )
    for name in names:
        parts = name.replace("\\", "/").split("/")
        if name.startswith("/") or ".." in parts:
            raise DetectionError(
                f"{package_path} contains an unsafe ZIP entry name {name!r}. "
                "Refusing to read a package with absolute or parent-directory entries."
            )


def _find_origin_part(reader: pyecma376_2.ZipPackageReader, package_path: Path) -> str:
    core_relationships = reader.get_related_parts_by_type("/")
    for relationship_type, targets in core_relationships.items():
        if relationship_type in AASX_ORIGIN_RELATIONSHIP_TYPES and targets:
            _warn_if_deprecated(relationship_type, package_path)
            return targets[0]
    raise DetectionError(
        f"{package_path} has no aasx-origin relationship. "
        "Check that the file is a valid AASX package (OPC root relationships)."
    )


def _read_spec_parts(
    reader: pyecma376_2.ZipPackageReader,
    origin_part: str,
    package_path: Path,
) -> list[PackagePart]:
    relationships = reader.get_related_parts_by_type(origin_part)
    spec_names: list[str] = []
    for relationship_type in (
        RELATIONSHIP_TYPE_AAS_SPEC,
        DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC,
        RELATIONSHIP_TYPE_AAS_SPEC_SPLIT,
        DEPRECATED_RELATIONSHIP_TYPE_AAS_SPEC_SPLIT,
    ):
        for target in relationships.get(relationship_type, []):
            _warn_if_deprecated(relationship_type, package_path)
            if target not in spec_names:
                spec_names.append(target)

    parts: list[PackagePart] = []
    for name in spec_names:
        try:
            content_type = reader.get_content_type(name) or "application/octet-stream"
            with reader.open_part(name) as part:
                data = part.read()
        except KeyError as exc:
            raise DetectionError(
                f"{package_path} references a missing AAS-spec part {name}. "
                "The package is inconsistent; re-export it."
            ) from exc
        parts.append(PackagePart(name=name, content_type=content_type, data=data))
    return parts


def _warn_if_deprecated(relationship_type: str, package_path: Path) -> None:
    if relationship_type in DEPRECATED_RELATIONSHIP_TYPES:
        logger.warning(
            "%s uses the deprecated relationship type %s; basyx accepts it for now.",
            package_path,
            relationship_type,
        )


def _clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    clone = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    clone.compress_type = info.compress_type
    clone.comment = info.comment
    clone.extra = info.extra
    clone.create_system = info.create_system
    clone.external_attr = info.external_attr
    clone.internal_attr = info.internal_attr
    return clone


def _verify_rebuild(
    source_path: Path,
    output_path: Path,
    replacements: Mapping[str, bytes],
) -> None:
    with (
        zipfile.ZipFile(source_path, "r") as source_zip,
        zipfile.ZipFile(output_path, "r") as output_zip,
    ):
        source_infos = source_zip.infolist()
        output_infos = output_zip.infolist()
        if [info.filename for info in source_infos] != [info.filename for info in output_infos]:
            raise MigrationError(
                f"Rebuild of {source_path} changed the ZIP entry list. "
                "The output was removed; the input was not modified."
            )
        for source_info, output_info in zip(source_infos, output_infos, strict=True):
            part_name = normalize_part_name(source_info.filename)
            expected = replacements.get(part_name)
            output_data = output_zip.read(output_info)
            if expected is not None:
                if output_data != expected:
                    raise MigrationError(
                        f"Rebuild of {source_path} wrote unexpected bytes for {part_name}. "
                        "The output was removed; the input was not modified."
                    )
                continue
            if output_data != source_zip.read(source_info):
                raise MigrationError(
                    f"Rebuild of {source_path} altered the untouched part {part_name}. "
                    "The output was removed; the input was not modified."
                )
            if (
                source_info.compress_type != output_info.compress_type
                or source_info.date_time != output_info.date_time
            ):
                raise MigrationError(
                    f"Rebuild of {source_path} altered ZIP metadata for {part_name}. "
                    "The output was removed; the input was not modified."
                )
