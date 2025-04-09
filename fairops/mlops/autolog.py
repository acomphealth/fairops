import importlib
import json
import os
import tempfile
from abc import ABC, abstractmethod
import shutil
from typing import Union, Optional

from .models import LoggedMetric, LoggedMetrics, LoggedParam, LoggedParams


# Check for MLflow and W&B availability
mlflow_available = importlib.util.find_spec("mlflow") is not None
wandb_available = importlib.util.find_spec("wandb") is not None

# Conditional imports
if mlflow_available:
    import mlflow
    from mlflow.entities import RunStatus
    _original_mlflow_log_param = mlflow.log_param
    _original_mlflow_log_params = mlflow.log_params
    _original_mlflow_log_metric = mlflow.log_metric
    _original_mlflow_log_metrics = mlflow.log_metrics
    _original_mlflow_end_run = mlflow.end_run
else:
    mlflow = None

if wandb_available:
    import wandb
    _original_wandb_log = wandb.log
else:
    wandb = None


# Abstract base class for logging
class AutoLogger(ABC):
    def __init__(self):
        self.metrics_store = LoggedMetrics()
        self.param_store = LoggedParams()
        self.fairops_log_path = "fairops"
        self.fairops_log_file = "trial_results.json"

    def parse_last_metrics(self, child_data):
        last_metrics = {
            "experiment_id": child_data["experiment_id"],
            "experiment_name": child_data["experiment_name"],
            "parent_run_id": child_data["parent_run_id"],
            "run_id": child_data["run_id"],
            "run_name": child_data["run_name"],
            "params": {},
            "last_metrics": child_data["last_metrics"].copy()
        }

        for param in child_data["params"]:
            last_metrics["params"][param["key"]] = param["value"]

        return last_metrics

    def export_logs_to_dict(self):
        """
        Combines metrics and parameters into a unified JSON structure.

        Args:
            metrics_data (list): List of dictionaries containing metrics.
            params_data (list): List of dictionaries containing parameters.
            filepath (str, optional): Path to save the JSON file.

        Returns:
            str: JSON-formatted string.
        """
        combined_data = []
        completed = []

        # Ensure param_store and metrics_store are not None and have data
        params_list = self.param_store.to_dict() if self.param_store else []
        metrics_list = self.metrics_store.to_dict() if self.metrics_store else []

        # Convert params data to a lookup dictionary {experiment_id -> {run_id -> [params_list]}}
        params_lookup = {
            exp.get("experiment_id"): {
                run.get("run_id"): run.get("parameters", [])
                for run in exp.get("runs", [])
            }
            for exp in params_list
        } if params_list else {}

        # Convert metrics data to a structured list
        for exp in metrics_list:
            experiment_id = exp.get("experiment_id")
            for run in exp.get("runs", []):
                run_id = run.get("run_id")

                # Fetch parameters if available, otherwise use an empty list
                run_params_list = params_lookup.get(experiment_id, {}).get(run_id, [])

                # Fetch metrics if available, otherwise use an empty list
                run_metrics_list = run.get("metrics", [])

                completed.append(f"{experiment_id}{run_id}")

                parent_run_id = None
                parent_run = mlflow.get_parent_run(run_id)
                if parent_run is not None:
                    parent_run_id = parent_run.info.run_id

                metrics_last = {}
                for metric in run_metrics_list:
                    key = metric["key"]
                    steps = metric["steps"]

                    valid_steps = [s for s in steps if s["step"] is not None]
                    if valid_steps:
                        # Get the one with the largest step
                        last = max(valid_steps, key=lambda x: x["step"])
                    else:
                        # No valid steps, take last item
                        last = steps[-1]

                    metrics_last[key] = last["value"]

                combined_data.append({
                    "experiment_id": experiment_id,
                    "experiment_name": mlflow.get_experiment(experiment_id).name,
                    "parent_run_id": parent_run_id,
                    "run_id": run_id,
                    "run_name": mlflow.get_run(run_id).info.run_name,
                    "params": run_params_list,
                    "metrics": run_metrics_list,
                    "last_metrics": metrics_last
                })

        # If metrics data is missing but params exist, include runs from params_store
        for experiment_id, runs in params_lookup.items():
            for run_id, params in runs.items():
                if f"{experiment_id}{run_id}" not in completed:
                    parent_run_id = None
                    parent_run = mlflow.get_parent_run(run_id)
                    if parent_run is not None:
                        parent_run_id = parent_run.info.run_id

                    combined_data.append({
                        "experiment_id": experiment_id,
                        "experiment_name": mlflow.get_experiment(experiment_id).name,
                        "parent_run_id": parent_run_id,
                        "run_id": run_id,
                        "run_name": mlflow.get_run(run_id).info.run_name,
                        "params": params,
                        "metrics": [],
                        "last_metrics": {}
                    })

        return combined_data

    def generate_log_artifact(self, local_base_path, experiment_id, run_id, artifact_filename="results.json"):
        log_path = os.path.join(local_base_path, experiment_id, run_id)
        os.makedirs(log_path, exist_ok=True)
        log_file_path = os.path.join(log_path, artifact_filename)
        if os.path.exists(log_file_path):
            raise Exception(f"Log file path already exists {log_file_path}")

        logs = self.export_logs_to_dict()
        run_logs = next((log for log in logs if log["experiment_id"] == experiment_id and log["run_id"] == run_id), None)

        if run_logs is not None:
            with open(log_file_path, "w") as log_file:
                json.dump(run_logs, log_file, indent=4)
            return log_file_path

        return None

    def clear_run_logs(self, experiment_id, run_id):
        if experiment_id in self.metrics_store.metrics:
            if run_id in self.metrics_store.metrics[experiment_id]:
                del self.metrics_store.metrics[experiment_id][run_id]

        if experiment_id in self.param_store.params:
            if run_id in self.param_store.params[experiment_id]:
                del self.param_store.params[experiment_id][run_id]

    @abstractmethod
    def get_experiment_metrics(self):
        pass

    @abstractmethod
    def export_logs_as_artifact(self):
        pass

    @abstractmethod
    def log_param(self, key: str, value, synchronous: bool | None = None):
        pass

    @abstractmethod
    def log_params(self, params: dict[str, ], synchronous: bool | None = None, run_id: str | None = None):
        pass

    @abstractmethod
    def log_metric(self, key: str, value: float, step: int | None = None,
                   synchronous: bool | None = None, timestamp: int | None = None,
                   run_id: str | None = None):
        pass

    @abstractmethod
    def log_metrics(self, metrics: dict[str, float], step: int | None = None,
                    synchronous: bool | None = None, timestamp: int | None = None,
                    run_id: str | None = None):
        pass


# MLflow Logger Implementation
class MLflowAutoLogger(AutoLogger):
    # Refactor this to an AutoLogger method for wandb+mlflow where appropriate
    def get_experiment_metrics(
            self,
            tracking_uri=None,
            experiment_name=None,
            experiment_id=None,
            parent_run_ids=None,
            output_path=None
    ):
        fairops_artifact_path = os.path.join(self.fairops_log_path, self.fairops_log_file)

        if tracking_uri is not None:
            mlflow.set_tracking_uri(tracking_uri=tracking_uri)

        client = mlflow.MlflowClient()
        if experiment_name is not None:
            mlflow.set_experiment(experiment_name=experiment_name)
        elif experiment_id is not None:
            mlflow.set_experiment(experiment_id=experiment_id)

        if parent_run_ids is None:
            runs = mlflow.search_runs()[["run_id", "tags.mlflow.parentRunId"]]
            parent_run_ids = runs[runs['tags.mlflow.parentRunId'].isnull()]['run_id'].tolist()

        for parent_run_id in parent_run_ids:
            with tempfile.TemporaryDirectory() as tmpdir:
                trial_path = os.path.join(tmpdir, parent_run_id)
                if output_path is None:
                    output_path = trial_path
                else:
                    os.makedirs(output_path, exist_ok=True)

                os.makedirs(trial_path)

                local_artifact_path = client.download_artifacts(
                    parent_run_id,
                    fairops_artifact_path,
                    trial_path
                )
                shutil.move(local_artifact_path, os.path.join(trial_path, "parent.json"))

                child_run_ids = runs[runs['tags.mlflow.parentRunId'] == parent_run_id]['run_id'].tolist()
                for child_run_id in child_run_ids:
                    try:
                        local_artifact_path = client.download_artifacts(
                            child_run_id,
                            fairops_artifact_path,
                            trial_path
                        )
                    except Exception as ex:  # noqa: F841
                        # TODO: add skipped child run to the results/metrics file but without only run id
                        print(f"FAIROps trial metrics not found for run: {child_run_id}")
                        pass

                    shutil.move(local_artifact_path, os.path.join(trial_path, f"{child_run_id}.json"))

                with open(os.path.join(trial_path, "parent.json"), 'r') as f:
                    parent_data = json.load(f)
                    trial_results_path = os.path.join(output_path, f"trial_results_{parent_run_id}.jsonl")
                    trial_metrics_path = os.path.join(output_path, f"trial_metrics_{parent_run_id}.json")

                    last_metrics = []
                    with open(trial_results_path, 'w') as out_f:
                        out_f.write(json.dumps(parent_data) + "\n")

                        for child_run_id in child_run_ids:
                            child_artifact = os.path.join(trial_path, f"{child_run_id}.json")
                            with open(child_artifact, 'r') as child_f:
                                child_data = json.load(child_f)
                                child_last_metrics = self.parse_last_metrics(child_data)
                                last_metrics.append(child_last_metrics)
                                out_f.write(json.dumps(child_data) + "\n")

                    with open(trial_metrics_path, 'w') as metric_out_f:
                        json.dump(last_metrics, metric_out_f, indent=4)

        return

    def export_logs_as_artifact(self):
        experiment_id = mlflow.active_run().info.experiment_id
        run_id = mlflow.active_run().info.run_id

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file_path = self.generate_log_artifact(tmpdir, experiment_id, run_id, self.fairops_log_file)
            if log_file_path is not None:
                mlflow.log_artifact(log_file_path, self.fairops_log_path)
                os.remove(log_file_path)

    def log_param(
            self,
            key: str,
            value,
            synchronous: bool | None = None):

        if not mlflow_available:
            print("[MLflowAutoLogger] MLflow is not installed. Skipping logging.")
            return

        param_result = _original_mlflow_log_param(key, value, synchronous)

        param = LoggedParam(key, value)
        self.param_store.add_param(param)

        return param_result

    def log_params(self, params: dict[str, ], synchronous: bool | None = None, run_id: str | None = None):
        if not mlflow_available:
            print("[MLflowAutoLogger] MLflow is not installed. Skipping logging.")
            return

        if run_id is not None:
            # TODO: Update to specify run_id (only present in log_params, not log_param)
            raise NotImplementedError("Autologging does not support parameter logging for non-active run")

        param_result = _original_mlflow_log_params(params, synchronous, run_id)

        for key, value in params.items():
            param = LoggedParam(key, value)
            self.param_store.add_param(param)

        return param_result

    def log_metric(
            self,
            key: str,
            value: float,
            step: int | None = None,
            synchronous: bool | None = None,
            timestamp: int | None = None,
            run_id: str | None = None):

        if not mlflow_available:
            print("[MLflowAutoLogger] MLflow is not installed. Skipping logging.")
            return

        run_operation = _original_mlflow_log_metric(
            key,
            value,
            step,
            synchronous,
            timestamp,
            run_id
        )

        metric = LoggedMetric(key, value, step, timestamp, run_id)
        self.metrics_store.add_metric(metric)

        return run_operation

    def log_metrics(
            self,
            metrics: dict[str, float],
            step: int | None = None,
            synchronous: bool | None = None,
            run_id: str | None = None,
            timestamp: int | None = None):

        if not mlflow_available:
            print("[MLflowAutoLogger] MLflow is not installed. Skipping logging.")
            return

        run_operation = _original_mlflow_log_metrics(
            metrics,
            step,
            synchronous,
            run_id,
            timestamp
        )

        for k, v in metrics.items():
            metric = LoggedMetric(k, v, step, timestamp, run_id)
            self.metrics_store.add_metric(metric)

        return run_operation

    def end_run(
            self,
            status: str = RunStatus.to_string(RunStatus.FINISHED)):

        self.clear_run_logs(
            mlflow.active_run().info.experiment_id,
            mlflow.active_run().info.run_id
        )
        return _original_mlflow_end_run(status)


# W&B Logger Implementation
class WandbAutoLogger(AutoLogger):
    def __init__(self):
        self.logged_metrics = []

    def log(
            self,
            data: dict[str, ],
            step: int | None = None,
            commit: bool | None = None,
            sync: bool | None = None):
        raise NotImplementedError()


# Logger Factory (Auto-registering)
class LoggerFactory:
    _loggers = {}

    @staticmethod
    def get_logger(name) -> Optional[Union[MLflowAutoLogger, WandbAutoLogger]]:
        """Retrieves a logger, registering it automatically if needed."""
        if name not in LoggerFactory._loggers:
            if name == "mlflow" and mlflow_available:
                LoggerFactory._loggers[name] = MLflowAutoLogger()
            elif name == "wandb" and wandb_available:
                LoggerFactory._loggers[name] = WandbAutoLogger()
            else:
                print(f"[LoggerFactory] No available logger for '{name}'.")
                return None  # Return None if logger is unavailable
        return LoggerFactory._loggers[name]


# Monkey-Patch mlflow.log_metric
if mlflow_available:
    def mlflow_log_param_wrapper(
            key: str,
            value,
            synchronous: bool | None = None):
        logger = LoggerFactory.get_logger("mlflow")
        if logger:
            logger.log_param(key, value, synchronous)

    def mlflow_log_params_wrapper(params: dict[str, ], synchronous: bool | None = None, run_id: str | None = None):
        logger = LoggerFactory.get_logger("mlflow")
        if logger:
            logger.log_params(params, synchronous, run_id)

    def mlflow_log_metric_wrapper(
            key: str,
            value: float,
            step: int | None = None,
            synchronous: bool | None = None,
            timestamp: int | None = None,
            run_id: str | None = None):
        logger = LoggerFactory.get_logger("mlflow")
        if logger:
            logger.log_metric(key, value, step, synchronous, timestamp, run_id)

    def mlflow_log_metrics_wrapper(
            metrics: dict[str, float],
            step: int | None = None,
            synchronous: bool | None = None,
            run_id: str | None = None,
            timestamp: int | None = None):
        logger = LoggerFactory.get_logger("mlflow")
        if logger:
            logger.log_metrics(metrics, step, synchronous, timestamp, run_id)

    def mlflow_end_run_wrapper(status: str = RunStatus.to_string(RunStatus.FINISHED)):
        logger = LoggerFactory.get_logger("mlflow")
        if logger:
            logger.end_run(status)

    mlflow.log_param = mlflow_log_param_wrapper
    mlflow.log_params = mlflow_log_params_wrapper
    mlflow.log_metric = mlflow_log_metric_wrapper
    mlflow.log_metrics = mlflow_log_metrics_wrapper
    mlflow.end_run = mlflow_end_run_wrapper

# Monkey-Patch
if wandb_available:
    def wandb_log(
            data: dict[str, ],
            step: int | None = None,
            commit: bool | None = None,
            sync: bool | None = None):
        logger = LoggerFactory.get_logger("wandb")
        logger.log(data, step, commit, sync)

    wandb.log = wandb_log
