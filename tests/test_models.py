# tests/test_models.py

import os
from pydantic import SecretStr
from darca_repository.models import Repository, StorageScheme


def test_get_secret_direct_value():
    repo = Repository(
        name="test1",
        storage_url="file:///tmp/abc",
        scheme=StorageScheme.FILE,
        credentials={"token": SecretStr("plain-secret")},
    )
    assert repo.get_secret("token") == "plain-secret"


def test_get_secret_from_env(monkeypatch):
    monkeypatch.setenv("DUMMY_KEY", "env-secret")
    repo = Repository(
        name="test2",
        storage_url="file:///tmp/xyz",
        scheme=StorageScheme.FILE,
        credentials={"token": SecretStr("${DUMMY_KEY}")},
    )
    assert repo.get_secret("token") == "env-secret"


def test_get_secret_missing_env(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    repo = Repository(
        name="test3",
        storage_url="file:///tmp/missing",
        scheme=StorageScheme.FILE,
        credentials={"token": SecretStr("${MISSING_KEY}")},
    )
    assert repo.get_secret("token") is None


def test_get_secret_none():
    repo = Repository(
        name="test4",
        storage_url="file:///tmp/nokey",
        scheme=StorageScheme.FILE,
    )
    assert repo.get_secret("token") is None
