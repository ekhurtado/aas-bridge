"""Unit tests for the registry data directory resolution (pure, offline)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aas_bridge.registry import data_dir


def test_environment_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "custom-registry"
    monkeypatch.setenv(data_dir.REGISTRY_ENV_VAR, str(target))
    monkeypatch.setattr(sys, "platform", "win32")

    assert data_dir.resolve_registry_dir() == target


def test_windows_default_uses_local_app_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(data_dir.REGISTRY_ENV_VAR, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert data_dir.resolve_registry_dir() == tmp_path / "aasbridge" / "registry"


def test_windows_default_falls_back_to_the_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(data_dir.REGISTRY_ENV_VAR, raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected = tmp_path / "AppData" / "Local" / "aasbridge" / "registry"
    assert data_dir.resolve_registry_dir() == expected


def test_posix_default_uses_the_xdg_data_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(data_dir.REGISTRY_ENV_VAR, raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    expected = tmp_path / ".local" / "share" / "aasbridge" / "registry"
    assert data_dir.resolve_registry_dir() == expected


def test_resolution_is_pure_and_the_command_layer_creates_on_demand(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "nested" / "registry"
    monkeypatch.setenv(data_dir.REGISTRY_ENV_VAR, str(target))

    resolved = data_dir.resolve_registry_dir()

    assert resolved == target
    assert not target.exists(), "resolve_registry_dir must not create directories"
    resolved.mkdir(parents=True, exist_ok=True)
    assert target.is_dir()
