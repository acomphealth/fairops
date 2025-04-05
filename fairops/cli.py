import click
from fairops.clitools import docker_cli
from fairops.clitools import configure_cli
from fairops.clitools.helpers import get_env_path
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
    env_path = get_env_path()
    if env_path is not None:
        load_dotenv(env_path, override=True)
    else:
        click.echo("Warning: No environment config found.")
    pass


docker.add_command(docker_cli.package_image)
docker.add_command(docker_cli.load_image)
docker.add_command(docker_cli.publish_image)


if __name__ == "__main__":
    cli()
