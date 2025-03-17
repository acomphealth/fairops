import mlflow
from fairops.mlops.autolog import LoggerFactory


mlflow.set_experiment("autolog_example")

ml_logger = LoggerFactory.get_logger("mlflow")

with mlflow.start_run() as run:
    mlflow.log_metric("accuracy", 0.95)

print("MLflow Logged Metrics:", ml_logger.logged_metrics)
