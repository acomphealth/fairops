import mlflow
from fairops.mlops.autolog import LoggerFactory
from fairops.mlops.helpers import ResultsHelper


mlflow.set_experiment("autolog_example")

ml_logger = LoggerFactory.get_logger("mlflow")
ml_logger.get_experiment_metrics(output_path="data/output")

results_helper = ResultsHelper()
results = results_helper.metrics_to_dataframe("data/output/trial_metrics_f5c1ac9e1ec7443292cb2c8211763408.json")

print(results.head())
print(results.columns)
