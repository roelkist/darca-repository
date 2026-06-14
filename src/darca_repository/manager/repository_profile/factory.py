from darca_repository.repository_vault.interfaces import RepositoryVault
from darca_repository.config import get_config


def get_repository_vault() -> RepositoryVault:
    """
    Factory for RepositoryVault backend selection.
    """
    cfg = get_config()
    mode = cfg.repository_vault_mode

    if mode == "yaml":
        from darca_repository.repository_vault.yaml_repository_vault import YamlRepositoryVault
        return YamlRepositoryVault(base_path=cfg.repository_vault_dir)

    if mode == "mysql":
        from darca_repository.repository_vault.mysql_repository_vault import MySQLRepositoryVault
        return MySQLRepositoryVault()

    raise ValueError(f"Unsupported repository vault mode: {mode}")
