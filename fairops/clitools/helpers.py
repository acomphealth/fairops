import questionary
import os
from pathlib import Path
from fairops.repositories.figshare import FigshareClient
from fairops.repositories.zenodo import ZenodoClient


def select_repository():
    return questionary.select(
        "Select upload platform:",
        choices=["Zenodo", "Figshare"]
    ).ask()


def get_repository_client(repository):
    repository_token = os.getenv(f"{repository.upper()}_API_TOKEN")

    if repository_token is None:
        raise Exception(f"{repository.upper()}_API_TOKEN must be configured")

    if repository == "Zenodo":
        repository_client = ZenodoClient(api_token=repository_token)
    elif repository == "Figshare":
        repository_client = FigshareClient(api_token=repository_token)

    if repository is None:
        raise Exception(f"Failed to create {repository} client")

    return repository_client


def get_env_path(create_if_not_exist=False):
    home_path = Path.home()

    env_paths = {
        "cwd": ".env",
        "home_config": os.path.join(home_path, ".config", "fairops", ".env")
    }

    selected_env = None
    for key, env_path in env_paths.items():
        if os.path.exists(env_path):
            selected_env = env_path
            break

    if selected_env is None and create_if_not_exist:
        selected_env = env_path["home_config"]
        os.makedirs(os.path.dirname(selected_env))

    return selected_env
