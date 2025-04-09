import questionary
import os
from fairops.repositories.figshare import FigshareClient
from fairops.repositories.zenodo import ZenodoClient


def select_mlops_library():
    return questionary.select(
        "Select MLOps library:",
        choices=["MLFlow", "WandB"]
    ).ask()


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
