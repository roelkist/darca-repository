# tests/conftest.py
# License: MIT

import pytest
import tempfile
import shutil
import os

@pytest.fixture(scope="session")
def temp_repo_dir():
    dir_path = tempfile.mkdtemp(prefix="darca_repo_test_")
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def repo_profile_file(temp_repo_dir):
    yaml_content = """name: local-test-repo
storage_url: file://{dir}/repo1
scheme: file
parameters:
  base_path: "data"
enabled: true
""".format(dir=temp_repo_dir)

    os.makedirs(os.path.join(temp_repo_dir, "profiles"), exist_ok=True)
    profile_path = os.path.join(temp_repo_dir, "profiles", "repo.yaml")
    with open(profile_path, "w") as f:
        f.write(yaml_content)

    os.environ["DARCA_REPOSITORY_MODE"] = "yaml"
    os.environ["DARCA_REPOSITORY_PROFILE_DIR"] = os.path.join(temp_repo_dir, "profiles")
    return profile_path
