Development Guide
=================

This comprehensive guide explains how to set up a development environment, contribute to **darca-repository**, 
and extend its functionality.

Getting Started
---------------

Prerequisites
^^^^^^^^^^^^^

**Required Software:**

- Python 3.12 or higher
- Git
- Make (for build automation)

**Recommended Tools:**

- Poetry (for dependency management)
- Docker (for testing with different backends)
- VS Code or PyCharm (with Python extension)

Initial Setup
^^^^^^^^^^^^^

1. **Clone the Repository**

.. code-block:: bash

    git clone https://github.com/roelkist/darca-repository.git
    cd darca-repository

2. **Install Dependencies**

.. code-block:: bash

    make install

This command will:

- Create a virtual environment in ``/tmp/darca-repository-venv``
- Install Poetry inside the virtual environment
- Install all project dependencies (including dev and docs)
- Configure pre-commit hooks

3. **Verify Installation**

.. code-block:: bash

    make test

This runs the full test suite and should show all tests passing.

Project Structure
-----------------

Understanding the Layout
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    darca-repository/
    ├── src/darca_repository/       # Main source code
    │   ├── __init__.py             # Public API exports
    │   ├── __version__.py          # Version information
    │   ├── models.py               # Data models (Repository, etc.)
    │   ├── instance.py             # RepositoryInstance class
    │   ├── exceptions.py           # Custom exceptions
    │   ├── main.py                 # FastAPI server entry point
    │   ├── registry/               # Registry implementations
    │   │   ├── __init__.py
    │   │   ├── base.py             # Abstract registry interface
    │   │   ├── factory.py          # Registry factory
    │   │   ├── yaml_registry.py    # YAML-based registry
    │   │   └── mysql_registry.py   # MySQL registry (stub)
    │   └── server/                 # FastAPI server components
    │       ├── api.py              # REST API endpoints
    │       ├── service.py          # Business logic
    │       └── dependencies.py     # FastAPI dependencies
    ├── tests/                      # Test suite
    │   ├── conftest.py             # Pytest fixtures
    │   ├── test_models.py          # Model tests
    │   ├── test_instance.py        # Instance tests
    │   ├── test_exceptions.py      # Exception tests
    │   ├── test_registry_factory.py # Factory tests
    │   ├── test_yaml_registry.py   # Registry tests
    │   ├── test_system.py          # Integration tests
    │   └── system/                 # System test resources
    │       └── profiles/           # Test YAML profiles
    ├── docs/                       # Documentation
    │   ├── source/                 # Sphinx source files
    │   │   ├── conf.py             # Sphinx configuration
    │   │   ├── index.rst           # Documentation home
    │   │   ├── usage.rst           # Usage guide
    │   │   ├── api.rst             # API reference
    │   │   ├── architecture.rst    # Architecture guide
    │   │   ├── examples.rst        # Examples and use cases
    │   │   └── development.rst     # This file
    │   └── build/                  # Generated documentation
    ├── pyproject.toml              # Project metadata and dependencies
    ├── Makefile                    # Build automation
    ├── README.rst                  # Project README
    ├── CONTRIBUTING.rst            # Contribution guidelines
    ├── LICENSE                     # MIT license
    └── .pre-commit-config.yaml     # Pre-commit hook configuration

Development Workflow
--------------------

Creating a Feature Branch
^^^^^^^^^^^^^^^^^^^^^^^^^

Always work in a feature branch:

.. code-block:: bash

    git checkout -b feature/my-new-feature
    # or
    git checkout -b fix/bug-description

Making Changes
^^^^^^^^^^^^^^

1. **Write Code**: Implement your feature or fix
2. **Format Code**: Run formatter before committing

   .. code-block:: bash

       make format

3. **Run Tests**: Ensure all tests pass

   .. code-block:: bash

       make test

4. **Run Linters**: Check code quality

   .. code-block:: bash

       make precommit

5. **Build Docs**: Verify documentation builds

   .. code-block:: bash

       make docs

Running Everything
^^^^^^^^^^^^^^^^^^

To run all checks in one command:

.. code-block:: bash

    make check

This runs: install → format → precommit → test → docs

Committing Changes
^^^^^^^^^^^^^^^^^^

The project uses pre-commit hooks to enforce quality standards:

.. code-block:: bash

    git add .
    git commit -m "Add feature: description"

Pre-commit will automatically:

- Format code with Black and isort
- Check for trailing whitespace
- Validate YAML files
- Run linting checks

If checks fail, fix the issues and commit again.

Testing
-------

Running Tests
^^^^^^^^^^^^^

**Run All Tests:**

.. code-block:: bash

    make test

**Run Specific Test File:**

.. code-block:: bash

    poetry run pytest tests/test_models.py -v

**Run Specific Test Function:**

.. code-block:: bash

    poetry run pytest tests/test_models.py::test_get_secret_direct_value -v

**Run Tests in Parallel:**

.. code-block:: bash

    poetry run pytest -n auto

Test Structure
^^^^^^^^^^^^^^

The test suite uses **pytest** with **pytest-asyncio** for async testing.

**Test Categories:**

1. **Unit Tests** (``test_*.py``): Test individual components
2. **Integration Tests** (``test_system.py``): Test component interactions
3. **System Tests** (``tests/system/``): Test with real file systems

**Test Fixtures** (``conftest.py``):

.. code-block:: python

    @pytest.fixture
    def temp_profile_dir(tmp_path):
        """Provides a temporary directory for YAML profiles"""
        profile_dir = tmp_path / "profiles"
        profile_dir.mkdir()
        return profile_dir
    
    @pytest.fixture
    def sample_repository():
        """Provides a sample Repository instance"""
        return Repository(
            name="test-repo",
            connection=RepositoryConnectionInfo(
                storage_url="file:///tmp/test",
                scheme=StorageScheme.FILE
            )
        )

Writing Tests
^^^^^^^^^^^^^

**Basic Test Example:**

.. code-block:: python

    import pytest
    from darca_repository.models import Repository, RepositoryConnectionInfo
    from darca_repository.exceptions import RepositoryValidationError
    
    def test_repository_name_validation():
        """Test that repository names must be valid identifiers"""
        with pytest.raises(RepositoryValidationError):
            Repository(
                name="invalid name",  # Spaces not allowed
                connection=RepositoryConnectionInfo(
                    storage_url="file:///tmp",
                    scheme="file"
                )
            )

**Async Test Example:**

.. code-block:: python

    import pytest
    from darca_repository.instance import RepositoryInstance
    
    @pytest.mark.asyncio
    async def test_connect_to_repository(sample_repository):
        """Test connecting to a repository"""
        instance = RepositoryInstance(sample_repository)
        client = await instance.connect()
        
        assert client is not None
        assert instance.client == client

**Parameterized Test Example:**

.. code-block:: python

    import pytest
    from darca_repository.models import StorageScheme
    
    @pytest.mark.parametrize("scheme,expected", [
        (StorageScheme.FILE, "file"),
        (StorageScheme.S3, "s3"),
        (StorageScheme.MEMORY, "mem"),
    ])
    def test_storage_scheme_values(scheme, expected):
        """Test storage scheme enum values"""
        assert scheme.value == expected

Coverage Requirements
^^^^^^^^^^^^^^^^^^^^^

The project aims for **100% test coverage**.

**View Coverage Report:**

.. code-block:: bash

    make test
    # Open htmlcov/index.html in browser

**Check Coverage for Specific File:**

.. code-block:: bash

    poetry run pytest --cov=src/darca_repository/models.py tests/

Code Style and Quality
----------------------

Code Formatting
^^^^^^^^^^^^^^^

The project uses:

- **Black**: Code formatter (line length: 79)
- **isort**: Import sorting

**Auto-format Code:**

.. code-block:: bash

    make format

**Manual Commands:**

.. code-block:: bash

    poetry run black -l79 src/ tests/
    poetry run isort -l79 --profile black src/ tests/

Linting
^^^^^^^

The project uses:

- **Flake8**: Style guide enforcement
- **Bandit**: Security issue detection
- **Mypy**: Static type checking

**Run Linters:**

.. code-block:: bash

    make precommit

Type Hints
^^^^^^^^^^

All functions should have type hints:

.. code-block:: python

    # Good
    def get_profile(self, name: str) -> Repository:
        """Retrieve a repository profile by name"""
        return self._profiles[name]
    
    # Bad
    def get_profile(self, name):
        return self._profiles[name]

**Check Type Hints:**

.. code-block:: bash

    poetry run mypy src/

Docstrings
^^^^^^^^^^

Use Google-style docstrings:

.. code-block:: python

    def connect(self) -> StorageClient:
        """
        Establishes connection to the storage backend.
        
        Returns:
            StorageClient: Connected client instance.
        
        Raises:
            RepositoryConnectionError: If connection fails.
        
        Examples:
            >>> repo = RepositoryInstance(profile)
            >>> client = await repo.connect()
        """
        pass

Documentation
-------------

Building Documentation
^^^^^^^^^^^^^^^^^^^^^^

**Build HTML Documentation:**

.. code-block:: bash

    make docs

Output is in ``docs/build/html/index.html``

**Watch for Changes (during development):**

.. code-block:: bash

    poetry run sphinx-autobuild docs/source docs/build/html

Then open http://localhost:8000

Documentation Structure
^^^^^^^^^^^^^^^^^^^^^^^

- ``index.rst``: Home page with overview
- ``usage.rst``: User guide and quick start
- ``api.rst``: API reference (auto-generated)
- ``architecture.rst``: Architecture and design
- ``examples.rst``: Examples and use cases
- ``development.rst``: This file

Adding New Documentation
^^^^^^^^^^^^^^^^^^^^^^^^

1. **Create RST File** in ``docs/source/``
2. **Add to Table of Contents** in ``index.rst``

.. code-block:: rst

    .. toctree::
       :maxdepth: 2
       
       usage
       architecture
       examples
       development
       my-new-guide

3. **Build and Preview**

.. code-block:: bash

    make docs
    open docs/build/html/index.html

Documentation Best Practices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

✅ **DO:**

- Use code examples liberally
- Include both simple and complex examples
- Cross-reference related sections with ``:doc:`usage```
- Use appropriate directives (``.. code-block::``, ``.. note::``)
- Keep line length reasonable (around 80-100 characters)

❌ **DON'T:**

- Assume prior knowledge
- Use jargon without explanation
- Forget to update when code changes
- Leave broken cross-references

Adding Features
---------------

Adding a New Registry Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Step 1: Create Registry Class**

Create ``src/darca_repository/registry/mybackend_registry.py``:

.. code-block:: python

    from typing import List, Optional
    from darca_repository.registry.base import RepositoryRegistry
    from darca_repository.models import Repository
    from darca_repository.exceptions import RepositoryNotFoundError
    
    class MyBackendRegistry(RepositoryRegistry):
        """Custom registry implementation"""
        
        def __init__(self, connection_string: str):
            self.connection = self._connect(connection_string)
        
        def get_profile(self, name: str) -> Repository:
            # Implementation
            pass
        
        def list_profiles(
            self, *, enabled_only: bool = False, tag: Optional[str] = None
        ) -> List[Repository]:
            # Implementation
            pass
        
        def add_profile(self, repository: Repository) -> None:
            # Implementation
            pass
        
        def remove_profile(self, name: str) -> None:
            # Implementation
            pass

**Step 2: Register in Factory**

Update ``src/darca_repository/registry/factory.py``:

.. code-block:: python

    def get_repository_registry() -> RepositoryRegistry:
        mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()
        
        # ... existing code ...
        
        if mode == "mybackend":
            connection = os.getenv("MYBACKEND_CONNECTION")
            from darca_repository.registry.mybackend_registry import MyBackendRegistry
            return MyBackendRegistry(connection)

**Step 3: Write Tests**

Create ``tests/test_mybackend_registry.py``:

.. code-block:: python

    import pytest
    from darca_repository.registry.mybackend_registry import MyBackendRegistry
    
    def test_get_profile():
        registry = MyBackendRegistry("test://connection")
        # Test implementation

**Step 4: Document**

Add to ``docs/source/api.rst``:

.. code-block:: rst

    MyBackend Registry
    ------------------
    
    .. automodule:: darca_repository.registry.mybackend_registry
       :members:

Adding a New Storage Scheme
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Step 1: Update Enum**

In ``src/darca_repository/models.py``:

.. code-block:: python

    class StorageScheme(str, Enum):
        FILE = "file"
        S3 = "s3"
        MEMORY = "mem"
        NFS = "nfs"
        SFTP = "sftp"  # New scheme

**Step 2: Implement in darca-storage**

The actual storage connector is in ``darca-storage`` package. 
You'll need to:

1. Add connector to darca-storage
2. Register in ``StorageConnectorFactory``
3. Test with darca-repository

**Step 3: Document**

Add example to ``docs/source/examples.rst``

Adding a New Exception
^^^^^^^^^^^^^^^^^^^^^^

**Step 1: Define Exception**

In ``src/darca_repository/exceptions.py``:

.. code-block:: python

    class RepositoryQuotaExceeded(RepositoryException):
        """Raised when repository storage quota is exceeded"""
        
        def __init__(self, name: str, quota: int, usage: int):
            super().__init__(
                message=f"Repository '{name}' quota exceeded: {usage}/{quota} bytes",
                error_code="REPOSITORY_QUOTA_EXCEEDED",
                metadata={
                    "repository": name,
                    "quota": quota,
                    "usage": usage
                }
            )

**Step 2: Write Tests**

In ``tests/test_exceptions.py``:

.. code-block:: python

    def test_repository_quota_exceeded():
        exc = RepositoryQuotaExceeded("test", quota=1000, usage=1500)
        assert exc.error_code == "REPOSITORY_QUOTA_EXCEEDED"
        assert exc.metadata["quota"] == 1000

**Step 3: Use in Code**

.. code-block:: python

    if storage_usage > quota:
        raise RepositoryQuotaExceeded(repo_name, quota, storage_usage)

Debugging
---------

Using Python Debugger
^^^^^^^^^^^^^^^^^^^^^

**Add Breakpoint:**

.. code-block:: python

    import pdb; pdb.set_trace()
    # Or in Python 3.7+
    breakpoint()

**Run Tests with Debugger:**

.. code-block:: bash

    poetry run pytest tests/test_instance.py::test_connect -s

Debugging Async Code
^^^^^^^^^^^^^^^^^^^^

Use ``pytest-asyncio`` with ``-s`` flag:

.. code-block:: bash

    poetry run pytest tests/ -s --log-cli-level=DEBUG

Logging
^^^^^^^

Add logging to debug issues:

.. code-block:: python

    import logging
    
    logger = logging.getLogger(__name__)
    
    def my_function():
        logger.debug("Debug info")
        logger.info("Informational message")
        logger.warning("Warning message")
        logger.error("Error message")

Enable logging in tests:

.. code-block:: python

    import logging
    logging.basicConfig(level=logging.DEBUG)

Performance Profiling
^^^^^^^^^^^^^^^^^^^^^

**Profile Code:**

.. code-block:: bash

    poetry run python -m cProfile -o profile.stats my_script.py

**Analyze Results:**

.. code-block:: python

    import pstats
    stats = pstats.Stats('profile.stats')
    stats.sort_stats('cumulative')
    stats.print_stats(20)

Common Development Tasks
------------------------

Running the Server
^^^^^^^^^^^^^^^^^^

**Development Mode:**

.. code-block:: bash

    poetry run uvicorn darca_repository.main:app --reload

Access at http://localhost:8000

**View API Documentation:**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Adding Dependencies
^^^^^^^^^^^^^^^^^^^

**Production Dependency:**

.. code-block:: bash

    make add-prod-deps deps="requests aiofiles"

**Development Dependency:**

.. code-block:: bash

    make add-deps group=dev deps="pytest-mock"

**Documentation Dependency:**

.. code-block:: bash

    make add-deps group=docs deps="sphinx-copybutton"

Updating Dependencies
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    poetry update
    poetry lock
    git add poetry.lock pyproject.toml
    git commit -m "Update dependencies"

Creating a Release
^^^^^^^^^^^^^^^^^^

1. **Update Version** in ``src/darca_repository/__version__.py``
2. **Update CHANGELOG** (if exists)
3. **Commit Changes**

   .. code-block:: bash

       git add .
       git commit -m "Release version 1.0.0"
       git tag v1.0.0
       git push && git push --tags

4. **Build Package**

   .. code-block:: bash

       poetry build

5. **Publish to PyPI**

   .. code-block:: bash

       poetry publish

Continuous Integration
----------------------

The project uses GitHub Actions for CI/CD:

Workflows
^^^^^^^^^

**CI Workflow** (``.github/workflows/ci.yml``):

- Runs on every push and PR
- Executes: linting, type checking, tests, coverage
- Builds documentation

**CD Workflow** (``.github/workflows/cd.yml``):

- Runs on tags (releases)
- Publishes to PyPI
- Deploys documentation to GitHub Pages

Local CI Simulation
^^^^^^^^^^^^^^^^^^^^

Run the same checks as CI locally:

.. code-block:: bash

    make ci

This runs: install → precommit → test → docs

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Poetry Not Found:**

.. code-block:: bash

    # Install poetry globally
    pip install poetry
    # Or use pipx
    pipx install poetry

**Tests Failing:**

.. code-block:: bash

    # Clean and reinstall
    make clean
    make install
    make test

**Import Errors:**

.. code-block:: bash

    # Ensure in poetry shell
    poetry shell
    # Or prefix with poetry run
    poetry run pytest tests/

**Pre-commit Hooks Failing:**

.. code-block:: bash

    # Update hooks
    poetry run pre-commit autoupdate
    # Run manually
    poetry run pre-commit run --all-files

Getting Help
^^^^^^^^^^^^

- **GitHub Issues**: https://github.com/roelkist/darca-repository/issues
- **Discussions**: https://github.com/roelkist/darca-repository/discussions
- **Email**: roel.kist@gmail.com

Best Practices
--------------

Code Quality
^^^^^^^^^^^^

✅ **DO:**

- Write tests for new features
- Keep functions small and focused
- Use type hints everywhere
- Handle errors gracefully
- Log important events
- Document complex logic

❌ **DON'T:**

- Commit untested code
- Ignore linter warnings
- Use bare ``except:`` clauses
- Hard-code credentials
- Duplicate code
- Skip documentation

Git Workflow
^^^^^^^^^^^^

✅ **DO:**

- Write clear commit messages
- Create feature branches
- Keep commits atomic
- Rebase on main before PR
- Respond to review feedback

❌ **DON'T:**

- Commit directly to main
- Push broken code
- Ignore CI failures
- Force push to shared branches

Security
^^^^^^^^

✅ **DO:**

- Use environment variables for secrets
- Validate all inputs
- Handle exceptions properly
- Keep dependencies updated
- Run security scans (Bandit)

❌ **DON'T:**

- Commit secrets or credentials
- Trust user input blindly
- Expose sensitive error messages
- Use deprecated libraries

Contributing
------------

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

See ``CONTRIBUTING.rst`` for detailed guidelines.

Resources
---------

**Project Links:**

- Repository: https://github.com/roelkist/darca-repository
- Documentation: https://roelkist.github.io/darca-repository/
- PyPI: https://pypi.org/project/darca-repository/
- Issues: https://github.com/roelkist/darca-repository/issues

**Related Projects:**

- darca-storage: Storage abstraction layer
- darca-exception: Exception framework

**Learning Resources:**

- Python Async: https://docs.python.org/3/library/asyncio.html
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/
- Pytest: https://docs.pytest.org/
- Sphinx: https://www.sphinx-doc.org/

Summary
-------

This development guide covered:

✅ **Setup**: Environment configuration and installation
✅ **Structure**: Project layout and organization
✅ **Workflow**: Development process and best practices
✅ **Testing**: Writing and running tests
✅ **Quality**: Code style and linting
✅ **Documentation**: Building and writing docs
✅ **Features**: Adding new functionality
✅ **Debugging**: Troubleshooting techniques
✅ **CI/CD**: Continuous integration and deployment

You're now ready to contribute to **darca-repository**! 🚀

For questions or help, open an issue or discussion on GitHub.
