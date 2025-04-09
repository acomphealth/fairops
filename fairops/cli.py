import click
from fairops.clitools import docker_cli
from fairops.clitools import configure_cli
from fairops.utils.envpath import load_fairops_env
from dotenv import load_dotenv


@click.group()
def cli():
    """fairops CLI"""
    pass


@cli.group()
def configure():
    """Configuration-related commands"""
    pass


configure.add_command(configure_cli.configure_repository)
configure.add_command(configure_cli.which)


@cli.group()
def docker():
    """Docker-related commands"""
    load_fairops_env()


docker.add_command(docker_cli.package_image)
docker.add_command(docker_cli.load_image)
docker.add_command(docker_cli.publish_image)


if __name__ == "__main__":
    cli()
