"""Official AAS artifacts probe: GitHub Releases feed and pinned artifact fetch.

Both functions use the standard library (``urllib.request``) with an injectable
opener, so unit tests never touch the network. Failures raise
:class:`ProbeError` with the URL, the reason and the next action; the caller
converts them into per-item ``failed``/``skipped_offline`` statuses (offline is a
degraded state, not a process error -- L1-14).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal

from aas_bridge.exceptions import ProbeError
from aas_bridge.registry.ecosystem.specs import (
    ARTIFACT_SOURCES,
    OFFICIAL_SOURCE,
    parse_official_release,
)

_CHUNK_SIZE: Final[int] = 64 * 1024


@dataclass(frozen=True)
class OfficialRelease:
    """One entry of the official Releases feed."""

    tag: str
    name: str
    published: str | None
    aas_label: str | None
    prerelease: bool


@dataclass(frozen=True)
class FetchedArtifact:
    """Result of fetching (or reusing) one artifact of a pinned tag."""

    kind: str
    aas_label: str
    tag: str
    url: str
    sha256: str | None
    size: int | None
    fetched_at: str | None
    status: Literal["fetched", "cached", "failed", "skipped_offline"]


def fetch_official_releases(
    limit: int = 30,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 30.0,
) -> list[OfficialRelease]:
    """Return the newest official AAS metamodel releases (newest first).

    Raises:
        ProbeError: the GitHub API is unreachable, rate-limited, or returns an
            invalid payload.
    """
    url = OFFICIAL_SOURCE.releases_feed
    payload = _read_json(url, opener, timeout)
    if not isinstance(payload, list):
        raise ProbeError(
            f"Unexpected GitHub response from {url}: expected a release list. "
            "Rerun when online; the tool works offline with the pinned registry data."
        )
    releases: list[OfficialRelease] = []
    for item in payload[: max(limit, 0)]:
        if not isinstance(item, dict):
            continue
        tag = str(item.get("tag_name") or "")
        name = str(item.get("name") or "")
        parsed = parse_official_release(tag, name)
        published = item.get("published_at")
        published_date = (
            published[:10] if isinstance(published, str) and len(published) >= 10 else None
        )
        releases.append(
            OfficialRelease(
                tag=tag,
                name=name,
                published=published_date,
                aas_label=parsed[0] if parsed is not None else None,
                prerelease=bool(item.get("prerelease")) or (parsed[1] if parsed else False),
            )
        )
    return releases


def fetch_artifacts(
    label: str,
    dest_dir: Path,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 60.0,
) -> list[FetchedArtifact]:
    """Download the pinned artifacts of ``label`` into ``dest_dir/<label>/``.

    An existing file whose sha256 matches the downloaded bytes is reported as
    ``cached`` (idempotent); different content is atomically overwritten. Writes
    go through a temporary file in the destination directory, so a partial
    download never leaves a destination file behind.

    Raises:
        ProbeError: the label is unknown or the download fails.
    """
    version = ARTIFACT_SOURCES.get(label)
    if version is None:
        raise ProbeError(
            f"Unknown AAS version label {label!r}; known labels: "
            f"{', '.join(sorted(ARTIFACT_SOURCES))}."
        )
    label_dir = Path(dest_dir) / label
    try:
        label_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProbeError(
            f"Cannot create the registry directory {label_dir} ({exc}). Set "
            "AASBRIDGE_REGISTRY_DIR to a writable directory."
        ) from exc
    return [
        _fetch_one(spec.kind, spec.path, version.tag, label, label_dir, opener, timeout)
        for spec in version.artifacts
    ]


def _fetch_one(
    kind: str,
    path: str,
    tag: str,
    label: str,
    label_dir: Path,
    opener: Callable[..., Any],
    timeout: float,
) -> FetchedArtifact:
    url = f"{OFFICIAL_SOURCE.raw_base}/{tag}/{path}"
    destination = label_dir / Path(path).name
    temporary = _temporary_path(label_dir, destination.name)
    hasher = hashlib.sha256()
    size = 0
    try:
        with opener(url, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            if status != 200:
                raise ProbeError(
                    f"HTTP {status} while downloading {url}. Check the pinned tag and "
                    "path; rerun when online."
                )
            with temporary.open("wb") as handle:
                while True:
                    chunk = response.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)
        digest = hasher.hexdigest()
        if destination.is_file() and _sha256_file(destination) == digest:
            temporary.unlink(missing_ok=True)
            return FetchedArtifact(
                kind=kind,
                aas_label=label,
                tag=tag,
                url=url,
                sha256=digest,
                size=destination.stat().st_size,
                fetched_at=_stored_at(destination),
                status="cached",
            )
        os.replace(temporary, destination)
        return FetchedArtifact(
            kind=kind,
            aas_label=label,
            tag=tag,
            url=url,
            sha256=digest,
            size=size,
            fetched_at=_stored_at(destination),
            status="fetched",
        )
    except ProbeError:
        temporary.unlink(missing_ok=True)
        raise
    except urllib.error.HTTPError as exc:
        temporary.unlink(missing_ok=True)
        if exc.code in (403, 429):
            raise ProbeError(
                f"GitHub rate limit while downloading {url} (HTTP {exc.code}). Wait a "
                "few minutes and rerun; the tool works offline with the pinned registry data."
            ) from exc
        raise ProbeError(
            f"HTTP {exc.code} while downloading {url}. Check the pinned tag and path; "
            "rerun when online."
        ) from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        temporary.unlink(missing_ok=True)
        reason = getattr(exc, "reason", exc)
        raise ProbeError(
            f"Cannot download {url} ({reason}). Check the connection and rerun; the "
            "tool works offline with the pinned registry data."
        ) from exc


def _read_json(url: str, opener: Callable[..., Any], timeout: float) -> Any:
    try:
        with opener(url, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            body = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise ProbeError(
                f"GitHub rate limit while reading {url} (HTTP {exc.code}). Wait a few "
                "minutes and rerun; the tool works offline with the pinned registry data."
            ) from exc
        raise ProbeError(
            f"GitHub returned HTTP {exc.code} for {url}. Rerun when online; the tool "
            "works offline with the pinned registry data."
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ProbeError(
            f"Cannot reach GitHub at {url} ({reason}). Check the connection and rerun; "
            "the tool works offline with the pinned registry data."
        ) from exc
    if status != 200:
        raise ProbeError(
            f"GitHub returned HTTP {status} for {url}. Rerun when online; the tool "
            "works offline with the pinned registry data."
        )
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError(
            f"Invalid JSON from GitHub at {url} ({exc}). Rerun when online; the tool "
            "works offline with the pinned registry data."
        ) from exc


def _temporary_path(directory: Path, name: str) -> Path:
    descriptor, raw_path = tempfile.mkstemp(dir=directory, prefix=f".{name}.", suffix=".part")
    os.close(descriptor)
    return Path(raw_path)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def _stored_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
