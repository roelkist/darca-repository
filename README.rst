darca-repository
================

A session-aware, credential-capable repository abstraction for structured storage backends.

`darca-repository` enables secure, pluggable resolution of storage spaces into active clients.
It builds on `darca-storage` and provides a registry-driven mechanism to manage logical repositories
with rich metadata, credential handling, and async file operations.

|Build Status| |Deploy Status| |CodeCov| |Formatting| |License| |PyPi Version| |Docs|

.. |Build Status| image:: https://github.com/roelkist/darca-repository/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/roelkist/darca-repository/actions
.. |Deploy Status| image:: https://github.com/roelkist/darca-repository/actions/workflows/cd.yml/badge.svg
   :target: https://github.com/roelkist/darca-repository/actions
.. |Codecov| image:: https://codecov.io/gh/roelkist/darca-repository/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/roelkist/darca-repository
   :alt: Codecov
.. |Formatting| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black code style
.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
.. |PyPi Version| image:: https://img.shields.io/pypi/v/darca-repository
   :target: https://pypi.org/project/darca-repository/
   :alt: PyPi
.. |Docs| image:: https://img.shields.io/github/deployments/roelkist/darca-repository/github-pages
   :target: https://roelkist.github.io/darca-repository/
   :alt: GitHub Pages

Features
--------

- ✅ Async-first storage repository resolution
- 🔐 Credential injection via secrets or environment variables
- 🔄 Session metadata propagation for observability
- 🔌 Pluggable registry backends (YAML, SQL-ready)
- 🔎 Clean interface for probing, connecting, and verifying access

Requirements
------------

- Python >= 3.9
- darca-storage
- pydantic
- PyYAML (if using YAML-based registries)

📦 Installation
---------------

.. code-block:: bash

   pip install darca-repository

Or using Poetry:

.. code-block:: bash

   poetry add darca-repository

Quick Usage
-----------

.. code-block:: python

    import asyncio
    from darca_repository.instance import RepositoryInstance
    from darca_repository.registry.factory import get_repository_registry

    async def main():
        # Get registry and retrieve a repository profile
        registry = get_repository_registry()
        profile = registry.get_profile("my-space")

        # Create repository instance and connect
        repo = RepositoryInstance(profile)
        client = await repo.connect()

        # Perform file operations
        await client.write("hello.txt", content="Hello, Darca!")
        content = await client.read("hello.txt")
        print(content)

    asyncio.run(main())

Repository Format (YAML)
------------------------

Repository profiles are defined in YAML files stored in ``~/.local/share/darca_repository/profiles/``

Example YAML file (``workspace-main.yaml``):

.. code-block:: yaml

    name: workspace-main
    connection:
      storage_url: file:///var/data/workspace
      scheme: file
      credentials:
        token: ${DARCA_TOKEN}
      parameters:
        cache: "false"
    tags:
      env: production
      team: engineering
    enabled: true
    priority: 10

**Key Components:**

- ``name``: Unique identifier for the repository
- ``connection.storage_url``: URL to the storage backend
- ``connection.scheme``: Storage type (file, s3, mem, nfs)
- ``connection.credentials``: Secrets (supports ``${ENV_VAR}`` interpolation)
- ``tags``: Metadata for filtering and organization
- ``enabled``: Whether the repository is active
- ``priority``: Preference order (higher = preferred)


⚙️ Configuration
----------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

**DARCA_REPOSITORY_MODE**
  Registry backend to use (default: ``yaml``)

  - ``yaml``: File-based YAML profiles
  - ``mysql``: MySQL database (planned)
  - Custom: Via plugin entry points

**DARCA_REPOSITORY_PROFILE_DIR**
  Directory containing YAML profiles (default: ``~/.local/share/darca_repository/profiles``)

**Credential Variables**
  Any environment variable can be referenced in profiles using ``${VAR_NAME}``

Example:

.. code-block:: bash

   export DARCA_REPOSITORY_MODE=yaml
   export DARCA_REPOSITORY_PROFILE_DIR=/etc/darca/profiles
   export AWS_ACCESS_KEY=your-key
   export AWS_SECRET_KEY=your-secret

🎯 Use Cases
------------

**darca-repository** is perfect for:

✅ **Multi-environment data pipelines**: Seamlessly switch between dev, staging, and production storage
✅ **Backup and disaster recovery**: Manage multiple backup destinations with failover support
✅ **Configuration management**: Store and retrieve application configs across environments
✅ **Data lake access**: Provide unified access to diverse storage backends (S3, file systems, etc.)
✅ **Microservices data layer**: Centralized repository management for distributed systems
✅ **CI/CD artifact storage**: Manage build artifacts across different storage systems
✅ **Machine learning datasets**: Organize and access training data from various sources

📚 Documentation
----------------

Visit the full documentation:

👉 https://roelkist.github.io/darca-repository/

**Documentation Sections:**

- 📖 **Usage Guide**: Getting started and basic operations
- 🏗️ **Architecture**: Detailed design and components
- 💡 **Examples**: Comprehensive use cases and patterns
- 🔧 **Development**: Contributing and extending the library
- 📋 **API Reference**: Complete API documentation

To build locally:

.. code-block:: bash

   make docs


🔥 Advanced Examples
--------------------

Multiple Repositories
~~~~~~~~~~~~~~~~~~~~~

Work with multiple storage backends simultaneously:

.. code-block:: python

    async def sync_data():
        registry = get_repository_registry()
        
        # Connect to source and destination
        source = RepositoryInstance(registry.get_profile("prod-data"))
        backup = RepositoryInstance(registry.get_profile("s3-backup"))
        
        source_client = await source.connect()
        backup_client = await backup.connect()
        
        # Copy files
        files = await source_client.list("exports/")
        for file in files:
            content = await source_client.read(file)
            await backup_client.write(file, content=content)

Repository Selection by Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamically select repositories based on metadata:

.. code-block:: python

    async def get_production_repository():
        registry = get_repository_registry()
        
        # Get all enabled repositories with 'production' tag
        repos = registry.list_profiles(enabled_only=True, tag="production")
        
        # Sort by priority and select the best one
        repos.sort(key=lambda r: r.priority or 0, reverse=True)
        
        for profile in repos:
            repo = RepositoryInstance(profile)
            if await repo.test_connection():
                return await repo.connect()

FastAPI Integration
~~~~~~~~~~~~~~~~~~~

Expose repository access via REST API:

.. code-block:: python

    from fastapi import FastAPI, Depends
    from darca_repository import get_repository_registry
    from darca_repository.server.dependencies import get_registry
    
    app = FastAPI()
    
    @app.get("/files/{repo}/{path:path}")
    async def read_file(repo: str, path: str, 
                        registry = Depends(get_registry)):
        profile = registry.get_profile(repo)
        instance = RepositoryInstance(profile)
        client = await instance.connect()
        return await client.read(path)

🧪 Testing
----------

Run all tests using:

.. code-block:: bash

   make test

Coverage and reports:

- Generates ``coverage.svg`` badge
- Stores HTML output in ``htmlcov/``
- Fully parallel test support with ``xdist``
- 33 tests covering all components

Run specific tests:

.. code-block:: bash

   poetry run pytest tests/test_instance.py -v
   poetry run pytest -k "test_connection" -v

🤝 Contributing
---------------

We welcome all contributions!

- Create a new **branch** from `main`
- Use PRs to submit changes
- You can also open feature requests or issues using our GitHub templates

See `CONTRIBUTING.rst` for detailed guidelines.

📄 License
----------

This project is licensed under the MIT License.
See `LICENSE <https://github.com/roelkist/darca-repository/blob/main/LICENSE>`_ for details.
