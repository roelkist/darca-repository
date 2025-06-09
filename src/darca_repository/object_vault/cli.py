import json
import typer
from rich import print
from typing import Optional

from darca_repository.object_vault.factory import get_object_vault
from darca_repository.exceptions import ObjectNotFoundError

app = typer.Typer(help="DARCA Object Vault CLI")


@app.command("list")
async def list_objects(repository: str):
    vault = get_object_vault()
    objects = await vault.list_objects(repository)
    if not objects:
        print(f"[yellow]No objects found in '{repository}'.[/yellow]")
        return
    for obj in objects:
        print(json.dumps(obj.model_dump(mode="json"), indent=2))


@app.command("get")
async def get_object(repository: str, path: str):
    vault = get_object_vault()
    try:
        obj = await vault.get_object(repository, path)
        print(json.dumps(obj.model_dump(mode="json"), indent=2))
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("add")
async def add_object(
    repository: str = typer.Option(..., help="Target repository"),
    path: str = typer.Option(..., help="Object path"),
    type: Optional[str] = typer.Option(None, help="Type of object"),
    metadata: Optional[str] = typer.Option(None, help="Metadata as JSON string"),
):
    vault = get_object_vault()
    meta_dict = json.loads(metadata) if metadata else None
    await vault.add_object(repository, path, type=type, metadata=meta_dict)
    print(f"[green]Object '{path}' added to repository '{repository}'.[/green]")


@app.command("remove")
async def remove_object(repository: str, path: str):
    vault = get_object_vault()
    try:
        await vault.remove_object(repository, path)
        print(f"[green]Object '{path}' removed from '{repository}'.[/green]")
    except ObjectNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("update-type")
async def update_type(repository: str, path: str, type: Optional[str]):
    vault = get_object_vault()
    await vault.update_type(repository, path, type)
    print(f"[green]Type updated for object '{path}' in '{repository}'.[/green]")


@app.command("update-metadata")
async def update_metadata(repository: str, path: str, metadata: str):
    vault = get_object_vault()
    meta_dict = json.loads(metadata)
    await vault.update_metadata(repository, path, meta_dict)
    print(f"[green]Metadata updated for object '{path}' in '{repository}'.[/green]")


@app.command("touch")
async def touch_object(repository: str, path: str):
    vault = get_object_vault()
    await vault.touch_object(repository, path)
    print(f"[green]Object '{path}' in '{repository}' touched.[/green]")


if __name__ == "__main__":
    app()
