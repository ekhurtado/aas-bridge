"""Unit tests for the network probes (mocked opener, fully offline)."""

from __future__ import annotations

import hashlib
import json
import urllib.error
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from aas_bridge.exceptions import ProbeError
from aas_bridge.probes import artifacts, pypi
from aas_bridge.registry.ecosystem.specs import ARTIFACT_SOURCES, OFFICIAL_SOURCE


class FakeResponse:
    """Minimal ``urlopen`` response: status, read chunks, context manager."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status
        self._offset = 0

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            chunk = self._body[self._offset :]
            self._offset = len(self._body)
            return chunk
        chunk = self._body[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


def opener_for(mapping: dict[str, bytes | Exception | FakeResponse]) -> Callable[..., Any]:
    def open_url(url: str, timeout: float | None = None) -> Any:
        try:
            response = mapping[url]
        except KeyError:  # pragma: no cover - test bug guard
            raise AssertionError(f"Unexpected URL requested: {url}") from None
        if isinstance(response, Exception):
            raise response
        if isinstance(response, bytes):
            return FakeResponse(response)
        return response

    return open_url


def pypi_payload(requires_dist: list[str] | None, uploaded: str = "2026-10-21T10:00:00Z") -> bytes:
    return json.dumps(
        {
            "info": {"version": "1.0.3", "requires_dist": requires_dist},
            "urls": [{"upload_time_iso_8601": uploaded}],
        }
    ).encode("utf-8")


def test_fetch_smia_pin_latest_parses_the_basyx_requirement() -> None:
    url = "https://pypi.org/pypi/smia/json"
    opener = opener_for(
        {url: pypi_payload(["typer>=0.29", "basyx-python-sdk~=1.2.1"], "2026-10-21T10:00:00Z")}
    )

    fact = pypi.fetch_smia_pin(opener=opener)

    assert fact.smia_version == "1.0.3"
    assert fact.basyx_pin == "~=1.2.1"
    assert fact.uploaded == "2026-10-21"


def test_fetch_smia_pin_versioned_parses_the_pin() -> None:
    url = "https://pypi.org/pypi/smia/0.2.2/json"
    opener = opener_for({url: pypi_payload(["basyx-python-sdk==1.1.0"], "2025-02-27T09:30:00Z")})

    fact = pypi.fetch_smia_pin("0.2.2", opener=opener)

    assert fact.basyx_pin == "==1.1.0"
    assert fact.uploaded == "2025-02-27"


def test_fetch_smia_pin_without_basyx_requirement() -> None:
    url = "https://pypi.org/pypi/smia/json"
    opener = opener_for({url: pypi_payload(None)})

    fact = pypi.fetch_smia_pin(opener=opener)

    assert fact.basyx_pin is None
    assert fact.uploaded == "2026-10-21"


def test_fetch_smia_pin_http_404_names_the_url() -> None:
    url = "https://pypi.org/pypi/smia/9.9.9/json"
    error = urllib.error.HTTPError(url, 404, "Not Found", None, None)
    opener = opener_for({url: error})

    with pytest.raises(ProbeError) as excinfo:
        pypi.fetch_smia_pin("9.9.9", opener=opener)

    assert url in str(excinfo.value)
    assert "404" in str(excinfo.value)


def test_fetch_smia_pin_timeout_is_probe_error() -> None:
    url = "https://pypi.org/pypi/smia/json"
    opener = opener_for({url: TimeoutError("timed out")})

    with pytest.raises(ProbeError) as excinfo:
        pypi.fetch_smia_pin(opener=opener)

    assert "offline" in str(excinfo.value)


def test_fetch_smia_pin_invalid_json_is_probe_error() -> None:
    url = "https://pypi.org/pypi/smia/json"
    opener = opener_for({url: b"<html>not json</html>"})

    with pytest.raises(ProbeError) as excinfo:
        pypi.fetch_smia_pin(opener=opener)

    assert "Invalid JSON" in str(excinfo.value)


def _releases_payload() -> bytes:
    entries = [
        ("v3.2.0", "IDTA-01001-3-2-0", "2026-07-21T10:00:00Z", False),
        ("v3.1.2", "IDTA-01001-3-1-2", "2025-11-10T10:00:00Z", False),
        ("v3.1.1", "IDTA-01001-3-1-1", "2025-08-01T10:00:00Z", False),
        ("v3.1.0", "IDTA-01001-3-1-0", "2025-05-27T10:00:00Z", False),
        (
            "IDTA-01001-3-0-1_schemasV3.0.9",
            "IDTA-01001-3-0-1_schemasV3.0.9",
            "2024-11-15T10:00:00Z",
            False,
        ),
        (
            "IDTA-01001-3-0-1_schemasV3.0.8",
            "IDTA-01001-3-0-1_schemasV3.0.8",
            "2024-07-05T10:00:00Z",
            False,
        ),
        ("V3.0.7", "V3.0.7", "2023-04-26T10:00:00Z", False),
        ("v3.0.6", "v3.0.6", "2023-04-04T10:00:00Z", False),
        ("V3.0.5RC02", "V3.0.5RC02", "2022-09-12T10:00:00Z", True),
    ]
    return json.dumps(
        [
            {
                "tag_name": tag,
                "name": name,
                "published_at": published,
                "prerelease": prerelease,
            }
            for tag, name, published, prerelease in entries
        ]
    ).encode("utf-8")


def test_fetch_official_releases_parses_labels_and_prereleases() -> None:
    opener = opener_for({OFFICIAL_SOURCE.releases_feed: _releases_payload()})

    releases = artifacts.fetch_official_releases(opener=opener)

    assert len(releases) == 9
    assert releases[0].tag == "v3.2.0"
    assert releases[0].aas_label == "3.2"
    assert releases[0].published == "2026-07-21"
    assert any(release.tag == "v3.1.2" and release.aas_label == "3.1" for release in releases)
    prereleases = [release for release in releases if release.prerelease]
    assert [release.tag for release in prereleases] == ["V3.0.5RC02"]


def test_fetch_official_releases_honours_the_limit() -> None:
    opener = opener_for({OFFICIAL_SOURCE.releases_feed: _releases_payload()})

    releases = artifacts.fetch_official_releases(limit=2, opener=opener)

    assert [release.tag for release in releases] == ["v3.2.0", "v3.1.2"]


def test_fetch_official_releases_rate_limit_is_actionable() -> None:
    error = urllib.error.HTTPError(OFFICIAL_SOURCE.releases_feed, 403, "Forbidden", None, None)
    opener = opener_for({OFFICIAL_SOURCE.releases_feed: error})

    with pytest.raises(ProbeError) as excinfo:
        artifacts.fetch_official_releases(opener=opener)

    assert "rate limit" in str(excinfo.value).lower()


def _artifact_bodies(label: str) -> dict[str, bytes]:
    version = ARTIFACT_SOURCES[label]
    bodies = {}
    for index, spec in enumerate(version.artifacts):
        url = f"{OFFICIAL_SOURCE.raw_base}/{version.tag}/{spec.path}"
        bodies[url] = f"{label}:{spec.kind}:{index}".encode() * 32
    return bodies


def test_fetch_artifacts_writes_three_files_with_sha256(tmp_path: Path) -> None:
    label = "3.1"
    bodies = _artifact_bodies(label)
    opener = opener_for(bodies)

    fetched = artifacts.fetch_artifacts(label, tmp_path, opener=opener)

    assert [entry.kind for entry in fetched] == ["xsd", "json-schema", "changelog"]
    assert all(entry.status == "fetched" for entry in fetched)
    assert all(entry.aas_label == label for entry in fetched)
    assert all(entry.tag == ARTIFACT_SOURCES[label].tag for entry in fetched)
    assert all(entry.sha256 for entry in fetched)
    assert all(entry.size and entry.size > 0 for entry in fetched)
    assert all(entry.fetched_at is not None for entry in fetched)

    for entry, spec in zip(fetched, ARTIFACT_SOURCES[label].artifacts, strict=True):
        destination = tmp_path / label / Path(spec.path).name
        assert destination.is_file()
        expected = hashlib.sha256(bodies[entry.url]).hexdigest()
        assert entry.sha256 == expected


def test_fetch_artifacts_30_line_fetches_the_two_schema_artifacts(tmp_path: Path) -> None:
    label = "3.0"
    opener = opener_for(_artifact_bodies(label))

    fetched = artifacts.fetch_artifacts(label, tmp_path, opener=opener)

    assert [entry.kind for entry in fetched] == ["xsd", "json-schema"]
    assert all(entry.status == "fetched" for entry in fetched)


def test_fetch_artifacts_is_idempotent_and_reports_cached(tmp_path: Path) -> None:
    label = "3.1"
    bodies = _artifact_bodies(label)

    first = artifacts.fetch_artifacts(label, tmp_path, opener=opener_for(bodies))
    second = artifacts.fetch_artifacts(label, tmp_path, opener=opener_for(bodies))

    assert all(entry.status == "fetched" for entry in first)
    assert all(entry.status == "cached" for entry in second)
    assert [entry.sha256 for entry in second] == [entry.sha256 for entry in first]
    assert [entry.fetched_at for entry in second] == [entry.fetched_at for entry in first]


def test_fetch_artifacts_overwrites_changed_content(tmp_path: Path) -> None:
    label = "3.0"
    bodies = _artifact_bodies(label)
    artifacts.fetch_artifacts(label, tmp_path, opener=opener_for(bodies))
    changed = {url: body + b"changed" for url, body in bodies.items()}

    fetched = artifacts.fetch_artifacts(label, tmp_path, opener=opener_for(changed))

    assert all(entry.status == "fetched" for entry in fetched)
    for entry in fetched:
        assert entry.sha256 == hashlib.sha256(changed[entry.url]).hexdigest()
        destination = tmp_path / label / Path(entry.url).name
        assert destination.read_bytes() == changed[entry.url]


class BrokenResponse:
    status = 200

    def __init__(self) -> None:
        self._calls = 0

    def read(self, size: int = -1) -> bytes:
        self._calls += 1
        if self._calls == 1:
            return b"partial"
        raise OSError("connection reset")

    def __enter__(self) -> BrokenResponse:
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


def test_fetch_artifacts_partial_download_leaves_no_destination(tmp_path: Path) -> None:
    label = "3.0"
    bodies = _artifact_bodies(label)
    broken_url = next(iter(bodies))
    mapping: dict[str, Any] = {url: body for url, body in bodies.items()}
    mapping[broken_url] = BrokenResponse()
    opener = opener_for(mapping)

    with pytest.raises(ProbeError):
        artifacts.fetch_artifacts(label, tmp_path, opener=opener)

    destination = tmp_path / label / Path(broken_url).name
    assert not destination.exists()
    assert list((tmp_path / label).glob("*.part")) == []


def test_fetch_artifacts_unknown_label_is_probe_error(tmp_path: Path) -> None:
    with pytest.raises(ProbeError) as excinfo:
        artifacts.fetch_artifacts("9.9", tmp_path)

    assert "Unknown AAS version label" in str(excinfo.value)
