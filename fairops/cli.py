import click
import questionary
from fairops.devops.container import DockerImage
from fairops.repositories.zenodo import ZenodoClient
from fairops.repositories.figshare import FigshareClient
from dotenv import load_dotenv
import os
import tempfile


@click.group()
def cli():
    """fairops CLI - Manage MLOps workflows"""
    pass


@cli.group()
def docker():
    """Docker-related commands"""
    pass


@docker.command("package")
@click.argument("repo")
@click.argument("tag")
@click.argument("archive_path")
def package_image(repo, tag, archive_path):
    """Package a Docker image to an archive"""
    docker_image = DockerImage()
    docker_image.package_image(repo, tag, archive_path)


@docker.command("load")
@click.argument("archive_path")
def load_image(archive_path):
    """Package a Docker image to an archive"""
    docker_image = DockerImage()
    docker_image.load_image(archive_path)


def select_platform():
    return questionary.select(
        "Select upload platform:",
        choices=["Zenodo", "Figshare"]
    ).ask()


# TODO: Add documentation and consider fairops configure to log necessary tokens
@docker.command("publish")
@click.argument("repo")
@click.argument("tag")
@click.argument("archive_path")
def publish_image(repo, tag, archive_path):
    """
    Publish Docker image archive to a repository (Zenodo or Figshare)
    """
    load_dotenv()

    # Prompt for platform choice
    platform = select_platform()

    repository_client = None
    repository_token = os.getenv(f"{platform.upper()}_API_TOKEN")

    if repository_token is None:
        raise Exception(f"{platform.upper()}_API_TOKEN must be configured in .env file")

    if platform == "Zenodo":
        repository_client = ZenodoClient(api_token=repository_token)
    elif platform == "Figshare":
        repository_client = FigshareClient(api_token=repository_token)

    title = click.prompt("Enter a title for the record/project")
    description = click.prompt("Enter a description for the record/project")

    id = repository_client.create_project(
        title=title,
        description=description
    )

    # Simulate packaging/upload logic
    click.echo(f"\n📦 Preparing to upload {repo}:{tag} to {platform.capitalize()}")

    docker_image = DockerImage()
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_file_path = docker_image.package_image(repo, tag, tmpdir)

        # Simulate upload behavior
        click.echo(f"🔗 Uploading to {platform}...")
        repository_url = repository_client.upload_files_to_project(
            project_id=id,
            file_paths=[archive_file_path],
            title=title
        )

    click.echo(f"✅ Upload complete: {repository_url}")
