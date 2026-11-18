"""Tests for the V3.0 -> V3.1 namespace relabel transformer."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest

from aas_bridge.engine.detect import detect_versions
from aas_bridge.engine.transformer import transform
from aas_bridge.exceptions import MigrationError
from aas_bridge.registry.versions import iri_for_label

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_NS = iri_for_label("3.1")
V30_FILES = [
    "aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx",
    "aas_v3-0/SimulatedAssetHTTP_IndustrialRobot_1.aasx",
    "aas_v3-0/SimulatedAssetsHTTP_Plan_1.aasx",
]
IEC_TEMPLATE = b"/DataSpecificationTemplates/DataSpecificationIEC61360/3/0"

_CONTENT_TYPES = b"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="text/xml"/>
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="json" ContentType="application/json"/>
<Override PartName="/aasx/aasx-origin" ContentType="text/plain"/>
</Types>"""

_ORIGIN_RELS = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Type="http://admin-shell.io/aasx/relationships/aasx-origin"
 Target="/aasx/aasx-origin" Id="r0"/>
</Relationships>"""

_SPEC_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Type="http://admin-shell.io/aasx/relationships/aas-spec"
 Target="/{part_name}" Id="r1"/>
</Relationships>"""


def _build_package(path: Path, part_name: str, data: bytes) -> Path:
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("[Content_Types].xml", _CONTENT_TYPES)
        package.writestr("_rels/.rels", _ORIGIN_RELS)
        package.writestr("aasx/aasx-origin", b"")
        package.writestr(
            "aasx/_rels/aasx-origin.rels", _SPEC_RELS.format(part_name=part_name).encode()
        )
        package.writestr(part_name, data)
    return path


def _copy_corpus(relative: str, tmp_path: Path) -> Path:
    destination = tmp_path / Path(relative).name
    shutil.copy2(REPO_ROOT / relative, destination)
    return destination


@pytest.mark.parametrize("relative", V30_FILES)
def test_transform_corpus_file(relative: str, tmp_path: Path) -> None:
    source = _copy_corpus(relative, tmp_path)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    result = transform(source, TARGET_NS, tmp_path / "out")

    assert result.output_path.name == f"{source.stem}-adapted.aasx"
    assert result.output_path.parent == tmp_path / "out"
    assert result.rule_id == "v3_0_to_v3_1/namespace-relabel"
    assert len(result.parts_touched) == 1
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha

    detection = detect_versions(result.output_path)
    assert detection.consistent is True
    assert detection.version_label == "3.1"

    touched = result.parts_touched[0].lstrip("/")
    with zipfile.ZipFile(source) as source_zip, zipfile.ZipFile(result.output_path) as out_zip:
        assert source_zip.namelist() == out_zip.namelist()
        for name in source_zip.namelist():
            if name != touched:
                assert out_zip.read(name) == source_zip.read(name)
        original = source_zip.read(touched)
        migrated = out_zip.read(touched)

    assert b'xmlns="https://admin-shell.io/aas/3/1"' in migrated
    assert b'xmlns="https://admin-shell.io/aas/3/0"' not in migrated
    assert migrated.count(IEC_TEMPLATE) == original.count(IEC_TEMPLATE) == 15
    assert migrated.startswith(b"\xef\xbb\xbf") == original.startswith(b"\xef\xbb\xbf")


def test_transform_preserves_single_quotes_and_bom(tmp_path: Path) -> None:
    source = _build_package(
        tmp_path / "quoted.aasx",
        "aasx/data.xml",
        b"\xef\xbb\xbf<environment xmlns='https://admin-shell.io/aas/3/0'/>",
    )

    result = transform(source, TARGET_NS, tmp_path)

    with zipfile.ZipFile(result.output_path) as package:
        migrated = package.read("aasx/data.xml")
    assert migrated == (b"\xef\xbb\xbf<environment xmlns='https://admin-shell.io/aas/3/1'/>")


def test_json_part_is_refused(tmp_path: Path) -> None:
    source = _build_package(
        tmp_path / "json.aasx",
        "aasx/data.json",
        b'{"@context": "https://admin-shell.io/aas/3/0"}',
    )

    with pytest.raises(MigrationError, match="is JSON") as excinfo:
        transform(source, TARGET_NS, tmp_path)

    assert "detect-only" in str(excinfo.value)
    assert "@context" in str(excinfo.value)


def test_unknown_target_namespace_is_refused(tmp_path: Path) -> None:
    source = _build_package(
        tmp_path / "data.aasx",
        "aasx/data.xml",
        b'<environment xmlns="https://example.com/unknown"/>',
    )

    with pytest.raises(MigrationError, match="Unknown target namespace"):
        transform(source, "https://example.com/v9", tmp_path)


def test_already_target_version_is_refused(tmp_path: Path) -> None:
    source = _copy_corpus("aas_v3-1/HumanWorker1.aasx", tmp_path)

    with pytest.raises(MigrationError, match="does not declare"):
        transform(source, TARGET_NS, tmp_path)


def test_output_name_uses_stem_next_to_input(tmp_path: Path) -> None:
    source = _build_package(
        tmp_path / "name.with.dots.aasx",
        "aasx/data.xml",
        b'<environment xmlns="https://admin-shell.io/aas/3/0"/>',
    )

    result = transform(source, TARGET_NS)

    assert result.output_path == tmp_path / "name.with.dots-adapted.aasx"
    assert result.output_path.exists()
