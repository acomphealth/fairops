import importlib
import json
import os
from abc import ABC, abstractmethod

from fairops.mlops.models import (LoggedMetric, LoggedMetrics, LoggedParam,
                                  LoggedParams)

# Check for MLflow and W&B availability
mlflow_available = importlib.util.find_spec("mlflow") is not None
wandb_available = importlib.util.find_spec("wandb") is not None

# Conditional imports
if mlflow_available:
    import mlflow
    _original_mlflow_log_param = mlflow.log_param
    _original_mlflow_log_metric = mlflow.log_metric
    _original_mlflow_log_metrics = mlflow.log_metrics
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

        # Convert params data to a lookup dictionary {experiment_id -> {run_id -> [params_list]}}
        params_lookup = {
            exp["experiment_id"]: {
                run["run_id"]: run.get("parameters", [])
                for run in exp["runs"]
            }
            for exp in self.param_store.to_dict()
        }

        # Convert metrics data to a structured list
        for exp in self.metrics_store.to_dict():
            experiment_id = exp["experiment_id"]
            for run in exp["runs"]:
                run_id = run["run_id"]

                # Fetch parameters if available, otherwise use an empty list
                params_list = params_lookup.get(experiment_id, {}).get(run_id, [])

                # Keep metrics in array format
                metrics_list = run["metrics"]

                combined_data.append({
                    "experiment_id": experiment_id,
                    "run_id": run_id,
                    "params": params_list,
                    "metrics": metrics_list
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

    @abstractmethod
    def export_logs_as_artifact(self, local_base_path, artifact_filename="results.json", artifact_path=None):
        pass

    @abstractmethod
    def log_param(self, key: str, value, synchronous: bool | None = None):
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
    def export_logs_as_artifact(self, local_base_path, artifact_filename="results.json", artifact_path=None):
        experiment_id = mlflow.active_run().info.experiment_id
        run_id = mlflow.active_run().info.run_id

        log_file_path = self.generate_log_artifact(local_base_path, experiment_id, run_id, artifact_filename)
        if log_file_path is not None:
            mlflow.log_artifact(log_file_path, artifact_path)
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
    def get_logger(name):
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

    mlflow.log_param = mlflow_log_param_wrapper
    mlflow.log_metric = mlflow_log_metric_wrapper
    mlflow.log_metrics = mlflow_log_metrics_wrapper

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
