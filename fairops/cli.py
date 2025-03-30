import click
from fairops.devops.container import DockerImage


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
