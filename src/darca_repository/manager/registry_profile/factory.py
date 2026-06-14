# registry/factory.py

from darca_repository.registry.interfaces import Registry
from darca_repository.config import get_config


def get_repository_registry() -> Registry:
    """
    Factory for Registry backend selection (YAML or MySQL).
    """
    cfg = get_config()
    mode = cfg.registry_mode

    if mode == "yaml":
        from darca_repository.registry.yaml_registry import YamlRegistry
        return YamlRegistry(base_path=cfg.registry_profile_dir)

    if mode == "mysql":
        from darca_repository.registry.mysql_registry import MySQLRegistry
        return MySQLRegistry()

    raise ValueError(f"Unsupported registry mode: {mode}")
