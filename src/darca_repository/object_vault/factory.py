import os
from object_vault.interfaces import ObjectVault
from darca_repository.object_vault.yaml_object_vault import YamlObjectVault


def get_object_vault() -> ObjectVault:
    """
    Factory to resolve and return the configured ObjectVault implementation.
    """
    mode = os.getenv("DARCA_OBJECT_VAULT_MODE", "yaml").lower()

    if mode == "yaml":
        directory = os.getenv(
            "DARCA_OBJECT_VAULT_DIR",
            os.path.expanduser("~/.local/share/darca_repository/objects"),
        )
        return YamlObjectVault(directory)

    if mode == "mysql":
        from object_vault.mysql_object_vault import MySQLObjectVault
        host = os.getenv("DARCA_OBJECT_MYSQL_HOST", "localhost")
        user = os.getenv("DARCA_OBJECT_MYSQL_USER", "darca_user")
        password = os.getenv("DARCA_OBJECT_MYSQL_PASSWORD", "darca_password")
        database = os.getenv("DARCA_OBJECT_MYSQL_DATABASE", "darca_objects")
        url = f"mysql+asyncmy://{user}:{password}@{host}/{database}"
        return MySQLObjectVault(connection_url=url)

    raise ValueError(f"Unsupported DARCA_OBJECT_VAULT_MODE: {mode}")
