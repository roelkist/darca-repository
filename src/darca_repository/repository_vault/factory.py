import os
from repository_vault.interfaces import RepositoryVault
from darca_repository.repository_vault.yaml_repository_vault import YamlRepositoryVault


def get_repository_vault() -> RepositoryVault:
    """
    Factory to resolve and return the configured RepositoryVault implementation.
    """
    mode = os.getenv("DARCA_REPOSITORY_VAULT_MODE", "yaml").lower()

    if mode == "yaml":
        directory = os.getenv(
            "DARCA_REPOSITORY_VAULT_DIR",
            os.path.expanduser("~/.local/share/darca_repository/repositories"),
        )
        return YamlRepositoryVault(directory)

    if mode == "mysql":
        from repository_vault.mysql_repository_vault import MySQLRepositoryVault
        host = os.getenv("DARCA_REPOSITORY_MYSQL_HOST", "localhost")
        user = os.getenv("DARCA_REPOSITORY_MYSQL_USER", "darca_user")
        password = os.getenv("DARCA_REPOSITORY_MYSQL_PASSWORD", "darca_password")
        database = os.getenv("DARCA_REPOSITORY_MYSQL_DATABASE", "darca_repository")
        url = f"mysql+asyncmy://{user}:{password}@{host}/{database}"
        return MySQLRepositoryVault(connection_url=url)

    raise ValueError(f"Unsupported DARCA_REPOSITORY_VAULT_MODE: {mode}")
