import tempfile
import click
import os
import re
import pandas as pd

from fairops.mlops.autolog import LoggerFactory
from fairops.mlops.helpers import ResultsHelper
from .helpers import select_mlops_library, select_repository, get_repository_client, generate_crate_from_exp


@click.command("publish")
def publish_experiment():
    """Publish an MLOps experiment RoCrate to a repository"""

    repository = select_repository()
    repository_client = get_repository_client(repository)

    title = click.prompt("Enter a title for the record/project")
    description = click.prompt("Enter a description for the record/project")

    ml_logger = None
    logger_type = select_mlops_library().lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        if logger_type == "mlflow":
            import mlflow

            tracking_uri = click.prompt("Enter MFlow Tracking URI (empty for current directory)", default="")
            if tracking_uri != "":
                mlflow.set_tracking_uri(tracking_uri.strip())

            experiment_id = click.prompt("Enter experiment ID")
            mlflow.set_experiment(experiment_id=experiment_id)

            ml_logger = LoggerFactory.get_logger("mlflow")
        else:
            ml_logger = LoggerFactory.get_logger("wandb")

        ml_logger.get_experiment_metrics(output_path=tmpdir)

        exp_crate = generate_crate_from_exp(tmpdir, compress=False)

        experiment_files = []
        for filename in os.listdir(exp_crate):
            experiment_files.append(os.path.join(exp_crate, filename))

        id = repository_client.create_project(
                title=title,
                description=description
            )

        repository_result = repository_client.upload_files_to_project(
            project_id=id,
            file_paths=experiment_files,
            title=f"FAIROps MLOps Crate for Experiment {experiment_id}"
        )

        click.echo(f"✅ Upload complete: {repository_result['url']}")

# TODO: Update docs for this
@click.command("visualize")
@click.argument("record_id")
@click.option("--private", is_flag=True)
def visualize(record_id, private):
    """Publish an MLOps experiment RoCrate to a repository"""

    print(record_id)
    repository = select_repository()
    repository_client = get_repository_client(repository)

    metrics_pattern = re.compile(r"^trial_metrics_[a-fA-F0-9]+\.json$")

    with tempfile.TemporaryDirectory() as tmpdir:
        repository_client.download_files_by_id(
            record_id=record_id,
            download_path=tmpdir,
            private=private
        )

        # List and search
        results_helper = ResultsHelper()
        results = None
        filenames = os.listdir(tmpdir)

        for filename in filenames:
            if metrics_pattern.match(filename):
                metrics_path = os.path.join(tmpdir, filename)
                cur_results = results_helper.metrics_to_dataframe(metrics_path)
                
                if results is None:
                    results = cur_results.copy()
                else:
                    results = pd.concat([results, cur_results], ignore_index=True)

        print(results.head())
