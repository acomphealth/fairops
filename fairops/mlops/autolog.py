import importlib
from abc import ABC, abstractmethod
from collections import defaultdict
import pandas as pd


# Check for MLflow and W&B availability
mlflow_available = importlib.util.find_spec("mlflow") is not None
wandb_available = importlib.util.find_spec("wandb") is not None

# Conditional imports
if mlflow_available:
    import mlflow
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
                 timestamp: int | None = None, run_id: str | None = None):
        self.key = key
        self.value = value
        self.step = step if step is not None else 0
        self.timestamp = timestamp if timestamp is not None else 0
        self.run_id = run_id if run_id is not None else "default_run"

    def __repr__(self):
        return f"LoggedMetric(key={self.key}, value={self.value}, step={self.step}, timestamp={self.timestamp}, run_id={self.run_id})"

    def to_dict(self):
        """Convert to dictionary for easy logging/exporting."""
        return {
            "run_id": self.run_id,
            "key": self.key,
            "value": self.value,
            "step": self.step,
            "timestamp": self.timestamp
        }


class LoggedMetrics:
    def __init__(self):
        # Hierarchical storage: {run_id -> {key -> {step -> [LoggedMetric]}}}
        self.metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    def add_metric(self, metric: LoggedMetric):
        """Store a new metric."""
        self.metrics[metric.run_id][metric.key][metric.step].append(metric)

    def get_metrics(self, run_id: str | None = None, key: str | None = None, step: int | None = None):
        """Retrieve stored metrics for a given run_id, key, and/or step."""
        if run_id and run_id in self.metrics:
            if key and key in self.metrics[run_id]:
                if step is not None:
                    return self.metrics[run_id][key].get(step, [])
                return self.metrics[run_id][key]
            return self.metrics[run_id]
        return self.metrics  # Return all metrics if no filters applied

    def export_to_dataframe(self):
        """Convert logged metrics into a Pandas DataFrame for analysis."""
        all_metrics = [
            metric.to_dict()
            for run in self.metrics.values()
            for key in run.values()
            for step in key.values()
            for metric in step
        ]
        return pd.DataFrame(all_metrics)

    def aggregate(self, run_id: str, key: str, step: int, method="mean"):
        """Aggregate multiple values at the same step."""
        values = [m.value for m in self.get_metrics(run_id, key, step)]
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


# Abstract base class for logging
class AutoLogger(ABC):
    def __init__(self):
        self.metrics_store = LoggedMetrics()

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

        metric = LoggedMetric(key, value, step, timestamp, run_id)
        self.metrics_store.add_metric(metric)

        return _original_mlflow_log_metric(
            key,
            value,
            step,
            synchronous,
            timestamp,
            run_id
        )

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

        for k, v in metrics.items():
            metric = LoggedMetric(k, v, step, timestamp, run_id)
            self.metrics_store.add_metric(metric)

        return _original_mlflow_log_metrics(
            metrics,
            step,
            synchronous,
            run_id,
            timestamp
        )


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
