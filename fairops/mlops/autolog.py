import importlib
from abc import ABC, abstractmethod
from collections import defaultdict
import pandas as pd
import json
import time
import os


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
    _original_wandb_log = wandb.log if hasattr(wandb, "log") else None
else:
    wandb = None


class LoggedMetric:
    def __init__(self, key: str, value: float, step: int | None = None,
                 timestamp: int | None = None, run_id: str | None = None,
                 experiment_id: str | None = None):
        self.key = key
        self.value = value
        self.step = step
        self.timestamp = timestamp
        self.run_id = run_id
        self.experiment_id = experiment_id

        if self.experiment_id is None:
            self.experiment_id = mlflow.active_run().info.experiment_id

        self.timestamp = self.timestamp if self.timestamp is not None else int(time.time())
        if self.run_id is None:
            self.run_id = mlflow.active_run().info.run_id

    def __repr__(self):
        return f"LoggedMetric(key={self.key}, value={self.value}, step={self.step}, timestamp={self.timestamp}, run_id={self.run_id}, experiment_id={self.experiment_id})"

    def to_dict(self):
        """Convert to dictionary for easy logging/exporting."""
        return {
            "run_id": self.run_id,
            "key": self.key,
            "value": self.value,
            "step": self.step,
            "timestamp": self.timestamp,
            "experiment_id": self.experiment_id
        }


class LoggedMetrics:
    def __init__(self):
        # Hierarchical storage: {experiment_id -> {run_id -> {key -> {step -> [LoggedMetric]}}}}
        self.metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    def add_metric(self, metric: LoggedMetric):
        """Store a new metric."""
        self.metrics[metric.experiment_id][metric.run_id][metric.key][metric.step] = metric

    def get_metrics(self, experiment_id: str | None = None, run_id: str | None = None,
                    key: str | None = None, step: int | None = None):
        """Retrieve stored metrics for a given experiment_id, run_id, key, and/or step."""
        if experiment_id and experiment_id in self.metrics:
            if run_id and run_id in self.metrics[experiment_id]:
                if key and key in self.metrics[experiment_id][run_id]:
                    if step is not None:
                        return self.metrics[experiment_id][run_id][key].get(step, [])
                    return self.metrics[experiment_id][run_id][key]
                return self.metrics[experiment_id][run_id]
            return self.metrics[experiment_id]
        return self.metrics  # Return all metrics if no filters applied

    def export_to_dict(self):
        """Export logged metrics to a JSON file while preserving hierarchy."""
        structured_data = [
            {
                "experiment_id": experiment_id,
                "runs": [
                    {
                        "run_id": run_id,
                        "metrics": [
                            {
                                "key": key,
                                "steps": [
                                    {
                                        "step": step,
                                        "value": metric.value,
                                        "timestamp": metric.timestamp
                                    }
                                    for step, metric in key_metrics.items()
                                ]
                            }
                            for key, key_metrics in run_data.items()
                        ]
                    }
                    for run_id, run_data in exp_data.items()
                ]
            }
            for experiment_id, exp_data in self.metrics.items()
        ]
        return structured_data

    def export_to_dataframe(self):
        """Convert logged metrics into a Pandas DataFrame for analysis."""
        all_metrics = [{
            "experiment_id": experiment_id,
            "run_id": run_id,
            "key": key,
            "step": step,
            "value": metric.value,
            "timestamp": metric.timestamp
        }
            for experiment_id, exp_data in self.metrics.items()
            for run_id, run_data in exp_data.items()
            for key, key_metrics in run_data.items()
            for step, metric in key_metrics.items()
        ]
        return pd.DataFrame(all_metrics)

    def aggregate(self, experiment_id: str, run_id: str, key: str, step: int, method="mean"):
        """Aggregate multiple values at the same step for a specific experiment and run."""
        values = [m.value for m in self.get_metrics(experiment_id, run_id, key, step)]
        if not values:
            return None
        if method == "mean":
            return sum(values) / len(values)
        elif method == "max":
            return max(values)
        elif method == "min":
            return min(values)
        else:
            raise ValueError(f"Unsupported aggregation method: {method}")


class LoggedParam:
    def __init__(self, key: str, value: float, run_id: str | None = None, experiment_id: str | None = None):
        self.key = key
        self.value = value
        self.run_id = mlflow.active_run().info.run_id
        self.experiment_id = mlflow.active_run().info.experiment_id

    def __repr__(self):
        return f"LoggedParam(key={self.key}, value={self.value}, run_id={self.run_id}, experiment_id={self.experiment_id})"

    def to_dict(self):
        """Convert to dictionary for easy logging/exporting."""
        return {
            "run_id": self.run_id,
            "key": self.key,
            "value": self.value,
            "experiment_id": self.experiment_id
        }


class LoggedParams:
    def __init__(self):
        # Hierarchical storage: {experiment_id -> {run_id -> {key -> LoggedParam}}}
        self.params = defaultdict(lambda: defaultdict(dict))

    def add_param(self, param: LoggedParam):
        """Store a new parameter."""
        self.params[param.experiment_id][param.run_id][param.key] = param

    def get_params(self, experiment_id: str | None = None, run_id: str | None = None, key: str | None = None):
        """Retrieve stored parameters for a given experiment_id, run_id, and/or key."""
        if experiment_id and experiment_id in self.params:
            if run_id and run_id in self.params[experiment_id]:
                if key and key in self.params[experiment_id][run_id]:
                    return self.params[experiment_id][run_id][key]
                return self.params[experiment_id][run_id]
            return self.params[experiment_id]
        return self.params  # Return all parameters if no filters applied

    def export_to_dict(self):
        """Export logged parameters to a JSON file while preserving hierarchy."""
        structured_data = [
            {
                "experiment_id": experiment_id,
                "runs": [
                    {
                        "run_id": run_id,
                        "parameters": [
                            {"key": key, "value": param.value}
                            for key, param in run_data.items()
                        ]
                    }
                    for run_id, run_data in exp_data.items()
                ]
            }
            for experiment_id, exp_data in self.params.items()
        ]
        return structured_data

    def export_to_dataframe(self):
        """Convert logged parameters into a Pandas DataFrame for analysis."""
        all_params = [
            param.to_dict()
            for exp in self.params.values()
            for run in exp.values()
            for param in run.values()
        ]
        return pd.DataFrame(all_params)


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
            for exp in self.param_store.export_to_dict()
        }

        # Convert metrics data to a structured list
        for exp in self.metrics_store.export_to_dict():
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

    @abstractmethod
    def export_logs_as_artifact(self, base_path):
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
    def export_logs_as_artifact(self, base_path):
        experiment_id = mlflow.active_run().info.experiment_id
        run_id = mlflow.active_run().info.run_id
        log_path = os.path.join(base_path, experiment_id, run_id)
        os.makedirs(log_path, exist_ok=True)
        log_file_path = os.path.join(log_path, "results.json")
        if os.path.exists(log_file_path):
            raise Exception(f"Log file path already exists {log_file_path}")

        logs = self.export_logs_to_dict()
        run_logs = next((log for log in logs if log["experiment_id"] == experiment_id and log["run_id"] == run_id), None)

        if run_logs is not None:
            with open(log_file_path, "w") as log_file:
                json.dump(run_logs, log_file, indent=4)
            mlflow.log_artifact(log_file_path)
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

    def log_metric(self, key, value):
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

# Monkey-Patch wandb.log
if wandb_available:
    def wandb_log_wrapper(data, *args, **kwargs):
        logger = LoggerFactory.get_logger("wandb")
        if logger and isinstance(data, dict):
            for key, value in data.items():
                logger.log_metric(key, value)
    wandb.log = wandb_log_wrapper  # Overwrite wandb.log
