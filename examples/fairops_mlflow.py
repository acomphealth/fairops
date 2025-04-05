import mlflow
from fairops.mlops.autolog import LoggerFactory
from fairops.mlops.helpers import ResultsHelper
import os
import re


mlflow.set_experiment("autolog_example")

ml_logger = LoggerFactory.get_logger("mlflow")
output_path = "data/output"
ml_logger.get_experiment_metrics(output_path=output_path)

metrics_pattern = re.compile(r"^trial_metrics_[a-fA-F0-9]+\.json$")

# List and search
for filename in os.listdir(output_path):
    if metrics_pattern.match(filename):
        metrics_path = os.path.join(output_path, filename)
        break

results_helper = ResultsHelper()
results = results_helper.metrics_to_dataframe(metrics_path)

print(results.head())
print(results.columns)
