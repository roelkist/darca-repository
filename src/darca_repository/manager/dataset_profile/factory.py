from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.config import get_config


def get_dataset() -> Dataset:
    """
    Factory for ObjectVault backend selection.
    """
    cfg = get_config()
    mode = cfg.object_vault_mode

    if mode == "yaml":
        from darca_repository.object_vault.yaml_object_vault import YamlObjectVault
        return YamlObjectVault(base_path=cfg.object_vault_dir)

    if mode == "mysql":
        from darca_repository.object_vault.mysql_object_vault import MySQLObjectVault
        return MySQLObjectVault()

    raise ValueError(f"Unsupported object vault mode: {mode}")
