# cli.py
'''
For testing:
export DARCA_REPOSITORY_MODE=mysql
export DARCA_REPOSITORY_MYSQL_HOST=mysql-darca-repository:3306
export DARCA_REPOSITORY_MYSQL_USER=darca_user
export DARCA_REPOSITORY_MYSQL_PASSWORD=darca_password
export DARCA_REPOSITORY_MYSQL_DATABASE=darca_database
'''
import json
import typer
from rich import print
from typing import Optional

from darca_repository.registry.factory import get_repository_registry
from darca_repository.registry.models import RegistryProfile, StorageScheme
from darca_repository.exceptions import RepositoryNotFoundError

app = typer.Typer(help="DARCA Repository Registry CLI")

@app.command("list")
def list_profiles(
    enabled_only: bool = typer.Option(False, "--enabled-only", "-e", help="Only show enabled repositories"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """List all repository profiles."""
    registry = get_repository_registry()
    profiles = registry.list_profiles(enabled_only=enabled_only, tag=tag)
    if not profiles:
        print("[bold yellow]No repository profiles found.[/bold yellow]")
        return

    for profile in profiles:
        print(json.dumps(profile.model_dump(mode="json"), indent=2))


@app.command("get")
def get_profile(name: str):
    """Retrieve a specific repository profile by name."""
    registry = get_repository_registry()
    try:
        profile = registry.get_profile(name)
        print(json.dumps(profile.model_dump(mode="json"), indent=2))
    except RepositoryNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")


@app.command("add")
def add_profile(
    name: str = typer.Option(..., help="Repository name"),
    storage_url: str = typer.Option(..., help="Storage URL"),
    scheme: StorageScheme = typer.Option(..., help="Storage scheme (file, s3, mem, nfs)"),
    credentials: Optional[str] = typer.Option(None, help="Credentials as JSON string"),
    parameters: Optional[str] = typer.Option(None, help="Additional parameters as JSON string"),
):
    """Add a new repository profile."""
    registry = get_repository_registry()

    try:
        creds_dict = json.loads(credentials) if credentials else None
        params_dict = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError as e:
        print(f"[bold red]Invalid JSON provided:[/bold red] {e}")
        raise typer.Exit(code=1)

    profile = RegistryProfile(
        name=name,
        storage_url=storage_url,
        scheme=scheme,
        credentials=creds_dict,
        parameters=params_dict,
    )

    registry.add_profile(profile)
    print(f"[green]Repository '{name}' added successfully.[/green]")


@app.command("remove")
def remove_profile(name: str):
    """Remove a repository profile by name."""
    registry = get_repository_registry()
    try:
        registry.remove_profile(name)
        print(f"[green]Repository '{name}' removed.[/green]")
    except RepositoryNotFoundError as e:
        print(f"[bold red]Error:[/bold red] {e}")


@app.command("reload")
def reload_profiles():
    """Reload repository profiles (if supported)."""
    registry = get_repository_registry()
    if hasattr(registry, "reload"):
        registry.reload()
        print("[green]Registry reloaded successfully.[/green]")
    else:
        print("[yellow]This registry does not support reload operation.[/yellow]")


if __name__ == "__main__":
    app()
