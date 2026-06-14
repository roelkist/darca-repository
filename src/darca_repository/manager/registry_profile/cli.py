# cli.py
'''
For testing:
export DARCA_REPOSITORY_MODE=mysql
export DARCA_REPOSITORY_MYSQL_HOST=mysql-darca-repository:3306
export DARCA_REPOSITORY_MYSQL_USER=darca_user
export DARCA_REPOSITORY_MYSQL_PASSWORD=darca_password
export DARCA_REPOSITORY_MYSQL_DATABASE=darca_database

darca-registry-cli add --name local_dev --storage-url file:///tmp/darca-local --scheme file --parameters '{"compression": "gzip"}'   --tags dev,test
darca-registry-cli list
darca-registry-cli get local_dev
darca-registry-cli remove local_dev
'''

import asyncio
import json
import typer
from rich import print
from typing import Optional

from darca_repository.registry.factory import get_repository_registry
from darca_repository.registry.models import RegistryProfile, StorageScheme
from darca_repository.exceptions import RepositoryNotFoundError

app = typer.Typer(help="DARCA Registry CLI")


@app.command("list")
def list_profiles(
    enabled_only: bool = typer.Option(False, "--enabled-only", "-e", help="Only show enabled profiles"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    asyncio.run(_list_profiles(enabled_only, tag))


async def _list_profiles(enabled_only: bool, tag: Optional[str]):
    registry = get_repository_registry()
    profiles = await registry.list_profiles(enabled_only=enabled_only, tag=tag)
    if not profiles:
        print("[yellow]No repository profiles found.[/yellow]")
        return
    for profile in profiles:
        print(json.dumps(profile.model_dump(mode="json"), indent=2))


@app.command("get")
def get_profile(name: str):
    asyncio.run(_get_profile(name))


async def _get_profile(name: str):
    registry = get_repository_registry()
    try:
        profile = await registry.get_profile(name)
        print(json.dumps(profile.model_dump(mode="json"), indent=2))
    except RepositoryNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("add")
def add_profile(
    name: str = typer.Option(..., help="Profile name"),
    storage_url: str = typer.Option(..., help="Storage URL"),
    scheme: StorageScheme = typer.Option(..., help="Storage scheme (file, s3, mem, nfs)"),
    credentials: Optional[str] = typer.Option(None, help="Credentials (JSON string)"),
    parameters: Optional[str] = typer.Option(None, help="Parameters (JSON string)"),
    enabled: bool = typer.Option(True, help="Mark profile as enabled"),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
):
    asyncio.run(_add_profile(name, storage_url, scheme, credentials, parameters, enabled, tags))


async def _add_profile(
    name: str,
    storage_url: str,
    scheme: StorageScheme,
    credentials: Optional[str],
    parameters: Optional[str],
    enabled: bool,
    tags: Optional[str],
):
    registry = get_repository_registry()

    try:
        creds_dict = json.loads(credentials) if credentials else None
        params_dict = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError as e:
        print(f"[red]Invalid JSON:[/red] {e}")
        raise typer.Exit(code=1)

    profile = RegistryProfile(
        name=name,
        storage_url=storage_url,
        scheme=scheme,
        credentials=creds_dict,
        parameters=params_dict,
        enabled=enabled,
        tags=[t.strip() for t in tags.split(",")] if tags else None,
    )

    await registry.add_profile(profile)
    print(f"[green]Profile '{name}' added.[/green]")


@app.command("remove")
def remove_profile(name: str):
    asyncio.run(_remove_profile(name))


async def _remove_profile(name: str):
    registry = get_repository_registry()
    try:
        await registry.remove_profile(name)
        print(f"[green]Profile '{name}' removed.[/green]")
    except RepositoryNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
