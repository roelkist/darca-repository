# validation.py
# License: MIT

from darca_repository.models import Repository
from darca_repository.exceptions import RepositoryValidationError
from darca_storage.factory import StorageConnectorFactory


def validate_repository_config(repo: Repository) -> None:
    """
    Perform validation on a repository config.

    - Ensures required fields are present.
    - Tries to initialize a storage connector.
    - Raises RepositoryValidationError if checks fail.
    """
    if not repo.name:
        raise RepositoryValidationError("Repository must have a name.")

    if not repo.storage_url:
        raise RepositoryValidationError(f"Repository '{repo.name}' must have a storage_url.")

    try:
        connector = StorageConnectorFactory.from_url_sync(
            repo.storage_url,
            credentials={k: v.get_secret_value() for k, v in (repo.credentials or {}).items()},
            parameters=repo.parameters
        )
        backend = connector.connect_sync()
        backend.health_check()
    except Exception as e:
        raise RepositoryValidationError(
            f"Validation failed for repository '{repo.name}': {e}",
            cause=e
        )
