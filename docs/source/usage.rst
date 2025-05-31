Usage Guide
===========

This guide walks through how to use `darca-repository` to resolve and interact with storage repositories
via the `StorageClient` abstraction.

----

Repository Resolution
---------------------

Start by retrieving a repository profile from the registry:

.. code-block:: python

    from darca_repository.registry.factory import get_repository_registry

    registry = get_repository_registry()
    profile = registry.get_profile("workspace-main")

----

Connect and Use a Repository
----------------------------

Wrap the profile in a `RepositoryInstance` and connect to its storage:

.. code-block:: python

    from darca_repository.instance import RepositoryInstance

    repo = RepositoryInstance(profile)
    client = await repo.connect()  # returns a StorageClient

Now you can read/write files using the familiar async interface:

.. code-block:: python

    await client.write("data/report.txt", content="Hello Darca!")
    content = await client.read("data/report.txt")
    print(content)

----

Verify Access
-------------

Use `test_connection()` to check if the repository root is reachable and accessible:

.. code-block:: python

    success = await repo.test_connection()
    if not success:
        raise RuntimeError("Repository is unavailable.")

----

Credential Injection
--------------------

You can define credentials in your YAML profile using environment variables:

.. code-block:: yaml

    credentials:
      token: ${DARCA_ACCESS_TOKEN}

At runtime, `Repository.get_secret("token")` will resolve `${DARCA_ACCESS_TOKEN}` from the environment:

.. code-block:: python

    token = profile.get_secret("token")
    assert token == os.getenv("DARCA_ACCESS_TOKEN")

These credentials are automatically injected into the connector and client.

----

Repository Profile Example
--------------------------

.. code-block:: yaml

    name: workspace-main
    storage_url: file:///data/workspace
    scheme: file
    credentials:
      token: ${DARCA_TOKEN}
    parameters:
      cache: "false"
    tags:
      env: dev
    enabled: true
    priority: 5

----

Next Steps
----------

- See :doc:`api` for a full reference of modules and classes.
- Explore advanced backends (e.g. cloud connectors) via future plugins.

