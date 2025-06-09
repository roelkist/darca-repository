import asyncio
import json
import typer
from rich import print
from typing import Optional

from darca_repository.object_vault.factory import get_object_vault
from darca_repository.exceptions import ObjectNotFoundError

"""
export DARCA_REPOSITORY_MODE=mysql
export DARCA_REPOSITORY_MYSQL_HOST=mysql-darca-repository:3306
export DARCA_REPOSITORY_MYSQL_USER=darca_user
export DARCA_REPOSITORY_MYSQL_PASSWORD=darca_password
export DARCA_REPOSITORY_MYSQL_DATABASE=darca_database

or 
export DARCA_REPOSITORY_MODE=yaml

# Add Objects
darca-object-vault-cli add --repository test-repo-1 --path /obj/1.txt --type document --metadata '{"size": 123, "owner": "alice"}'
darca-object-vault-cli add --repository test-repo-1 --path /obj/2.txt --type image --metadata '{"resolution": "1080p"}'

# List Objects
darca-object-vault-cli list test-repo-1

# Get Object
darca-object-vault-cli get test-repo-1 /obj/1.txt

# Update Object Fields
darca-object-vault-cli update-type test-repo-1 /obj/1.txt archive
darca-object-vault-cli update-metadata test-repo-1 /obj/1.txt '{"size": 456, "checked": true}'

# Touch Object
darca-object-vault-cli touch test-repo-1 /obj/1.txt

# Remove Object
darca-object-vault-cli remove  test-repo-1 /obj/2.txt

# Error: Get non-existent object
darca-object-vault-cli get test-repo-1 /obj/missing.txt

# Error: Add object to non-existent repository
darca-object-vault-cli add --repository fake-repo --path /obj/x.txt --type file --metadata '{"test": true}'

"""

app = typer.Typer(help="DARCA Object Vault CLI")


@app.command("list")
def list_objects(repository: str):
    asyncio.run(_list_objects(repository))


async def _list_objects(repository: str):
    vault = get_object_vault()
    objects = await vault.list_objects(repository)
    if not objects:
        print(f"[yellow]No objects found in '{repository}'.[/yellow]")
        return
    for obj in objects:
        print(json.dumps(obj.model_dump(mode="json"), indent=2))


@app.command("get")
def get_object(repository: str, path: str):
    asyncio.run(_get_object(repository, path))


async def _get_object(repository: str, path: str):
    vault = get_object_vault()
    try:
        obj = await vault.get_object(repository, path)
        print(json.dumps(obj.model_dump(mode="json"), indent=2))
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("add")
def add_object(
    repository: str = typer.Option(..., help="Target repository"),
    path: str = typer.Option(..., help="Object path"),
    type: Optional[str] = typer.Option(None, help="Type of object"),
    metadata: Optional[str] = typer.Option(None, help="Metadata as JSON string"),
):
    asyncio.run(_add_object(repository, path, type, metadata))


async def _add_object(repository: str, path: str, type: Optional[str], metadata: Optional[str]):
    vault = get_object_vault()
    meta_dict = json.loads(metadata) if metadata else None
    await vault.add_object(repository, path, type=type, metadata=meta_dict)
    print(f"[green]Object '{path}' added to repository '{repository}'.[/green]")


@app.command("remove")
def remove_object(repository: str, path: str):
    asyncio.run(_remove_object(repository, path))


async def _remove_object(repository: str, path: str):
    vault = get_object_vault()
    try:
        await vault.remove_object(repository, path)
        print(f"[green]Object '{path}' removed from '{repository}'.[/green]")
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("update-type")
def update_type(repository: str, path: str, type: Optional[str]):
    asyncio.run(_update_type(repository, path, type))


async def _update_type(repository: str, path: str, type: Optional[str]):
    vault = get_object_vault()
    await vault.update_type(repository, path, type)
    print(f"[green]Type updated for object '{path}' in '{repository}'.[/green]")


@app.command("update-metadata")
def update_metadata(repository: str, path: str, metadata: str):
    asyncio.run(_update_metadata(repository, path, metadata))


async def _update_metadata(repository: str, path: str, metadata: str):
    vault = get_object_vault()
    meta_dict = json.loads(metadata)
    await vault.update_metadata(repository, path, meta_dict)
    print(f"[green]Metadata updated for object '{path}' in '{repository}'.[/green]")


@app.command("touch")
def touch_object(repository: str, path: str):
    asyncio.run(_touch_object(repository, path))


async def _touch_object(repository: str, path: str):
    vault = get_object_vault()
    await vault.touch_object(repository, path)
    print(f"[green]Object '{path}' in '{repository}' touched.[/green]")


if __name__ == "__main__":
    app()
