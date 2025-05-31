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

    from darca_repository.instance import RepositoryInstance
    from darca_repository.registry.factory import get_repository_registry

    registry = get_repository_registry()
    profile = registry.get_profile("my-space")

    repo = RepositoryInstance(profile)
    client = await repo.connect()

    await client.write("hello.txt", content="Hello, Darca!")

Repository Format (YAML)
------------------------

Example YAML file (`workspace-main.yaml`):

.. code-block:: yaml

    name: workspace-main
    storage_url: file:///var/data/workspace
    scheme: file
    credentials:
      token: ${DARCA_TOKEN}
    parameters:
      cache: "false"
    tags:
      env: production
    enabled: true
    priority: 10


📚 Documentation
----------------

Visit the full documentation:

👉 https://roelkist.github.io/darca-repository/

To build locally:

.. code-block:: bash

   make docs


🧪 Testing
----------

Run all tests using:

.. code-block:: bash

   make test

Coverage and reports:

- Generates `coverage.svg` badge
- Stores HTML output in `htmlcov/`
- Fully parallel test support with `xdist`

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
