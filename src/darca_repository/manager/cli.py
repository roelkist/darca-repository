import asyncio
import json
import typer
from rich import print
from typing import Optional

from darca_repository.manager.factory import get_repository_manager

app = typer.Typer(help="DARCA Repository Manager CLI")


@app.command("create")
def create_repository(
    name: str = typer.Option(..., help="Repository name"),
    profile: str = typer.Option(..., help="Registry profile name"),
    description: Optional[str] = typer.Option(None, help="Optional repository description"),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
    priority: Optional[int] = typer.Option(None, help="Optional priority value"),
):
    asyncio.run(_create_repository(name, profile, description, tags, priority))


async def _create_repository(name: str, profile: str, description: Optional[str], tags: Optional[str], priority: Optional[int]):
    manager = get_repository_manager()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    try:
        binding = await manager.create_repository(name, profile, description=description, tags=tag_list, priority=priority)
        print("[green]Repository created:[/green]")
        print(json.dumps(binding.model_dump(mode="json"), indent=2))
    except Exception as e:
        print(f"[red]Error:[/red] {e}")


@app.command("list")
def list_repositories(tag: Optional[str] = typer.Option(None, "--tag", "-t")):
    asyncio.run(_list_repositories(tag))


async def _list_repositories(tag: Optional[str]):
    manager = get_repository_manager()
    bindings = await manager.list_repositories(tag=tag)
    if not bindings:
        print("[yellow]No repositories found.[/yellow]")
        return
    for b in bindings:
        print(json.dumps(b.model_dump(mode="json"), indent=2))


@app.command("add-object")
def add_object(
    repo: str = typer.Option(..., help="Repository name"),
    path: str = typer.Option(..., help="Object path"),
    type: Optional[str] = typer.Option(None, help="Type of the object"),
):
    asyncio.run(_add_object(repo, path, type))


async def _add_object(repo: str, path: str, type: Optional[str]):
    manager = get_repository_manager()
    await manager.add_object(repo, path, type=type)
    print(f"[green]Object '{path}' added to repository '{repo}'.[/green]")


@app.command("list-objects")
def list_objects(repo: str):
    asyncio.run(_list_objects(repo))


async def _list_objects(repo: str):
    manager = get_repository_manager()
    objects = await manager.list_objects(repo)
    if not objects:
        print(f"[yellow]No objects found in repository '{repo}'.[/yellow]")
        return
    for obj in objects:
        print(json.dumps(obj.model_dump(mode="json"), indent=2))


@app.command("remove")
def remove_repository(name: str):
    asyncio.run(_remove_repository(name))


async def _remove_repository(name: str):
    manager = get_repository_manager()
    await manager.remove_repository(name)
    print(f"[green]Repository '{name}' removed.[/green]")


if __name__ == "__main__":
    app()
