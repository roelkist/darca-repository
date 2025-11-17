# Darca Repository - Complete Module Guide

## 📖 Table of Contents

1. [Overview](#overview)
2. [What is darca-repository?](#what-is-darca-repository)
3. [Core Concepts](#core-concepts)
4. [Architecture](#architecture)
5. [Installation & Setup](#installation--setup)
6. [Basic Usage](#basic-usage)
7. [Advanced Features](#advanced-features)
8. [Use Cases](#use-cases)
9. [API Reference](#api-reference)
10. [Development](#development)
11. [Extending the Module](#extending-the-module)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)
14. [Resources](#resources)

## Overview

**darca-repository** is a Python library that provides a session-aware, credential-capable repository abstraction for structured storage backends. It enables secure, pluggable resolution of storage spaces into active clients with rich metadata, credential handling, and async file operations.

### Key Features

- ✅ **Async-first**: Built on Python's asyncio for non-blocking operations
- 🔐 **Secure credentials**: Environment variable interpolation prevents hardcoding secrets
- 🔄 **Session metadata**: Propagate observability context through the storage stack
- 🔌 **Pluggable backends**: Support for YAML, SQL, and custom registry implementations
- 🔎 **Connection testing**: Probe and verify storage access before operations
- 🏷️ **Tagging system**: Organize repositories by environment, team, or purpose
- ⚡ **High performance**: Connection reuse and concurrent operations

## What is darca-repository?

Think of **darca-repository** as a configuration-driven abstraction layer that sits between your application and various storage backends. Instead of hardcoding storage URLs and credentials in your application, you define "repository profiles" that describe how to connect to storage, and the library handles the rest.

### The Problem It Solves

**Without darca-repository:**
```python
# Hardcoded, insecure, inflexible
client = S3Client(
    bucket="my-bucket",
    access_key="AKIAIOSFODNN7EXAMPLE",  # ⚠️ Hardcoded secret!
    secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # ⚠️ Hardcoded secret!
)

# Different code for different environments
if env == "production":
    client = S3Client(...)
elif env == "staging":
    client = FileClient(...)
```

**With darca-repository:**
```python
# Configuration-driven, secure, flexible
registry = get_repository_registry()
profile = registry.get_profile("data-storage")  # Loads from config
repo = RepositoryInstance(profile)
client = await repo.connect()  # Credentials from environment

# Same code for all environments!
await client.write("data.txt", content="Hello!")
```

### Key Benefits

1. **Separation of Concerns**: Application code doesn't know about storage implementation details
2. **Security**: Credentials stored in environment variables, not in code
3. **Flexibility**: Switch storage backends without code changes
4. **Observability**: Session metadata tracks operations across the stack
5. **Testability**: Easy to mock and test with in-memory storage

## Core Concepts

### 1. Repository Profile

A **repository profile** is a configuration that describes how to connect to a storage backend. It includes:

- **Name**: Unique identifier
- **Connection Info**: URL, scheme, credentials, parameters
- **Tags**: Metadata for organization and filtering
- **Status**: Enabled/disabled flag
- **Priority**: Preference ordering for selection

Example YAML profile:
```yaml
name: production-data
connection:
  storage_url: s3://my-bucket/data
  scheme: s3
  credentials:
    access_key: ${AWS_ACCESS_KEY}
    secret_key: ${AWS_SECRET_KEY}
  parameters:
    region: us-east-1
tags:
  env: production
  team: data-engineering
enabled: true
priority: 10
```

### 2. Registry

A **registry** is the storage mechanism for repository profiles. It provides:

- Loading profiles from storage (YAML files, database, etc.)
- Listing and filtering profiles
- Adding and removing profiles dynamically

Built-in registries:
- **YamlRepositoryRegistry**: Loads profiles from YAML files in a directory
- **Custom registries**: Implement your own via the plugin system

### 3. Repository Instance

A **repository instance** is the runtime representation of a profile. It:

- Holds reference to the profile
- Resolves credentials from environment variables
- Creates and caches the storage client
- Provides connection testing capabilities

### 4. Storage Client

The **storage client** (from `darca-storage`) performs actual I/O operations:

- Read/write files
- List directories
- Check file existence
- Delete files

The client is abstracted so you use the same API regardless of backend (file, S3, etc.).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────┐
│           Your Application                  │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│      Registry Factory                       │
│  (Selects backend based on env)             │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│      Repository Registry                    │
│  (Loads profiles from storage)              │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│      Repository Instance                    │
│  (Resolves credentials, creates client)     │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│      Storage Client                         │
│  (Performs I/O operations)                  │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│      Storage Backend                        │
│  (File system, S3, Memory, etc.)            │
└─────────────────────────────────────────────┘
```

### Component Interactions

1. **Application** requests a repository from the **Registry Factory**
2. **Registry Factory** selects appropriate **Registry** (YAML, SQL, etc.)
3. **Registry** loads and returns **Repository Profile**
4. **Application** creates **Repository Instance** with profile
5. **Repository Instance** resolves credentials and creates **Storage Client**
6. **Storage Client** performs operations on **Storage Backend**

### Data Flow

```
Profile (YAML) → Registry → Repository Instance → Storage Client → Backend
                    ↓              ↓                    ↓
               Credentials    Session Metadata    I/O Operations
```

## Installation & Setup

### Install from PyPI

```bash
pip install darca-repository
```

Or with Poetry:
```bash
poetry add darca-repository
```

### Configure Environment

Set environment variables for registry configuration:

```bash
# Registry mode (default: yaml)
export DARCA_REPOSITORY_MODE=yaml

# Profile directory (default: ~/.local/share/darca_repository/profiles)
export DARCA_REPOSITORY_PROFILE_DIR=/etc/darca/profiles

# Credentials (referenced in profiles)
export AWS_ACCESS_KEY=your-access-key
export AWS_SECRET_KEY=your-secret-key
```

### Create Profile Directory

```bash
mkdir -p ~/.local/share/darca_repository/profiles
```

### Create Your First Profile

Create `~/.local/share/darca_repository/profiles/my-workspace.yaml`:

```yaml
name: my-workspace
connection:
  storage_url: file:///home/user/workspace
  scheme: file
  credentials: null
  parameters: {}
tags:
  env: development
enabled: true
priority: 5
```

## Basic Usage

### Simple File Operations

```python
import asyncio
from darca_repository import get_repository_registry, RepositoryInstance

async def main():
    # Get registry
    registry = get_repository_registry()
    
    # Get repository profile
    profile = registry.get_profile("my-workspace")
    
    # Create instance and connect
    repo = RepositoryInstance(profile)
    client = await repo.connect()
    
    # Write a file
    await client.write("hello.txt", content="Hello, World!")
    
    # Read the file
    content = await client.read("hello.txt")
    print(f"Content: {content}")
    
    # List files
    files = await client.list(".")
    print(f"Files: {files}")
    
    # Check existence
    exists = await client.exists("hello.txt")
    print(f"File exists: {exists}")

asyncio.run(main())
```

### Test Connection Before Use

```python
async def safe_connect():
    registry = get_repository_registry()
    profile = registry.get_profile("my-workspace")
    repo = RepositoryInstance(profile)
    
    # Test connection first
    if await repo.test_connection():
        print("Repository is accessible")
        return await repo.connect()
    else:
        print("Repository is not accessible")
        return None
```

### List All Repositories

```python
def list_all_repos():
    registry = get_repository_registry()
    
    # List all enabled repositories
    repos = registry.list_profiles(enabled_only=True)
    
    for repo in repos:
        print(f"Name: {repo.name}")
        print(f"  URL: {repo.connection.storage_url}")
        print(f"  Tags: {repo.tags}")
        print(f"  Enabled: {repo.enabled}")
        print()
```

### Filter by Tag

```python
def get_production_repos():
    registry = get_repository_registry()
    
    # Get only production repositories
    repos = registry.list_profiles(enabled_only=True, tag="production")
    
    return repos
```

## Advanced Features

### Dynamic Repository Selection

Select repository based on priority and availability:

```python
async def get_best_repository(tag: str):
    """Find highest-priority available repository with tag"""
    registry = get_repository_registry()
    repos = registry.list_profiles(enabled_only=True, tag=tag)
    
    # Sort by priority (higher is better)
    repos.sort(key=lambda r: r.priority or 0, reverse=True)
    
    # Try each in order
    for profile in repos:
        repo = RepositoryInstance(profile)
        try:
            if await repo.test_connection():
                return await repo.connect()
        except Exception as e:
            print(f"Skipping {profile.name}: {e}")
            continue
    
    raise RuntimeError(f"No available repositories with tag '{tag}'")
```

### Multi-Repository Operations

Work with multiple repositories simultaneously:

```python
async def sync_repositories(source_name: str, dest_name: str):
    """Copy files from source to destination"""
    registry = get_repository_registry()
    
    # Connect to both
    source_profile = registry.get_profile(source_name)
    dest_profile = registry.get_profile(dest_name)
    
    source = RepositoryInstance(source_profile)
    dest = RepositoryInstance(dest_profile)
    
    source_client = await source.connect()
    dest_client = await dest.connect()
    
    # List and copy files
    files = await source_client.list("", recursive=True)
    
    for file_path in files:
        content = await source_client.read(file_path)
        await dest_client.write(file_path, content=content)
        print(f"Copied: {file_path}")
```

### Batch Operations

Process multiple files concurrently:

```python
async def batch_upload(repo_name: str, files: list[tuple[str, str]]):
    """Upload multiple files concurrently"""
    registry = get_repository_registry()
    profile = registry.get_profile(repo_name)
    repo = RepositoryInstance(profile)
    client = await repo.connect()
    
    async def upload_one(path: str, content: str):
        await client.write(path, content=content)
        print(f"Uploaded: {path}")
    
    # Upload all concurrently
    await asyncio.gather(*[upload_one(p, c) for p, c in files])
```

### Programmatic Profile Management

Create and manage profiles dynamically:

```python
from darca_repository import Repository
from darca_repository.models import RepositoryConnectionInfo, StorageScheme

def create_temp_repository(name: str, path: str):
    """Create a temporary repository"""
    registry = get_repository_registry()
    
    connection = RepositoryConnectionInfo(
        storage_url=f"file://{path}",
        scheme=StorageScheme.FILE,
        credentials=None,
        parameters={}
    )
    
    repo = Repository(
        name=name,
        connection=connection,
        tags={"type": "temporary"},
        enabled=True,
        priority=1
    )
    
    registry.add_profile(repo)
    return repo

def cleanup_temp_repositories():
    """Remove all temporary repositories"""
    registry = get_repository_registry()
    repos = registry.list_profiles(tag="temporary")
    
    for repo in repos:
        registry.remove_profile(repo.name)
```

## Use Cases

### 1. Multi-Environment Data Pipeline

**Scenario**: ETL pipeline that processes data across dev, staging, and production.

```python
class DataPipeline:
    def __init__(self, environment: str):
        self.environment = environment
        self.registry = get_repository_registry()
    
    async def get_input_repo(self):
        repos = self.registry.list_profiles(tag=self.environment)
        input_repos = [r for r in repos if "input" in r.tags]
        repo = RepositoryInstance(input_repos[0])
        return await repo.connect()
    
    async def get_output_repo(self):
        repos = self.registry.list_profiles(tag=self.environment)
        output_repos = [r for r in repos if "output" in r.tags]
        repo = RepositoryInstance(output_repos[0])
        return await repo.connect()
    
    async def process(self, input_path: str, output_path: str):
        input_client = await self.get_input_repo()
        output_client = await self.get_output_repo()
        
        # Read, transform, write
        data = await input_client.read(input_path)
        processed = data.upper()  # Example transform
        await output_client.write(output_path, content=processed)
```

### 2. Backup and Disaster Recovery

**Scenario**: Automated backup across multiple storage backends with restore capability.

```python
class BackupManager:
    async def backup(self, source: str, backup: str):
        """Backup all files from source to backup with timestamp"""
        registry = get_repository_registry()
        
        source_client = await self._connect(source)
        backup_client = await self._connect(backup)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/{source}/{timestamp}/"
        
        files = await source_client.list("", recursive=True)
        
        for file_path in files:
            content = await source_client.read(file_path)
            await backup_client.write(backup_dir + file_path, content=content)
    
    async def restore(self, backup: str, target: str, timestamp: str):
        """Restore files from backup to target"""
        # Implementation similar to backup
        pass
```

### 3. Configuration Management

**Scenario**: Store and retrieve application configurations across environments.

```python
class ConfigManager:
    def __init__(self, environment: str):
        self.environment = environment
        self.registry = get_repository_registry()
    
    async def get_config(self, app_name: str) -> dict:
        """Load configuration for an application"""
        client = await self._get_config_repo()
        content = await client.read(f"{app_name}/config.json")
        return json.loads(content)
    
    async def save_config(self, app_name: str, config: dict):
        """Save configuration for an application"""
        client = await self._get_config_repo()
        content = json.dumps(config, indent=2)
        await client.write(f"{app_name}/config.json", content=content)
```

### 4. REST API Integration

**Scenario**: Expose repository access via FastAPI.

```python
from fastapi import FastAPI, Depends
from darca_repository.server.dependencies import get_registry

app = FastAPI()

@app.get("/files/{repo}/{path:path}")
async def read_file(repo: str, path: str, registry = Depends(get_registry)):
    profile = registry.get_profile(repo)
    instance = RepositoryInstance(profile)
    client = await instance.connect()
    content = await client.read(path)
    return {"path": path, "content": content}

@app.post("/files/{repo}/{path:path}")
async def write_file(repo: str, path: str, data: dict, registry = Depends(get_registry)):
    profile = registry.get_profile(repo)
    instance = RepositoryInstance(profile)
    client = await instance.connect()
    await client.write(path, content=data["content"])
    return {"status": "success"}
```

## API Reference

### Main Exports

```python
from darca_repository import (
    Repository,              # Repository model
    StorageScheme,          # Storage scheme enum
    get_repository_registry, # Registry factory
    RepositoryInstance,     # Repository instance
)
```

### Registry API

```python
registry = get_repository_registry()

# Get a single profile
profile = registry.get_profile(name: str) -> Repository

# List profiles
profiles = registry.list_profiles(
    enabled_only: bool = False,
    tag: Optional[str] = None
) -> List[Repository]

# Add/update profile
registry.add_profile(repository: Repository) -> None

# Remove profile
registry.remove_profile(name: str) -> None
```

### Repository Instance API

```python
repo = RepositoryInstance(profile: Repository)

# Properties
repo.name: str
repo.metadata: Repository
repo.client: Optional[StorageClient]

# Methods
client = await repo.connect() -> StorageClient
is_available = await repo.test_connection() -> bool
```

### Storage Client API (from darca-storage)

```python
# Read operations
content = await client.read(path: str) -> str
exists = await client.exists(path: str) -> bool
files = await client.list(path: str, recursive: bool = False) -> List[str]

# Write operations
await client.write(path: str, content: str) -> None
await client.delete(path: str) -> None
```

### Exception Hierarchy

```python
RepositoryException              # Base exception
├── RepositoryNotFoundError      # Profile not found
├── RepositoryConnectionError    # Connection failed
├── RepositoryAccessDenied       # Permission denied
└── RepositoryValidationError    # Validation failed
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/roelkist/darca-repository.git
cd darca-repository
make install
```

### Run Tests

```bash
make test                    # Run all tests
poetry run pytest tests/     # Run with pytest directly
poetry run pytest -v tests/test_instance.py  # Run specific file
```

### Code Quality

```bash
make format    # Auto-format code (Black, isort)
make precommit # Run linters (Flake8, Bandit, Mypy)
make check     # Run everything (format + lint + test + docs)
```

### Build Documentation

```bash
make docs      # Build HTML documentation
```

### Project Structure

```
darca-repository/
├── src/darca_repository/    # Source code
│   ├── models.py           # Data models
│   ├── instance.py         # Repository instance
│   ├── exceptions.py       # Custom exceptions
│   ├── registry/           # Registry implementations
│   └── server/             # FastAPI server
├── tests/                  # Test suite
├── docs/                   # Documentation
└── pyproject.toml          # Project metadata
```

## Extending the Module

### Create Custom Registry Backend

```python
from darca_repository.registry.base import RepositoryRegistry

class PostgresRegistry(RepositoryRegistry):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def get_profile(self, name: str) -> Repository:
        # Query database
        pass
    
    def list_profiles(self, **kwargs) -> List[Repository]:
        # Query database
        pass
    
    def add_profile(self, repository: Repository) -> None:
        # Insert into database
        pass
    
    def remove_profile(self, name: str) -> None:
        # Delete from database
        pass
```

Register via entry points in `pyproject.toml`:

```toml
[project.entry-points."darca_repository.registries"]
postgres = "mypackage.postgres_registry:PostgresRegistry"
```

Use with:
```bash
export DARCA_REPOSITORY_MODE=postgres
```

### Add Custom Storage Scheme

1. Update enum in `models.py`:
```python
class StorageScheme(str, Enum):
    FILE = "file"
    S3 = "s3"
    MEMORY = "mem"
    NFS = "nfs"
    CUSTOM = "custom"  # New scheme
```

2. Implement connector in `darca-storage` package

3. Use in profiles:
```yaml
connection:
  scheme: custom
  storage_url: custom://endpoint
```

## Best Practices

### Security

✅ **DO:**
- Use environment variables for credentials
- Set restrictive file permissions on profile directory (700)
- Rotate credentials regularly
- Use minimal credential permissions

❌ **DON'T:**
- Hardcode credentials in profiles or code
- Commit profiles with secrets to version control
- Use admin/root credentials for application access
- Share credentials across environments

### Performance

✅ **DO:**
- Reuse `RepositoryInstance` for multiple operations
- Use `asyncio.gather()` for concurrent operations
- Cache registry lookups if profiles don't change
- Test connections before critical operations

❌ **DON'T:**
- Create new instances for every operation
- Use blocking I/O in async functions
- Ignore connection errors silently
- Skip connection testing in production

### Code Organization

✅ **DO:**
- Use tags to organize repositories by environment/team
- Set priority for fallback/failover scenarios
- Keep profile names descriptive and consistent
- Document custom registry implementations

❌ **DON'T:**
- Use special characters in profile names
- Mix production and development in same directory
- Leave unused profiles enabled
- Forget to update profiles when infrastructure changes

## Troubleshooting

### Common Issues

**Profile Not Found**
```
RepositoryNotFoundError: Repository 'my-repo' not found
```
- Check profile name spelling
- Verify profile directory location
- Ensure YAML file exists and is named correctly

**Connection Failed**
```
RepositoryConnectionError: Failed to connect to repository
```
- Test storage backend is reachable
- Verify credentials are set in environment
- Check URL format in profile
- Review storage backend logs

**Credential Resolution Failed**
```
Credentials not resolving from environment
```
- Check environment variable is set
- Verify variable name matches profile (case-sensitive)
- Use `${VAR_NAME}` syntax in YAML
- Test with `echo $VAR_NAME`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all operations log details
registry = get_repository_registry()
```

### Testing Profiles

Test a profile before use:

```bash
# Set environment
export DARCA_REPOSITORY_PROFILE_DIR=/path/to/profiles

# Test in Python
python -c "
from darca_repository import get_repository_registry
registry = get_repository_registry()
print(registry.list_profiles())
"
```

## Resources

### Documentation

- **GitHub**: https://github.com/roelkist/darca-repository
- **Full Docs**: https://roelkist.github.io/darca-repository/
- **PyPI**: https://pypi.org/project/darca-repository/

### Related Projects

- **darca-storage**: Storage abstraction layer
- **darca-exception**: Exception framework

### Support

- **Issues**: https://github.com/roelkist/darca-repository/issues
- **Discussions**: https://github.com/roelkist/darca-repository/discussions
- **Email**: roel.kist@gmail.com

### Learning Resources

- Python Asyncio: https://docs.python.org/3/library/asyncio.html
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/

---

## Summary

**darca-repository** provides a powerful, flexible abstraction for managing storage backends in Python applications. Key takeaways:

✅ **Configuration-driven**: Separate storage details from application code
✅ **Secure**: Environment variable interpolation for credentials  
✅ **Async-first**: Built for modern Python async/await patterns
✅ **Extensible**: Plugin system for custom registries and storage types
✅ **Production-ready**: Comprehensive testing, documentation, and error handling

Whether you're building data pipelines, backup systems, configuration management, or REST APIs, darca-repository provides the foundation for reliable, secure storage access.

**Next Steps:**
1. Install the package: `pip install darca-repository`
2. Create your first profile in `~/.local/share/darca_repository/profiles/`
3. Try the quick usage example
4. Read the full documentation for advanced features
5. Join the community on GitHub

Happy coding! 🚀
