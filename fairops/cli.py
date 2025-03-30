import click
from fairops.devops.container import DockerImage
from fairops.repositories.zenodo import ZenodoClient
from dotenv import load_dotenv
import os


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
    platforms = ["Zenodo"]
    click.echo("Select upload platform:")
    for i, platform in enumerate(platforms, start=1):
        click.echo(f"{i}. {platform.capitalize()}")
    choice = click.prompt("Enter choice number", type=click.IntRange(1, len(platforms)))
    return platforms[choice - 1]


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
    if platform == "Zenodo":
        zenodo_token = os.getenv("ZENODO_API_TOKEN")
        if zenodo_token is None:
            raise Exception("ZENODO_API_TOKEN must be configured in .env file")

        repository_client = ZenodoClient(api_token=zenodo_token)

    title = click.prompt("Enter a title for the record/project")
    description = click.prompt("Enter a description for the record/project")

    id = repository_client.create_project(
        title=title,
        description=description
    )

    # Simulate packaging/upload logic
    click.echo(f"\n📦 Preparing to upload {repo}:{tag} to {platform.capitalize()}")

    docker_image = DockerImage()
    archive_file_path = docker_image.package_image(repo, tag, archive_path)

    # Simulate upload behavior
    click.echo(f"🔗 Uploading to {platform}...")
    repository_client.upload_files_to_project(
        deposition_id=id,
        file_paths=[archive_file_path]
    )
    os.remove(archive_file_path)
    click.echo("✅ Upload complete")
