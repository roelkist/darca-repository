# manager/factory.py

from darca_repository.manager.interfaces import RepositoryManager
from darca_repository.config import get_config


def get_repository_manager() -> RepositoryManager:
    """
    Factory for resolving the appropriate RepositoryManager implementation
    based on current configuration (yaml or mysql).
    """
    cfg = get_config()
    mode = cfg.repository_vault_mode.lower()

    if mode == "yaml":
        from darca_repository.manager.yaml_manager import YamlRepositoryManager
        return YamlRepositoryManager()

    if mode == "mysql":
        from darca_repository.manager.mysql_manager import MySQLRepositoryManager
        return MySQLRepositoryManager()

    raise ValueError(f"Unsupported repository manager mode: {mode}")
