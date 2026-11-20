"""Local data directory for runtime-fetched registry artifacts (TD-004).

Fetched official artifacts are user data, never package data: they live outside
the installed package and outside the current working directory. The
``AASBRIDGE_REGISTRY_DIR`` environment variable overrides the location.

:func:`resolve_registry_dir` is pure: it never creates or writes anything. The
command layer creates the directory on demand before fetching.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Final

REGISTRY_ENV_VAR: Final[str] = "AASBRIDGE_REGISTRY_DIR"


def resolve_registry_dir() -> Path:
    """Return the registry data directory (``AASBRIDGE_REGISTRY_DIR`` wins).

    Defaults: ``%LOCALAPPDATA%/aasbridge/registry`` on Windows and
    ``~/.local/share/aasbridge/registry`` on POSIX. The path is returned even
    when it does not exist yet; the command layer creates it on demand.
    """
    override = os.environ.get(REGISTRY_ENV_VAR)
    if override:
        return Path(override)
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base / "aasbridge" / "registry"
    return Path.home() / ".local" / "share" / "aasbridge" / "registry"
