# tests/test_registry.py
# License: MIT

import pytest
from darca_repository.registry.factory import get_repository_registry
from darca_repository.registry.yaml_registry import YamlRepositoryRegistry
from darca_repository.exceptions import RepositoryNotFoundError

def test_yaml_registry_profile_loading(repo_profile_file):
    registry = get_repository_registry()
    assert isinstance(registry, YamlRepositoryRegistry)

    profile = registry.get_profile("local-test-repo")
    assert profile.name == "local-test-repo"
    assert profile.scheme.value == "file"

    all_profiles = registry.list_profiles()
    assert any(p.name == "local-test-repo" for p in all_profiles)

    with pytest.raises(RepositoryNotFoundError):
        registry.get_profile("does-not-exist")
