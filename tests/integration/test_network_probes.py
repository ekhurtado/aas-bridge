"""Real network probes (opt-in only: ``python -m pytest -m network``).

These tests hit PyPI and GitHub anonymously. They are also marked
``integration`` so the declared offline suite (``-m "not integration"``) never
runs them; the full run and the explicit ``-m network`` run do. The facts
asserted here are the dated evidence recorded in
``.ai/ECOSYSTEM_COMPATIBILITY.md`` §7/§8.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aas_bridge.probes.artifacts import fetch_artifacts, fetch_official_releases
from aas_bridge.probes.pypi import fetch_smia_pin

pytestmark = [pytest.mark.network, pytest.mark.integration]


def test_pypi_reports_the_verified_smia_release() -> None:
    fact = fetch_smia_pin("1.0.3")

    assert fact.smia_version == "1.0.3"
    assert fact.basyx_pin == "~=1.2.1"
    assert fact.uploaded == "2026-10-21"


def test_official_releases_feed_lists_the_pinned_tags() -> None:
    releases = fetch_official_releases(limit=30)

    assert len(releases) >= 8
    by_tag = {release.tag: release for release in releases}
    assert "v3.1.2" in by_tag
    assert "IDTA-01001-3-0-1_schemasV3.0.9" in by_tag
    assert by_tag["v3.1.2"].aas_label == "3.1"
    assert by_tag["v3.1.2"].prerelease is False


def test_artifact_download_records_sha256_and_size(tmp_path: Path) -> None:
    fetched = fetch_artifacts("3.1", tmp_path)

    assert [entry.kind for entry in fetched] == ["xsd", "json-schema", "changelog"]
    for entry in fetched:
        assert entry.status == "fetched"
        assert entry.sha256 is not None
        assert len(entry.sha256) == 64
        assert entry.size is not None
        assert entry.size > 0
        assert entry.fetched_at is not None
        stored = tmp_path / "3.1" / Path(entry.url).name
        assert stored.is_file()
        assert hashlib.sha256(stored.read_bytes()).hexdigest() == entry.sha256
