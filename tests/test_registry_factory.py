# tests/test_registry_factory.py
# License: MIT

import pytest
from darca_repository.registry.factory import get_repository_registry
from darca_repository.registry.yaml_registry import YamlRepositoryRegistry

def test_default_factory(monkeypatch, tmp_path):
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    monkeypatch.delenv("DARCA_REPOSITORY_MODE", raising=False)
    monkeypatch.setenv("DARCA_REPOSITORY_PROFILE_DIR", str(profile_dir))

    registry = get_repository_registry()
    assert isinstance(registry, YamlRepositoryRegistry)

def test_yaml_factory(monkeypatch, tmp_path):
    profile_dir = tmp_path / "yaml_profiles"
    profile_dir.mkdir()
    monkeypatch.setenv("DARCA_REPOSITORY_MODE", "yaml")
    monkeypatch.setenv("DARCA_REPOSITORY_PROFILE_DIR", str(profile_dir))

    registry = get_repository_registry()
    assert isinstance(registry, YamlRepositoryRegistry)

def test_mysql_not_implemented(monkeypatch):
    monkeypatch.setenv("DARCA_REPOSITORY_MODE", "mysql")
    with pytest.raises(NotImplementedError):
        get_repository_registry()

def test_invalid_mode(monkeypatch):
    monkeypatch.setenv("DARCA_REPOSITORY_MODE", "unknown")
    with pytest.raises(ValueError):
        get_repository_registry()
