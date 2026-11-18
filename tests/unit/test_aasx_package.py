"""Tests for OPC/ZIP package reading and byte-preserving rebuilds."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest

from aas_bridge.engine.aasx_package import open_package, part_format, rebuild_package
from aas_bridge.exceptions import DetectionError, MigrationError

REPO_ROOT = Path(__file__).resolve().parents[2]

CORPUS_PARTS = {
    "aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx": [
        "/aasx/IndustrialRobot_ABB_CeDRI/IndustrialRobot_ABB_CeDRI.aas.xml"
    ],
    "aas_v3-0/SimulatedAssetHTTP_IndustrialRobot_1.aasx": [
        "/aasx/GuidedTutorialExtensionAAS/GuidedTutorialExtensionAAS.aas.xml"
    ],
    "aas_v3-0/SimulatedAssetsHTTP_Plan_1.aasx": [
        "/aasx/GuidedTutorialExtensionAAS/GuidedTutorialExtensionAAS.aas.xml"
    ],
    "aas_v3-1/HumanWorker1.aasx": ["/aasx/data.xml"],
    "aas_v3-1/LEGO_machine0.aasx": ["/aasx/data.xml"],
    "aas_v3-1/SMIA_orchestrator.aasx": ["/aasx/data.xml"],
}

_CONTENT_TYPES = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="xml" ContentType="text/xml"/>'
    b'<Default Extension="rels" '
    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    b'<Default Extension="json" ContentType="application/json"/>'
    b'<Override PartName="/aasx/aasx-origin" ContentType="text/plain"/>'
    b"</Types>"
)

_ROOT_RELS = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Type="http://admin-shell.io/aasx/relationships/aasx-origin" '
    b'Target="/aasx/aasx-origin" Id="r1"/>'
    b"</Relationships>"
)

_ORIGIN_RELS = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Type="http://admin-shell.io/aasx/relationships/aas-spec" '
    b'Target="/aasx/data.xml" Id="r1"/>'
    b"</Relationships>"
)


def _write_package(
    path: Path,
    data_parts: dict[str, bytes],
    *,
    extra_entries: dict[str, bytes] | None = None,
) -> Path:
    """Create a minimal valid AASX package for tests (no corpus writes)."""
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("[Content_Types].xml", _CONTENT_TYPES)
        package.writestr("_rels/.rels", _ROOT_RELS)
        package.writestr("aasx/aasx-origin", b"Intentionally empty")
        package.writestr("aasx/_rels/aasx-origin.rels", _ORIGIN_RELS)
        for name, data in data_parts.items():
            package.writestr(name, data)
        for name, data in (extra_entries or {}).items():
            package.writestr(name, data)
    return path


def _copy_corpus(relative: str, tmp_path: Path) -> Path:
    destination = tmp_path / Path(relative).name
    shutil.copy2(REPO_ROOT / relative, destination)
    return destination


@pytest.mark.parametrize(("relative", "expected_parts"), CORPUS_PARTS.items())
def test_open_corpus_package_inventory(
    relative: str, expected_parts: list[str], tmp_path: Path
) -> None:
    package = open_package(_copy_corpus(relative, tmp_path))

    assert package.origin_part == "/aasx/aasx-origin"
    assert [part.name for part in package.spec_parts] == expected_parts
    assert all(part_format(part) == "xml" for part in package.spec_parts)
    assert all(
        part.data.startswith(b"\xef\xbb\xbf") or part.data.startswith(b"<?xml")
        for part in package.spec_parts
    )


@pytest.mark.parametrize("relative", CORPUS_PARTS)
def test_rebuild_without_changes_preserves_every_entry(relative: str, tmp_path: Path) -> None:
    source = _copy_corpus(relative, tmp_path)
    output = tmp_path / f"{source.stem}-rebuilt.aasx"

    rebuild_package(source, output, {})

    with zipfile.ZipFile(source) as source_zip, zipfile.ZipFile(output) as output_zip:
        source_infos = source_zip.infolist()
        output_infos = output_zip.infolist()
        assert [info.filename for info in source_infos] == [info.filename for info in output_infos]
        for source_info, output_info in zip(source_infos, output_infos, strict=True):
            assert output_zip.read(output_info) == source_zip.read(source_info)
            assert output_info.date_time == source_info.date_time
            assert output_info.compress_type == source_info.compress_type


def test_rebuild_replaces_only_the_given_part(tmp_path: Path) -> None:
    source = _copy_corpus("aas_v3-1/SMIA_orchestrator.aasx", tmp_path)
    output = tmp_path / "out.aasx"
    replacement = b"<replaced/>"

    rebuild_package(source, output, {"/aasx/data.xml": replacement})

    with zipfile.ZipFile(source) as source_zip, zipfile.ZipFile(output) as output_zip:
        assert output_zip.read("aasx/data.xml") == replacement
        for name in source_zip.namelist():
            if name != "aasx/data.xml":
                assert output_zip.read(name) == source_zip.read(name)


def test_rebuild_refuses_missing_replacement_part(tmp_path: Path) -> None:
    source = _copy_corpus("aas_v3-1/SMIA_orchestrator.aasx", tmp_path)
    output = tmp_path / "out.aasx"

    with pytest.raises(MigrationError, match="missing part"):
        rebuild_package(source, output, {"/aasx/not-there.xml": b"x"})

    assert not output.exists()


def test_open_rejects_plain_file(tmp_path: Path) -> None:
    not_a_package = tmp_path / "notes.aasx"
    not_a_package.write_text("not a zip", encoding="utf-8")

    with pytest.raises(DetectionError, match="OPC/ZIP"):
        open_package(not_a_package)


def test_open_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DetectionError, match="not found"):
        open_package(tmp_path / "missing.aasx")


def test_open_rejects_zip_without_origin_relationship(tmp_path: Path) -> None:
    package_path = tmp_path / "no-origin.aasx"
    empty_relationships = (
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )
    with zipfile.ZipFile(package_path, "w") as package:
        package.writestr("[Content_Types].xml", _CONTENT_TYPES)
        package.writestr("_rels/.rels", empty_relationships)

    with pytest.raises(DetectionError, match="aasx-origin"):
        open_package(package_path)


def test_open_rejects_unsafe_entry_name(tmp_path: Path) -> None:
    package_path = tmp_path / "unsafe.aasx"
    _write_package(
        package_path,
        {"aasx/data.xml": b"<environment/>"},
        extra_entries={"../escape.txt": b"x"},
    )

    with pytest.raises(DetectionError, match="unsafe ZIP entry"):
        open_package(package_path)


def test_transformed_input_is_never_mutated(tmp_path: Path) -> None:
    source = _copy_corpus("aas_v3-0/SimulatedAssetsHTTP_Plan_1.aasx", tmp_path)
    before = hashlib.sha256(source.read_bytes()).hexdigest()

    rebuild_package(source, tmp_path / "copy.aasx", {})

    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
