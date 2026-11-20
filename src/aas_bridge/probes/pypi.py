"""PyPI JSON probe for SMIA releases (stdlib ``urllib``, injectable opener).

The probe reads ``https://pypi.org/pypi/smia[/<version>]/json`` and extracts the
``basyx-python-sdk`` requirement from ``info.requires_dist``. Every failure
(HTTP error, timeout, invalid payload) raises :class:`ProbeError` naming what
failed, why and what to do next; the tool stays usable offline with the static
registry table.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from aas_bridge.exceptions import ProbeError

PYPI_PROJECT: Final[str] = "smia"
BASYX_DISTRIBUTION: Final[str] = "basyx-python-sdk"
_PYPI_BASE: Final[str] = "https://pypi.org/pypi"


@dataclass(frozen=True)
class SmiaPinFact:
    """The basyx pin declared by one SMIA release on PyPI."""

    smia_version: str
    basyx_pin: str | None
    uploaded: str | None


def fetch_smia_pin(
    version: str | None = None,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 15.0,
) -> SmiaPinFact:
    """Return the SMIA release metadata and its basyx pin (``None`` = latest).

    Raises:
        ProbeError: PyPI is unreachable, answers non-200, or returns an invalid
            payload. The message names the URL and the next action.
    """
    url = f"{_PYPI_BASE}/{PYPI_PROJECT}" + (f"/{version}" if version else "") + "/json"
    payload = _read_json(url, opener, timeout)
    info = payload.get("info")
    if not isinstance(info, dict):
        raise ProbeError(
            f"Unexpected PyPI response from {url}: no 'info' object was returned. "
            "Rerun when online; the tool works offline with the registry table."
        )
    resolved_version = info.get("version") or version
    if not isinstance(resolved_version, str) or not resolved_version:
        raise ProbeError(
            f"Unexpected PyPI response from {url}: the release version is missing. "
            "Rerun when online; the tool works offline with the registry table."
        )
    return SmiaPinFact(
        smia_version=resolved_version,
        basyx_pin=_basyx_pin(info.get("requires_dist"), url),
        uploaded=_uploaded_date(payload),
    )


def _read_json(url: str, opener: Callable[..., Any], timeout: float) -> dict[str, Any]:
    try:
        with opener(url, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status is None:
                status = response.getcode()
            body = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ProbeError(
                f"PyPI returned HTTP 404 for {url}: the requested SMIA version is not "
                "published. Check the version number or rerun when online."
            ) from exc
        raise ProbeError(
            f"PyPI returned HTTP {exc.code} for {url}. Rerun when online; the tool "
            "works offline with the registry table."
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ProbeError(
            f"Cannot reach PyPI at {url} ({reason}). Check the connection and rerun; "
            "the tool works offline with the registry table."
        ) from exc
    if status != 200:
        raise ProbeError(
            f"PyPI returned HTTP {status} for {url}. Rerun when online; the tool "
            "works offline with the registry table."
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError(
            f"Invalid JSON from PyPI at {url} ({exc}). Rerun when online; the tool "
            "works offline with the registry table."
        ) from exc
    if not isinstance(payload, dict):
        raise ProbeError(
            f"Invalid JSON from PyPI at {url}: expected an object. Rerun when online; "
            "the tool works offline with the registry table."
        )
    return payload


def _basyx_pin(requires_dist: Any, url: str) -> str | None:
    if not isinstance(requires_dist, list):
        return None
    for requirement in requires_dist:
        if not isinstance(requirement, str):
            continue
        if requirement.lower().startswith(BASYX_DISTRIBUTION):
            specifier = requirement.split(";", 1)[0].strip()
            specifier = specifier[len(BASYX_DISTRIBUTION) :].strip().strip("()").strip()
            return specifier or None
    return None


def _uploaded_date(payload: dict[str, Any]) -> str | None:
    urls = payload.get("urls")
    if not isinstance(urls, list):
        return None
    for entry in urls:
        if not isinstance(entry, dict):
            continue
        stamp = entry.get("upload_time_iso_8601") or entry.get("upload_time")
        if isinstance(stamp, str) and len(stamp) >= 10:
            return stamp[:10]
    return None
