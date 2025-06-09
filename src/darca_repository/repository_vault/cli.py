import asyncio
import json
import typer
from rich import print
from typing import Optional

from darca_repository.repository_vault.factory import get_repository_vault
from darca_repository.exceptions import RepositoryNotFoundError

app = typer.Typer(help="DARCA Repository Vault CLI")


@app.command("list")
def list_repositories(tag: Optional[str] = typer.Option(None, "--tag", "-t")):
    asyncio.run(_list_repositories(tag))


async def _list_repositories(tag: Optional[str]):
    vault = get_repository_vault()
    repos = await vault.list_repositories(tag=tag)
    if not repos:
        print("[yellow]No repositories found.[/yellow]")
        return
    for repo in repos:
        print(json.dumps(repo.model_dump(mode="json"), indent=2))


@app.command("get")
def get_repository(name: str):
    asyncio.run(_get_repository(name))


async def _get_repository(name: str):
    vault = get_repository_vault()
    try:
        repo = await vault.get_repository(name)
        print(json.dumps(repo.model_dump(mode="json"), indent=2))
    except RepositoryNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("create")
def create_repository(
    name: str = typer.Option(..., help="Repository name"),
    description: Optional[str] = typer.Option(None),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
    priority: Optional[int] = typer.Option(None),
):
    asyncio.run(_create_repository(name, description, tags, priority))


async def _create_repository(name: str, description: Optional[str], tags: Optional[str], priority: Optional[int]):
    vault = get_repository_vault()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    await vault.create_repository(name, description=description, tags=tag_list, priority=priority)
    print(f"[green]Repository '{name}' created.[/green]")


@app.command("remove")
def remove_repository(name: str):
    asyncio.run(_remove_repository(name))


async def _remove_repository(name: str):
    vault = get_repository_vault()
    try:
        await vault.remove_repository(name)
        print(f"[green]Repository '{name}' removed.[/green]")
    except RepositoryNotFoundError as e:
        print(f"[red]Error:[/red] {e}")


@app.command("update-description")
def update_description(name: str, description: Optional[str]):
    asyncio.run(_update_description(name, description))


async def _update_description(name: str, description: Optional[str]):
    vault = get_repository_vault()
    await vault.update_description(name, description)
    print(f"[green]Description updated for '{name}'.[/green]")


@app.command("update-tags")
def update_tags(name: str, tags: Optional[str]):
    asyncio.run(_update_tags(name, tags))


async def _update_tags(name: str, tags: Optional[str]):
    vault = get_repository_vault()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    await vault.update_tags(name, tag_list)
    print(f"[green]Tags updated for '{name}'.[/green]")


@app.command("update-priority")
def update_priority(name: str, priority: Optional[int]):
    asyncio.run(_update_priority(name, priority))


async def _update_priority(name: str, priority: Optional[int]):
    vault = get_repository_vault()
    await vault.update_priority(name, priority)
    print(f"[green]Priority updated for '{name}'.[/green]")


if __name__ == "__main__":
    app()
