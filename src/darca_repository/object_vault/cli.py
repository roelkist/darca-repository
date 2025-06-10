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

# Add Objects to a Bucket
darca-object-vault-cli add --bucket test-bucket-1 --path /obj/1.txt --type document
darca-object-vault-cli add --bucket test-bucket-1 --path /obj/2.txt --type image

# List All Objects in the Bucket
darca-object-vault-cli list test-bucket-1

# Get Specific Object by Path
darca-object-vault-cli get test-bucket-1 /obj/1.txt

# Update Object Type
darca-object-vault-cli update-type test-bucket-1 /obj/1.txt archive

# Touch Object (updates modification time)
darca-object-vault-cli touch test-bucket-1 /obj/1.txt

# Remove Object from Bucket
darca-object-vault-cli remove test-bucket-1 /obj/2.txt

# Attempt to Get Non-Existent Object (error expected)
darca-object-vault-cli get test-bucket-1 /obj/missing.txt

# Add Object to New Bucket (bucket created automatically)
darca-object-vault-cli add --bucket new-bucket --path /obj/alpha.txt --type binary

"""

app = typer.Typer(help="DARCA Object Vault CLI")

@app.command("list")
def list_objects(bucket: str):
    asyncio.run(_list_objects(bucket))


async def _list_objects(bucket: str):
    vault = get_object_vault()
    objects = await vault.list_objects(bucket)
    if not objects:
        print(f"[yellow]No objects found in bucket '{bucket}'.[/yellow]")
        return
    for obj in objects:
        print(json.dumps(obj.model_dump(mode="json"), indent=2))


@app.command("get")
def get_object(bucket: str, path: str):
    asyncio.run(_get_object(bucket, path))


async def _get_object(bucket: str, path: str):
    vault = get_object_vault()
    try:
        obj = await vault.get_object(bucket, path)
        print(json.dumps(obj.model_dump(mode="json"), indent=2))
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("add")
def add_object(
    bucket: str = typer.Option(..., help="Target bucket name"),
    path: str = typer.Option(..., help="Object path"),
    type: Optional[str] = typer.Option(None, help="Type of object"),
):
    asyncio.run(_add_object(bucket, path, type))


async def _add_object(bucket: str, path: str, type: Optional[str]):
    vault = get_object_vault()
    await vault.add_object(bucket, path, type=type)
    print(f"[green]Object '{path}' added to bucket '{bucket}'.[/green]")


@app.command("remove")
def remove_object(bucket: str, path: str):
    asyncio.run(_remove_object(bucket, path))


async def _remove_object(bucket: str, path: str):
    vault = get_object_vault()
    try:
        await vault.remove_object(bucket, path)
        print(f"[green]Object '{path}' removed from bucket '{bucket}'.[/green]")
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("update-type")
def update_type(bucket: str, path: str, type: Optional[str]):
    asyncio.run(_update_type(bucket, path, type))


async def _update_type(bucket: str, path: str, type: Optional[str]):
    vault = get_object_vault()
    await vault.update_type(bucket, path, type)
    print(f"[green]Type updated for object '{path}' in bucket '{bucket}'.[/green]")


@app.command("touch")
def touch_object(bucket: str, path: str):
    asyncio.run(_touch_object(bucket, path))


async def _touch_object(bucket: str, path: str):
    vault = get_object_vault()
    await vault.touch_object(bucket, path)
    print(f"[green]Object '{path}' in bucket '{bucket}' touched.[/green]")


if __name__ == "__main__":
    app()