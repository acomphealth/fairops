import click
from dotenv import set_key, get_key
from .helpers import select_repository
from utils.envpath import get_env_path


@click.command("repository")
def configure_repository():
    """Set or update repository API tokens for fairops"""
    env_path = get_env_path(create_if_not_exist=True)

    repository = select_repository()

    existing_key = get_key(env_path, f"{repository.upper()}_API_TOKEN")
    if existing_key is not None:
        click.echo(f"API key exists for {repository}. Enter new key to overwrite, or q to exit.")

    token = click.prompt(f"Enter your {repository} access token (q to quit)")
    if token == "q" or token == "Q":
        click.echo(f"Configuration not updated. Config file at: {env_path}")
        exit(0)

    set_key(env_path, f"{repository.upper()}_API_TOKEN", token)
    click.echo(f"Configuration updated: {env_path}")


@click.command("which")
def which():
    """Display active fairops environment file"""
    env_path = get_env_path()

    if env_path is not None:
        click.echo(f"Using configuration from: {env_path}")
    else:
        click.echo("Configuration file does not exist. Using env variables if present.")
