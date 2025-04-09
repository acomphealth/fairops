import questionary
from rocrate.rocrate import ROCrate
import os
from fairops.repositories.figshare import FigshareClient
from fairops.repositories.zenodo import ZenodoClient
import re


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

# TODO: Move to mlops module and integrate additional experiment metadata into rocrate
def generate_crate_from_exp(path, compress):
    crate = ROCrate()
    metrics_pattern = re.compile(r"^trial_metrics_[a-fA-F0-9]+\.json$")
    
    for filename in os.listdir(path):
        if metrics_pattern.match(filename):
            metrics_path = os.path.join(path, filename)
            results_path = metrics_path.replace("trial_metrics", "trial_results").replace(".json", ".jsonl")

            crate.add_file(
                metrics_path,
                properties = {
                    "name": f"FAIROps Metrics ({os.path.basename(metrics_path)})",
                    "description": "FAIROps experiment metrics that can be loaded into pandas with fairops.ResultsHelper().metrics_to_dataframe()",
                    "encodingFormat": "application/json"
                }
            )
            crate.add_file(
                results_path,
                properties = {
                    "name": f"FAIROps Results ({os.path.basename(results_path)})",
                    "description": "FAIROps experiment results in jsonl format",
                    "encodingFormat": "application/jsonl"
                }
            )

    crate_path = os.path.join(path, "fairops_mlops_crate")
    os.makedirs(crate_path)

    if compress:
        crate.write_zip(os.path.join(crate_path, "fairops_mlops_crate.zip"))
    else:
        crate.write(crate_path)
    return crate_path
