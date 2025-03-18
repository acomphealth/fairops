import importlib
from collections import defaultdict
import pandas as pd
import time


# Check for MLflow and W&B availability
mlflow_available = importlib.util.find_spec("mlflow") is not None
wandb_available = importlib.util.find_spec("wandb") is not None

# Conditional imports
if mlflow_available:
    import mlflow
else:
    mlflow = None

if wandb_available:
    import wandb
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

    def to_dict(self):
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

    def to_dataframe(self):
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

    def to_dict(self):
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

    def to_dataframe(self):
        """Convert logged parameters into a Pandas DataFrame for analysis."""
        all_params = [
            param.to_dict()
            for exp in self.params.values()
            for run in exp.values()
            for param in run.values()
        ]
        return pd.DataFrame(all_params)
