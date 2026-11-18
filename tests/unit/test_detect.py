"""Tests for AAS version detection (XML declarations and JSON @context)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from aas_bridge.engine.detect import detect_versions
from aas_bridge.exceptions import DetectionError

REPO_ROOT = Path(__file__).resolve().parents[2]

_CONTENT_TYPES = b"""<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="text/xml"/>
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="json" ContentType="application/json"/>
<Override PartName="/aasx/aasx-origin" ContentType="text/plain"/>
</Types>"""

_ROOT_RELS = b"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Type="http://admin-shell.io/aasx/relationships/aasx-origin"
 Target="/aasx/aasx-origin" Id="r0"/>
</Relationships>"""

_V30 = b'<environment xmlns="https://admin-shell.io/aas/3/0"><assetAdministrationShells/></environment>'
_V31 = (
    b'<aas:environment xmlns:aas="https://admin-shell.io/aas/3/1">'
    b"<aas:assetAdministrationShells/></aas:environment>"
)
_IEC_VALUE = (
    b"<value>https://admin-shell.io/DataSpecificationTemplates/"
    b"DataSpecificationIEC61360/3/0</value>"
)


def _build_package(path: Path, parts: dict[str, bytes]) -> Path:
    relationships = "".join(
        f'<Relationship Type="http://admin-shell.io/aasx/relationships/aas-spec" '
        f'Target="/{name}" Id="r{index}"/>'
        for index, name in enumerate(parts, start=1)
    )
    origin_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{relationships}</Relationships>"
    ).encode()
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("[Content_Types].xml", _CONTENT_TYPES)
        package.writestr("_rels/.rels", _ROOT_RELS)
        package.writestr("aasx/aasx-origin", b"")
        package.writestr("aasx/_rels/aasx-origin.rels", origin_rels)
        for name, data in parts.items():
            package.writestr(name, data)
    return path


@pytest.mark.parametrize(
    ("relative", "expected_label"),
    [
        ("aas_v3-0/CeDRI_PunchingMachine_instanceA.aasx", "3.0"),
        ("aas_v3-0/SimulatedAssetHTTP_IndustrialRobot_1.aasx", "3.0"),
        ("aas_v3-0/SimulatedAssetsHTTP_Plan_1.aasx", "3.0"),
        ("aas_v3-1/HumanWorker1.aasx", "3.1"),
        ("aas_v3-1/LEGO_machine0.aasx", "3.1"),
        ("aas_v3-1/SMIA_orchestrator.aasx", "3.1"),
    ],
)
def test_corpus_detection(relative: str, expected_label: str) -> None:
    result = detect_versions(REPO_ROOT / relative)

    assert result.consistent is True
    assert result.version_label == expected_label
    assert [part.version_label for part in result.parts] == [expected_label]
    assert result.parts[0].format == "xml"
    assert result.file.endswith(Path(relative).name)


def test_default_xmlns_form_detects_30(tmp_path: Path) -> None:
    package = _build_package(tmp_path / "default.aasx", {"aasx/data.xml": _V30})

    result = detect_versions(package)

    assert result.version_label == "3.0"
    assert result.parts[0].declared_version == "https://admin-shell.io/aas/3/0"


def test_prefixed_xmlns_form_detects_31(tmp_path: Path) -> None:
    package = _build_package(tmp_path / "prefixed.aasx", {"aasx/data.xml": _V31})

    result = detect_versions(package)

    assert result.version_label == "3.1"
    assert result.parts[0].declared_version == "https://admin-shell.io/aas/3/1"


def test_iec61360_value_iri_is_not_a_declaration(tmp_path: Path) -> None:
    xml = (
        b'<environment xmlns="https://admin-shell.io/aas/3/1">'
        b"<assetAdministrationShells/>" + _IEC_VALUE + b"</environment>"
    )
    package = _build_package(tmp_path / "iec.aasx", {"aasx/data.xml": xml})

    result = detect_versions(package)

    assert result.version_label == "3.1"
    assert result.parts[0].declared_version == "https://admin-shell.io/aas/3/1"


def test_value_iri_only_is_undetectable(tmp_path: Path) -> None:
    xml = b"<environment>" + _IEC_VALUE + b"</environment>"
    package = _build_package(tmp_path / "values.aasx", {"aasx/data.xml": xml})

    result = detect_versions(package)

    assert result.parts[0].declared_version is None
    assert result.parts[0].version_label is None
    assert result.consistent is False
    assert result.version_label is None


def test_json_context_string_detects_version(tmp_path: Path) -> None:
    data = b'{"@context": "https://admin-shell.io/aas/3/0", "assetAdministrationShells": []}'
    package = _build_package(tmp_path / "json.aasx", {"aasx/data.json": data})

    result = detect_versions(package)

    assert result.parts[0].format == "json"
    assert result.version_label == "3.0"


def test_json_context_list_detects_version(tmp_path: Path) -> None:
    data = (
        b'{"@context": ["https://example.com/context", '
        b'"https://admin-shell.io/aas/3/1"], "submodels": []}'
    )
    package = _build_package(tmp_path / "json-list.aasx", {"aasx/data.json": data})

    assert detect_versions(package).version_label == "3.1"


def test_json_without_context_is_undetectable(tmp_path: Path) -> None:
    package = _build_package(
        tmp_path / "json-nomarker.aasx",
        {"aasx/data.json": b'{"assetAdministrationShells": []}'},
    )

    result = detect_versions(package)

    assert result.parts[0].declared_version is None
    assert result.version_label is None
    assert result.consistent is False


def test_different_xml_parts_are_inconsistent(tmp_path: Path) -> None:
    package = _build_package(
        tmp_path / "mixed.aasx",
        {"aasx/data.xml": _V30, "aasx/other.xml": _V31},
    )

    result = detect_versions(package)

    assert result.consistent is False
    assert result.version_label is None
    assert [part.version_label for part in result.parts] == ["3.0", "3.1"]


def test_conflicting_declarations_in_one_part_are_rejected(tmp_path: Path) -> None:
    xml = (
        b'<environment xmlns="https://admin-shell.io/aas/3/0" '
        b'xmlns:aas="https://admin-shell.io/aas/3/1"/>'
    )
    package = _build_package(tmp_path / "conflict.aasx", {"aasx/data.xml": xml})

    with pytest.raises(DetectionError, match="conflicting AAS namespaces"):
        detect_versions(package)


def test_non_aasx_zip_is_rejected(tmp_path: Path) -> None:
    package_path = tmp_path / "plain.aasx"
    with zipfile.ZipFile(package_path, "w") as package:
        package.writestr("readme.txt", b"not an AASX package")

    with pytest.raises(DetectionError):
        detect_versions(package_path)


def test_malformed_xml_is_rejected(tmp_path: Path) -> None:
    package = _build_package(tmp_path / "broken.aasx", {"aasx/data.xml": b"<environment"})

    with pytest.raises(DetectionError, match="not well-formed XML"):
        detect_versions(package)
