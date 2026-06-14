Architecture Guide
==================

This guide provides an in-depth explanation of the **darca-repository** architecture, 
its design patterns, core components, and how they work together.

Overview
--------

``darca-repository`` is a session-aware, credential-capable repository abstraction layer 
that sits on top of ``darca-storage``. It provides a structured way to manage multiple 
storage backends with:

- **Profile-based configuration**: Store repository metadata in YAML or database
- **Credential management**: Secure handling of secrets with environment variable interpolation
- **Async-first design**: All I/O operations are asynchronous
- **Pluggable registries**: Support for multiple backend storage systems
- **Session metadata**: Propagate observability context through the storage stack

Architecture Diagram
--------------------

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                     Application Layer                       │
    │  (Your code using darca-repository)                         │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ get_repository_registry()
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   Registry Factory                          │
    │  - Selects registry backend based on environment            │
    │  - Supports: YAML, SQL, Plugin-based registries             │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ get_profile(name)
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              Repository Registry (Interface)                │
    │  - YamlRepositoryRegistry (file-based)                      │
    │  - MySQLRepositoryRegistry (database-based, planned)        │
    │  - Custom registry via entry points                         │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Repository profile
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  Repository Instance                        │
    │  - Holds repository metadata                                │
    │  - Manages credentials resolution                           │
    │  - Creates StorageClient connections                        │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ connect()
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │           StorageConnectorFactory                           │
    │  (from darca-storage)                                       │
    │  - Parses storage URL                                       │
    │  - Creates appropriate connector                            │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ StorageClient
                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    Storage Backend                          │
    │  - File system                                              │
    │  - S3                                                       │
    │  - Memory                                                   │
    │  - NFS                                                      │
    └─────────────────────────────────────────────────────────────┘


Core Components
---------------

1. Repository Model
^^^^^^^^^^^^^^^^^^^

The ``Repository`` model (defined in ``models.py``) is the central data structure:

.. code-block:: python

    class Repository(BaseModel):
        name: str                           # Unique identifier
        connection: RepositoryConnectionInfo # Connection details
        tags: Optional[Dict[str, str]]      # Metadata tags
        enabled: bool                       # Active/inactive flag
        priority: Optional[int]             # Priority for selection

**Connection Information** includes:

- ``storage_url``: The URL to the storage backend (e.g., ``file:///data``, ``s3://bucket``)
- ``scheme``: The storage type (file, s3, mem, nfs)
- ``credentials``: Dictionary of secret values (supports environment variable interpolation)
- ``parameters``: Additional connection parameters

2. Registry System
^^^^^^^^^^^^^^^^^^

The registry system is responsible for loading and managing repository profiles.

**Base Interface** (``registry/base.py``):

.. code-block:: python

    class RepositoryRegistry(ABC):
        @abstractmethod
        def get_profile(self, name: str) -> Repository:
            """Retrieve a repository by name"""
            
        @abstractmethod
        def list_profiles(self, *, enabled_only: bool, tag: Optional[str]) -> List[Repository]:
            """List all repositories with optional filtering"""
            
        @abstractmethod
        def add_profile(self, repository: Repository) -> None:
            """Add or update a repository"""
            
        @abstractmethod
        def remove_profile(self, name: str) -> None:
            """Delete a repository"""

**YAML Registry** (``registry/yaml_registry.py``):

- Loads profiles from YAML files in a directory
- One file per repository (e.g., ``workspace-main.yaml``)
- Automatically reloads on changes
- Simple file-based persistence

**Registry Factory** (``registry/factory.py``):

The factory pattern allows dynamic selection of registry backend:

.. code-block:: python

    def get_repository_registry() -> RepositoryRegistry:
        mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml")
        
        # Plugin-based loading via entry points
        for entry_point in entry_points(group="darca_repository.registries"):
            if entry_point.name == mode:
                return entry_point.load()()
        
        # Built-in backends
        if mode == "yaml":
            return YamlRepositoryRegistry(profile_dir)

3. Repository Instance
^^^^^^^^^^^^^^^^^^^^^^

``RepositoryInstance`` (in ``instance.py``) is the runtime representation of a repository:

**Key Responsibilities:**

1. **Credential Resolution**: Resolves ``${ENV_VAR}`` placeholders to actual values
2. **Session Metadata**: Builds context for observability (repository name, tags, URL)
3. **StorageClient Creation**: Uses ``StorageConnectorFactory`` to create the client
4. **Connection Management**: Maintains a single client instance per repository
5. **Error Handling**: Wraps connection errors with repository context

**Usage Flow:**

.. code-block:: python

    # 1. Get repository profile from registry
    registry = get_repository_registry()
    profile = registry.get_profile("my-repo")
    
    # 2. Create instance
    instance = RepositoryInstance(profile)
    
    # 3. Connect (idempotent)
    client = await instance.connect()
    
    # 4. Use storage client
    await client.write("file.txt", content="data")

4. Exception Hierarchy
^^^^^^^^^^^^^^^^^^^^^^

All exceptions inherit from ``RepositoryException`` (which extends ``DarcaException``):

- ``RepositoryNotFoundError``: Profile doesn't exist in registry
- ``RepositoryConnectionError``: Failed to connect to storage backend
- ``RepositoryAccessDenied``: Insufficient permissions
- ``RepositoryValidationError``: Profile validation failed

Exceptions support:

- **Error codes**: Machine-readable codes for filtering/routing
- **Metadata**: Structured context (repository name, user, etc.)
- **Cause chaining**: Original exception preserved

5. Server API (FastAPI)
^^^^^^^^^^^^^^^^^^^^^^^^

The server component provides a REST API for managing repositories:

**Endpoints:**

- ``GET /repositories/``: List all repositories
- ``GET /repositories/{name}``: Get specific repository
- ``GET /repositories/{name}/test``: Test repository connection
- ``POST /repositories/``: Add new repository
- ``DELETE /repositories/{name}``: Remove repository

**Dependency Injection:**

Uses FastAPI's dependency injection to provide the registry:

.. code-block:: python

    @router.get("/{name}", response_model=Repository)
    def get_repository(
        name: str, 
        registry: RepositoryRegistry = Depends(get_registry)
    ):
        return registry.get_profile(name)

Data Flow
---------

Connection Establishment Flow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    1. Application calls get_repository_registry()
       └─> Factory reads DARCA_REPOSITORY_MODE
       └─> Returns appropriate registry (YAML, SQL, plugin)
    
    2. Application calls registry.get_profile("name")
       └─> Registry loads profile from storage
       └─> Returns Repository model
    
    3. Application creates RepositoryInstance(profile)
       └─> Stores profile reference
    
    4. Application calls instance.connect()
       └─> Resolves credentials (${ENV_VAR} → actual values)
       └─> Builds session metadata
       └─> Calls StorageConnectorFactory.from_url()
       └─> Returns StorageClient
    
    5. Application uses client for I/O
       └─> await client.read(path)
       └─> await client.write(path, content)

Credential Resolution Flow
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    Profile contains:
    credentials:
      token: ${DARCA_TOKEN}
      api_key: direct-value-123
    
    Resolution process:
    1. Repository.get_secret("token") is called
    2. Checks if value starts with "${" and ends with "}"
    3. If yes: extracts "DARCA_TOKEN" from "${DARCA_TOKEN}"
    4. Calls os.getenv("DARCA_TOKEN")
    5. Returns environment variable value
    
    If no interpolation needed:
    1. Returns the direct value (e.g., "direct-value-123")

Design Patterns
---------------

1. **Factory Pattern**: Registry selection and storage client creation
2. **Strategy Pattern**: Different registry backends implement same interface
3. **Singleton Pattern**: Single client instance per repository instance
4. **Repository Pattern**: Abstraction over storage backends
5. **Dependency Injection**: FastAPI uses DI for registry access

Configuration
-------------

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

**DARCA_REPOSITORY_MODE**
  Registry backend to use (default: ``yaml``)
  
  - ``yaml``: File-based YAML registry
  - ``mysql``: MySQL database registry (not yet implemented)
  - Custom: Via plugin entry points

**DARCA_REPOSITORY_PROFILE_DIR**
  Directory for YAML profiles (default: ``~/.local/share/darca_repository/profiles``)

**DARCA_TOKEN** (and other credential variables)
  Used in credential interpolation (``${DARCA_TOKEN}`` in YAML)

Plugin System
^^^^^^^^^^^^^

Custom registries can be registered via entry points in ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."darca_repository.registries"]
    mybackend = "mypackage.registry:MyRegistry"

Then use with:

.. code-block:: bash

    export DARCA_REPOSITORY_MODE=mybackend

Extensibility
-------------

Adding a New Registry Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Create a class implementing ``RepositoryRegistry``
2. Implement all abstract methods
3. Register via entry points or factory
4. Configure via environment variable

Example:

.. code-block:: python

    from darca_repository.registry.base import RepositoryRegistry
    
    class PostgresRegistry(RepositoryRegistry):
        def __init__(self, connection_string: str):
            self.conn = create_connection(connection_string)
        
        def get_profile(self, name: str) -> Repository:
            # Query database
            row = self.conn.execute("SELECT * FROM repos WHERE name=?", name)
            return Repository(**row)
        
        # ... implement other methods

Performance Considerations
--------------------------

Connection Reuse
^^^^^^^^^^^^^^^^

``RepositoryInstance`` caches the ``StorageClient`` after first connection:

- Subsequent ``connect()`` calls return the same client
- No reconnection overhead for repeated access
- One instance per repository recommended

Registry Caching
^^^^^^^^^^^^^^^^

``YamlRepositoryRegistry`` loads all profiles into memory on initialization:

- Fast profile lookups (dict access)
- Call ``reload()`` to refresh from disk
- Suitable for hundreds of profiles

Async Operations
^^^^^^^^^^^^^^^^

All I/O operations are async:

- Non-blocking file/network operations
- Use ``asyncio.gather()`` for concurrent operations
- Integrates with async frameworks (FastAPI, aiohttp)

Security
--------

Credential Handling
^^^^^^^^^^^^^^^^^^^

- Credentials stored as ``SecretStr`` (Pydantic)
- Not logged or serialized by default
- Environment variable interpolation prevents hardcoding
- Secrets resolved at runtime, not stored in memory longer than needed

File Permissions
^^^^^^^^^^^^^^^^

YAML profile directory should have restricted permissions:

.. code-block:: bash

    chmod 700 ~/.local/share/darca_repository/profiles
    chmod 600 ~/.local/share/darca_repository/profiles/*.yaml

Access Control
^^^^^^^^^^^^^^

- Repository profiles can be enabled/disabled
- Tags allow filtering by environment/team
- Priority allows preference ordering

Testing
-------

The architecture supports comprehensive testing:

**Unit Tests**: Test individual components in isolation

- ``test_models.py``: Model validation and credential resolution
- ``test_exceptions.py``: Exception handling
- ``test_yaml_registry.py``: Registry operations
- ``test_instance.py``: Connection and error handling

**Integration Tests**: Test components working together

- ``test_system.py``: End-to-end flows
- ``test_registry_factory.py``: Factory behavior

**Test Utilities**:

- ``conftest.py``: Fixtures for temporary registries
- Mock storage backends for testing without real I/O

Summary
-------

The ``darca-repository`` architecture is designed for:

✅ **Flexibility**: Multiple registry backends, pluggable design
✅ **Security**: Safe credential handling with environment variables
✅ **Observability**: Session metadata propagation
✅ **Simplicity**: Clean abstractions, minimal API surface
✅ **Testability**: Components are loosely coupled and mockable
✅ **Performance**: Connection reuse, in-memory caching

The layered architecture separates concerns:

1. **Application Layer**: Your code
2. **Repository Layer**: Profile management and connection
3. **Storage Layer**: Actual I/O operations (via darca-storage)

This separation allows each layer to evolve independently while maintaining
a stable interface for applications.
