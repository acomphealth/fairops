import tempfile

import click

from fairops.devops.container import DockerImage

from .helpers import select_repository, get_repository_client


@click.command("package")
@click.argument("repo")
@click.argument("tag")
@click.argument("archive_path")
def package_image(repo, tag, archive_path):
    """Package a Docker image to an archive"""
    docker_image = DockerImage()
    docker_image.package_image(repo, tag, archive_path)


@click.command("load")
@click.argument("archive_path")
def load_image(archive_path):
    """Package a Docker image to an archive"""
    docker_image = DockerImage()
    docker_image.load_image(archive_path)


@click.command("publish")
@click.argument("repo")
@click.argument("tag")
def publish_image(repo, tag):
    """
    Publish Docker image archive to a repository (Zenodo or Figshare)
    """
    # Prompt for platform choice
    repository = select_repository()
    repository_client = get_repository_client(repository)

    title = click.prompt("Enter a title for the record/project")
    description = click.prompt("Enter a description for the record/project")

    id = repository_client.create_project(
        title=title,
        description=description
    )

    click.echo(f"\n📦 Preparing to upload {repo}:{tag} to {repository.capitalize()}")

    docker_image = DockerImage()
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_file_path = docker_image.package_image(repo, tag, tmpdir)

        click.echo(f"🔗 Uploading to {repository}...")
        repository_result = repository_client.upload_files_to_project(
            project_id=id,
            file_paths=[archive_file_path],
            title=title
        )

    click.echo(f"✅ Upload complete: {repository_result['url']}")
