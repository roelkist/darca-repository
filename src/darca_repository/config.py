import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


class DarcaRepositoryConfig:
    """
    Central configuration for repository components.
    """

    # Common MySQL connection attributes
    mysql_host: str
    mysql_user: str
    mysql_password: str
    mysql_database: str

    # Vault modes
    repository_vault_mode: str
    object_vault_mode: str
    registry_mode: str

    # Base paths
    repository_vault_dir: Path
    object_vault_dir: Path
    registry_profile_dir: Path

    def __init__(self):
        # DB connection parts
        self.mysql_host = os.getenv("DARCA_REPOSITORY_MYSQL_HOST", "localhost")
        self.mysql_user = os.getenv("DARCA_REPOSITORY_MYSQL_USER", "darca_user")
        self.mysql_password = os.getenv("DARCA_REPOSITORY_MYSQL_PASSWORD", "darca_password")
        self.mysql_database = os.getenv("DARCA_REPOSITORY_MYSQL_DATABASE", "darca_database")

        # Backend modes
        self.repository_vault_mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()
        self.object_vault_mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()
        self.registry_mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()

        # File/YAML base paths
        self.repository_vault_dir = Path(
            os.getenv("DARCA_REPOSITORY_VAULT_DIR", "~/.local/share/darca_repository/repositories")
        ).expanduser().resolve()

        self.object_vault_dir = Path(
            os.getenv("DARCA_OBJECT_VAULT_DIR", "~/.local/share/darca_repository/objects")
        ).expanduser().resolve()

        self.registry_profile_dir = Path(
            os.getenv("DARCA_REPOSITORY_PROFILE_DIR", "~/.local/share/darca_repository/profiles")
        ).expanduser().resolve()


@lru_cache
def get_config() -> DarcaRepositoryConfig:
    return DarcaRepositoryConfig()
