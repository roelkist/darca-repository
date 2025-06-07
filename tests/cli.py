import typer
import requests
import rich
from rich.pretty import pprint
from pathlib import Path
import yaml

app = typer.Typer()
SERVER_URL = "http://127.0.0.1:8000/repositories"

@app.command()
def list():
    """List all repositories"""
    resp = requests.get(SERVER_URL)
    resp.raise_for_status()
    pprint(resp.json())

@app.command()
def get(name: str):
    """Get repository details"""
    resp = requests.get(f"{SERVER_URL}/{name}")
    if resp.status_code == 404:
        typer.echo(f"Repository '{name}' not found.")
    else:
        resp.raise_for_status()
        pprint(resp.json())

@app.command()
def test(name: str):
    """Test connectivity of repository"""
    resp = requests.get(f"{SERVER_URL}/{name}/test")
    if resp.status_code == 404:
        typer.echo(f"Repository '{name}' not found.")
    else:
        resp.raise_for_status()
        success = resp.json()["success"]
        typer.echo(f"Connection test: {'✅ Success' if success else '❌ Failed'}")

@app.command()
def add(profile: Path):
    """Add or update a repository profile from YAML file"""
    with open(profile) as f:
        data = yaml.safe_load(f)
    resp = requests.post(SERVER_URL, json=data)
    resp.raise_for_status()
    typer.echo(f"Repository '{data['name']}' added.")
    pprint(resp.json())

@app.command()
def remove(name: str):
    """Remove a repository profile"""
    resp = requests.delete(f"{SERVER_URL}/{name}")
    if resp.status_code == 404:
        typer.echo(f"Repository '{name}' not found.")
    else:
        resp.raise_for_status()
        typer.echo(f"Repository '{name}' removed.")

if __name__ == "__main__":
    app()
