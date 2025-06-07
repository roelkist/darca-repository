# tests/test_yaml_registry.py
# License: MIT

import pytest
import yaml

from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.registry.yaml_registry import YamlRepositoryRegistry


@pytest.fixture
def sample_registry_dir(tmp_path):
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()

    repo_path = profile_dir / "demo.yaml"
    yaml_content = {
        "name": "demo",
        "connection": {
            "storage_url": "file:///data/demo",
            "scheme": "file",
            "tags": {"tier": "test"},
            "parameters": {}
        },
        "enabled": True,
        "priority": None
    }

    with open(repo_path, "w") as f:
        yaml.dump(yaml_content, f)

    return profile_dir


def test_load_profiles(sample_registry_dir):
    registry = YamlRepositoryRegistry(str(sample_registry_dir))
    profiles = registry.list_profiles()

    assert len(profiles) == 1
    assert profiles[0].name == "demo"
    assert profiles[0].connection.scheme.value == "file"


def test_get_existing_profile(sample_registry_dir):
    registry = YamlRepositoryRegistry(str(sample_registry_dir))
    profile = registry.get_profile("demo")
    assert profile.name == "demo"
    assert profile.connection.storage_url.startswith("file://")


def test_get_missing_profile(sample_registry_dir):
    registry = YamlRepositoryRegistry(str(sample_registry_dir))
    with pytest.raises(RepositoryNotFoundError):
        registry.get_profile("nonexistent")


def test_invalid_directory():
    with pytest.raises(FileNotFoundError):
        YamlRepositoryRegistry("/nonexistent/path/to/profiles")
