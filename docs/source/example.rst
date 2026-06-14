Examples and Use Cases
======================

This guide provides comprehensive examples and real-world use cases for **darca-repository**.

Basic Examples
--------------

Simple File Repository
^^^^^^^^^^^^^^^^^^^^^^

Connect to a local file-based repository and perform basic operations:

.. code-block:: python

    import asyncio
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def main():
        # Get registry and profile
        registry = get_repository_registry()
        profile = registry.get_profile("my-workspace")
        
        # Create repository instance
        repo = RepositoryInstance(profile)
        
        # Connect to storage
        client = await repo.connect()
        
        # Write a file
        await client.write("reports/daily.txt", content="Sales data here")
        
        # Read the file
        content = await client.read("reports/daily.txt")
        print(f"Content: {content}")
        
        # Check if file exists
        exists = await client.exists("reports/daily.txt")
        print(f"File exists: {exists}")
        
        # List files
        files = await client.list("reports/")
        print(f"Files in reports/: {files}")
    
    asyncio.run(main())

Create Profile YAML: ``~/.local/share/darca_repository/profiles/my-workspace.yaml``

.. code-block:: yaml

    name: my-workspace
    connection:
      storage_url: file:///home/user/workspace
      scheme: file
      credentials: null
      parameters: {}
    tags:
      team: engineering
    enabled: true
    priority: 10

S3 Repository with Credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connect to an S3 bucket using credentials from environment variables:

.. code-block:: python

    import asyncio
    import os
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def main():
        # Set credentials in environment
        os.environ["AWS_ACCESS_KEY"] = "your-key"
        os.environ["AWS_SECRET_KEY"] = "your-secret"
        
        # Get repository
        registry = get_repository_registry()
        profile = registry.get_profile("s3-data")
        
        repo = RepositoryInstance(profile)
        client = await repo.connect()
        
        # Upload file to S3
        await client.write("data/metrics.json", content='{"views": 1000}')
        
        # Download from S3
        data = await client.read("data/metrics.json")
        print(data)
    
    asyncio.run(main())

S3 Profile YAML: ``s3-data.yaml``

.. code-block:: yaml

    name: s3-data
    connection:
      storage_url: s3://my-bucket/analytics
      scheme: s3
      credentials:
        access_key: ${AWS_ACCESS_KEY}
        secret_key: ${AWS_SECRET_KEY}
      parameters:
        region: us-east-1
    tags:
      env: production
      team: data
    enabled: true
    priority: 5

Test Connection Before Use
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Verify a repository is accessible before performing operations:

.. code-block:: python

    import asyncio
    from darca_repository import get_repository_registry, RepositoryInstance
    from darca_repository.exceptions import RepositoryConnectionError
    
    async def safe_connect(repo_name: str):
        registry = get_repository_registry()
        profile = registry.get_profile(repo_name)
        repo = RepositoryInstance(profile)
        
        # Test connection first
        try:
            is_available = await repo.test_connection()
            if not is_available:
                print(f"Repository {repo_name} is not available")
                return None
        except RepositoryConnectionError as e:
            print(f"Failed to connect to {repo_name}: {e}")
            return None
        
        # Connection is good, proceed
        client = await repo.connect()
        return client
    
    async def main():
        client = await safe_connect("my-workspace")
        if client:
            await client.write("test.txt", content="Success!")
    
    asyncio.run(main())

Intermediate Examples
---------------------

Multiple Repositories
^^^^^^^^^^^^^^^^^^^^^

Work with multiple repositories simultaneously:

.. code-block:: python

    import asyncio
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def sync_repositories():
        """Copy files from source to destination repository"""
        registry = get_repository_registry()
        
        # Connect to both repositories
        source_profile = registry.get_profile("source-data")
        dest_profile = registry.get_profile("backup-storage")
        
        source = RepositoryInstance(source_profile)
        dest = RepositoryInstance(dest_profile)
        
        source_client = await source.connect()
        dest_client = await dest.connect()
        
        # List files in source
        files = await source_client.list("exports/")
        
        # Copy each file
        for file_path in files:
            print(f"Copying {file_path}...")
            content = await source_client.read(file_path)
            await dest_client.write(file_path, content=content)
        
        print(f"Copied {len(files)} files")
    
    asyncio.run(sync_repositories())

Dynamic Repository Selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Select repository based on tags or priority:

.. code-block:: python

    import asyncio
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def get_best_repository(tag: str):
        """Find the highest-priority enabled repository with a specific tag"""
        registry = get_repository_registry()
        
        # Filter repositories by tag
        repos = registry.list_profiles(enabled_only=True, tag=tag)
        
        if not repos:
            raise ValueError(f"No enabled repositories with tag '{tag}'")
        
        # Sort by priority (higher is better)
        repos.sort(key=lambda r: r.priority or 0, reverse=True)
        
        # Try to connect to each in priority order
        for profile in repos:
            repo = RepositoryInstance(profile)
            try:
                if await repo.test_connection():
                    print(f"Using repository: {profile.name}")
                    return await repo.connect()
            except Exception as e:
                print(f"Skipping {profile.name}: {e}")
                continue
        
        raise RuntimeError(f"No available repositories with tag '{tag}'")
    
    async def main():
        # Get best "production" repository
        client = await get_best_repository("production")
        await client.write("data.txt", content="Important data")
    
    asyncio.run(main())

Managing Profiles Programmatically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create and manage repository profiles dynamically:

.. code-block:: python

    from darca_repository import Repository, get_repository_registry
    from darca_repository.models import RepositoryConnectionInfo, StorageScheme
    from pydantic import SecretStr
    
    def create_temp_repository(name: str, path: str):
        """Create a temporary file-based repository"""
        registry = get_repository_registry()
        
        # Build connection info
        connection = RepositoryConnectionInfo(
            storage_url=f"file://{path}",
            scheme=StorageScheme.FILE,
            credentials=None,
            parameters={}
        )
        
        # Create repository
        repo = Repository(
            name=name,
            connection=connection,
            tags={"type": "temporary"},
            enabled=True,
            priority=1
        )
        
        # Add to registry
        registry.add_profile(repo)
        print(f"Created repository: {name}")
        
        return repo
    
    def cleanup_temp_repositories():
        """Remove all temporary repositories"""
        registry = get_repository_registry()
        repos = registry.list_profiles(tag="temporary")
        
        for repo in repos:
            registry.remove_profile(repo.name)
            print(f"Removed repository: {repo.name}")
    
    # Usage
    create_temp_repository("temp-001", "/tmp/workspace")
    # ... use repository ...
    cleanup_temp_repositories()

Advanced Examples
-----------------

Custom Registry Backend
^^^^^^^^^^^^^^^^^^^^^^^

Implement a custom registry that loads from a database:

.. code-block:: python

    from typing import List, Optional
    import psycopg2
    from darca_repository.registry.base import RepositoryRegistry
    from darca_repository.models import Repository
    from darca_repository.exceptions import RepositoryNotFoundError
    
    class PostgresRegistry(RepositoryRegistry):
        """PostgreSQL-backed repository registry"""
        
        def __init__(self, connection_string: str):
            self.conn = psycopg2.connect(connection_string)
            self._ensure_table()
        
        def _ensure_table(self):
            """Create repositories table if it doesn't exist"""
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS repositories (
                        name VARCHAR(255) PRIMARY KEY,
                        profile JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                self.conn.commit()
        
        def get_profile(self, name: str) -> Repository:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT profile FROM repositories WHERE name = %s",
                    (name,)
                )
                row = cur.fetchone()
                if not row:
                    raise RepositoryNotFoundError(name)
                return Repository(**row[0])
        
        def list_profiles(
            self, *, enabled_only: bool = False, tag: Optional[str] = None
        ) -> List[Repository]:
            query = "SELECT profile FROM repositories WHERE 1=1"
            params = []
            
            if enabled_only:
                query += " AND profile->>'enabled' = 'true'"
            
            if tag:
                query += " AND profile->'tags' ? %s"
                params.append(tag)
            
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                return [Repository(**row[0]) for row in cur.fetchall()]
        
        def add_profile(self, repository: Repository) -> None:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO repositories (name, profile) 
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE SET profile = EXCLUDED.profile
                    """,
                    (repository.name, repository.model_dump(mode="json"))
                )
                self.conn.commit()
        
        def remove_profile(self, name: str) -> None:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM repositories WHERE name = %s", (name,))
                if cur.rowcount == 0:
                    raise RepositoryNotFoundError(name)
                self.conn.commit()

Register via entry points in ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."darca_repository.registries"]
    postgres = "mypackage.postgres_registry:PostgresRegistry"

Then use:

.. code-block:: bash

    export DARCA_REPOSITORY_MODE=postgres
    export POSTGRES_CONNECTION="postgresql://user:pass@localhost/repos"

Repository Health Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Monitor multiple repositories and report health status:

.. code-block:: python

    import asyncio
    from datetime import datetime
    from typing import Dict, List
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def check_repository_health(name: str) -> Dict:
        """Check health of a single repository"""
        registry = get_repository_registry()
        start_time = datetime.now()
        
        try:
            profile = registry.get_profile(name)
            repo = RepositoryInstance(profile)
            
            # Test connection
            is_available = await repo.test_connection()
            
            # Measure response time
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                "name": name,
                "status": "healthy" if is_available else "unavailable",
                "response_time": elapsed,
                "error": None
            }
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            return {
                "name": name,
                "status": "error",
                "response_time": elapsed,
                "error": str(e)
            }
    
    async def monitor_repositories(tags: List[str] = None):
        """Monitor all repositories matching tags"""
        registry = get_repository_registry()
        
        # Get all enabled repositories
        repos = registry.list_profiles(enabled_only=True)
        
        # Filter by tags if specified
        if tags:
            repos = [r for r in repos if r.tags and any(t in r.tags for t in tags)]
        
        # Check health concurrently
        tasks = [check_repository_health(r.name) for r in repos]
        results = await asyncio.gather(*tasks)
        
        # Report results
        print(f"\n=== Repository Health Report ({datetime.now()}) ===")
        for result in results:
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            print(f"{status_icon} {result['name']}: {result['status']} "
                  f"({result['response_time']:.2f}s)")
            if result["error"]:
                print(f"   Error: {result['error']}")
        
        return results
    
    # Usage
    asyncio.run(monitor_repositories(tags=["production"]))

Batch File Operations
^^^^^^^^^^^^^^^^^^^^^

Efficiently process many files using concurrent operations:

.. code-block:: python

    import asyncio
    from typing import List, Tuple
    from darca_repository import get_repository_registry, RepositoryInstance
    
    async def batch_upload(
        repo_name: str, 
        files: List[Tuple[str, str]]
    ) -> List[str]:
        """Upload multiple files concurrently
        
        Args:
            repo_name: Repository to upload to
            files: List of (path, content) tuples
        
        Returns:
            List of successfully uploaded paths
        """
        registry = get_repository_registry()
        profile = registry.get_profile(repo_name)
        repo = RepositoryInstance(profile)
        client = await repo.connect()
        
        async def upload_one(path: str, content: str) -> str:
            try:
                await client.write(path, content=content)
                return path
            except Exception as e:
                print(f"Failed to upload {path}: {e}")
                return None
        
        # Upload all files concurrently
        tasks = [upload_one(path, content) for path, content in files]
        results = await asyncio.gather(*tasks)
        
        # Filter successful uploads
        successful = [r for r in results if r is not None]
        print(f"Uploaded {len(successful)}/{len(files)} files")
        
        return successful
    
    # Usage
    async def main():
        files_to_upload = [
            ("data/file1.txt", "content 1"),
            ("data/file2.txt", "content 2"),
            ("data/file3.txt", "content 3"),
        ]
        await batch_upload("my-workspace", files_to_upload)
    
    asyncio.run(main())

Real-World Use Cases
--------------------

Use Case 1: Multi-Environment Data Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Manage data across development, staging, and production environments:

**Scenario**: ETL pipeline that processes data from different environments based on configuration.

.. code-block:: python

    import asyncio
    import os
    from darca_repository import get_repository_registry, RepositoryInstance
    
    class DataPipeline:
        def __init__(self, environment: str):
            self.environment = environment
            self.registry = get_repository_registry()
        
        async def get_input_repository(self):
            """Get input data repository for this environment"""
            repos = self.registry.list_profiles(tag=self.environment)
            input_repos = [r for r in repos if "input" in r.tags]
            
            if not input_repos:
                raise ValueError(f"No input repository for {self.environment}")
            
            profile = input_repos[0]
            repo = RepositoryInstance(profile)
            return await repo.connect()
        
        async def get_output_repository(self):
            """Get output data repository for this environment"""
            repos = self.registry.list_profiles(tag=self.environment)
            output_repos = [r for r in repos if "output" in r.tags]
            
            if not output_repos:
                raise ValueError(f"No output repository for {self.environment}")
            
            profile = output_repos[0]
            repo = RepositoryInstance(profile)
            return await repo.connect()
        
        async def process(self, input_path: str, output_path: str):
            """Process data from input to output"""
            input_client = await self.get_input_repository()
            output_client = await self.get_output_repository()
            
            # Read input
            data = await input_client.read(input_path)
            
            # Transform (example: convert to uppercase)
            processed = data.upper()
            
            # Write output
            await output_client.write(output_path, content=processed)
            
            print(f"Processed {input_path} -> {output_path}")
    
    async def main():
        env = os.getenv("ENVIRONMENT", "dev")
        pipeline = DataPipeline(env)
        await pipeline.process("raw/data.txt", "processed/data.txt")
    
    asyncio.run(main())

Profile YAML files:

``dev-input.yaml``:

.. code-block:: yaml

    name: dev-input
    connection:
      storage_url: file:///data/dev/input
      scheme: file
    tags:
      env: dev
      role: input
    enabled: true

``dev-output.yaml``:

.. code-block:: yaml

    name: dev-output
    connection:
      storage_url: file:///data/dev/output
      scheme: file
    tags:
      env: dev
      role: output
    enabled: true

Use Case 2: Backup and Disaster Recovery
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Implement automated backup across multiple storage backends:

.. code-block:: python

    import asyncio
    from datetime import datetime
    from darca_repository import get_repository_registry, RepositoryInstance
    
    class BackupManager:
        def __init__(self):
            self.registry = get_repository_registry()
        
        async def backup_repository(
            self, source_name: str, backup_name: str
        ) -> None:
            """Backup all files from source to backup repository"""
            # Connect to repositories
            source_profile = self.registry.get_profile(source_name)
            backup_profile = self.registry.get_profile(backup_name)
            
            source = RepositoryInstance(source_profile)
            backup = RepositoryInstance(backup_profile)
            
            source_client = await source.connect()
            backup_client = await backup.connect()
            
            # Create timestamped backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/{source_name}/{timestamp}/"
            
            # List all files recursively
            files = await source_client.list("", recursive=True)
            
            print(f"Backing up {len(files)} files...")
            
            # Copy files concurrently
            async def backup_file(path: str):
                content = await source_client.read(path)
                backup_path = backup_dir + path
                await backup_client.write(backup_path, content=content)
            
            await asyncio.gather(*[backup_file(f) for f in files])
            
            print(f"Backup completed: {backup_dir}")
        
        async def restore_backup(
            self, backup_name: str, target_name: str, backup_timestamp: str
        ) -> None:
            """Restore files from backup to target repository"""
            backup_profile = self.registry.get_profile(backup_name)
            target_profile = self.registry.get_profile(target_name)
            
            backup = RepositoryInstance(backup_profile)
            target = RepositoryInstance(target_profile)
            
            backup_client = await backup.connect()
            target_client = await target.connect()
            
            # Find backup directory
            backup_dir = f"backups/{target_name}/{backup_timestamp}/"
            files = await backup_client.list(backup_dir, recursive=True)
            
            print(f"Restoring {len(files)} files...")
            
            # Restore files
            async def restore_file(backup_path: str):
                content = await backup_client.read(backup_path)
                # Remove backup prefix from path
                original_path = backup_path.replace(backup_dir, "")
                await target_client.write(original_path, content=content)
            
            await asyncio.gather(*[restore_file(f) for f in files])
            
            print(f"Restore completed from {backup_dir}")
    
    # Usage
    async def main():
        manager = BackupManager()
        
        # Backup production data to S3
        await manager.backup_repository("production-data", "s3-backups")
        
        # Restore if needed
        # await manager.restore_backup("s3-backups", "production-data", "20240101_120000")
    
    asyncio.run(main())

Use Case 3: FastAPI Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Expose repository access via REST API:

.. code-block:: python

    from fastapi import FastAPI, HTTPException, Depends
    from pydantic import BaseModel
    from darca_repository import get_repository_registry, RepositoryInstance
    from darca_repository.registry.base import RepositoryRegistry
    from darca_repository.exceptions import RepositoryNotFoundError
    
    app = FastAPI(title="Data Access API")
    
    def get_registry() -> RepositoryRegistry:
        return get_repository_registry()
    
    class FileContent(BaseModel):
        content: str
    
    @app.get("/repositories/{repo_name}/files/{file_path:path}")
    async def read_file(
        repo_name: str, 
        file_path: str,
        registry: RepositoryRegistry = Depends(get_registry)
    ):
        """Read a file from a repository"""
        try:
            profile = registry.get_profile(repo_name)
            repo = RepositoryInstance(profile)
            client = await repo.connect()
            
            content = await client.read(file_path)
            return {"path": file_path, "content": content}
        except RepositoryNotFoundError:
            raise HTTPException(status_code=404, detail="Repository not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/repositories/{repo_name}/files/{file_path:path}")
    async def write_file(
        repo_name: str,
        file_path: str,
        data: FileContent,
        registry: RepositoryRegistry = Depends(get_registry)
    ):
        """Write a file to a repository"""
        try:
            profile = registry.get_profile(repo_name)
            repo = RepositoryInstance(profile)
            client = await repo.connect()
            
            await client.write(file_path, content=data.content)
            return {"path": file_path, "status": "success"}
        except RepositoryNotFoundError:
            raise HTTPException(status_code=404, detail="Repository not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/repositories/{repo_name}/health")
    async def check_health(
        repo_name: str,
        registry: RepositoryRegistry = Depends(get_registry)
    ):
        """Check if repository is accessible"""
        try:
            profile = registry.get_profile(repo_name)
            repo = RepositoryInstance(profile)
            is_healthy = await repo.test_connection()
            return {"repository": repo_name, "healthy": is_healthy}
        except Exception as e:
            return {"repository": repo_name, "healthy": False, "error": str(e)}

Use Case 4: Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Store and retrieve application configuration from repositories:

.. code-block:: python

    import asyncio
    import json
    from typing import Dict, Any
    from darca_repository import get_repository_registry, RepositoryInstance
    
    class ConfigManager:
        """Manage application configuration across environments"""
        
        def __init__(self, environment: str):
            self.environment = environment
            self.registry = get_repository_registry()
            self._cache: Dict[str, Any] = {}
        
        async def _get_config_repository(self):
            """Get the configuration repository for this environment"""
            repos = self.registry.list_profiles(tag=self.environment)
            config_repos = [r for r in repos if "config" in r.tags]
            
            if not config_repos:
                raise ValueError(f"No config repository for {self.environment}")
            
            profile = config_repos[0]
            repo = RepositoryInstance(profile)
            return await repo.connect()
        
        async def get_config(self, app_name: str) -> Dict[str, Any]:
            """Load configuration for an application"""
            cache_key = f"{self.environment}:{app_name}"
            
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            client = await self._get_config_repository()
            config_path = f"{app_name}/config.json"
            
            try:
                content = await client.read(config_path)
                config = json.loads(content)
                self._cache[cache_key] = config
                return config
            except Exception as e:
                print(f"Failed to load config for {app_name}: {e}")
                return {}
        
        async def save_config(self, app_name: str, config: Dict[str, Any]):
            """Save configuration for an application"""
            client = await self._get_config_repository()
            config_path = f"{app_name}/config.json"
            
            content = json.dumps(config, indent=2)
            await client.write(config_path, content=content)
            
            # Update cache
            cache_key = f"{self.environment}:{app_name}"
            self._cache[cache_key] = config
        
        async def list_applications(self):
            """List all applications with configuration"""
            client = await self._get_config_repository()
            files = await client.list("", recursive=False)
            
            # Extract application names from directory structure
            apps = {f.split("/")[0] for f in files if "/" in f}
            return sorted(apps)
    
    # Usage
    async def main():
        config_mgr = ConfigManager(environment="production")
        
        # Get application config
        app_config = await config_mgr.get_config("api-service")
        print(f"Database: {app_config.get('database')}")
        
        # Update config
        app_config["feature_flags"] = {"new_ui": True}
        await config_mgr.save_config("api-service", app_config)
        
        # List all apps
        apps = await config_mgr.list_applications()
        print(f"Applications: {apps}")
    
    asyncio.run(main())

Summary
-------

The examples above demonstrate:

✅ **Basic Operations**: File read/write, connection testing
✅ **Intermediate Patterns**: Multi-repository operations, dynamic selection
✅ **Advanced Techniques**: Custom registries, health monitoring, batch operations
✅ **Real-World Applications**: Data pipelines, backups, API integration, config management

Key Takeaways
^^^^^^^^^^^^^

1. **Async First**: Always use ``await`` with I/O operations
2. **Test Connections**: Use ``test_connection()`` before critical operations
3. **Error Handling**: Wrap operations in try/except for robustness
4. **Concurrent Operations**: Use ``asyncio.gather()`` for batch operations
5. **Profile Management**: Leverage tags and priority for flexible selection
6. **Credential Security**: Use environment variables for sensitive data
7. **Registry Choice**: Select appropriate backend for your scale and requirements

These patterns can be adapted to many other scenarios including:

- Log aggregation and analysis
- Machine learning dataset management
- Document storage and retrieval
- Media asset management
- Distributed caching systems
- Multi-cloud data synchronization
