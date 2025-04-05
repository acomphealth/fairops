import os
import re
import unittest
import tempfile
import shutil
import mlflow

from fairops.mlops.autolog import LoggerFactory
from fairops.mlops.helpers import ResultsHelper


class TestMlflowAutologging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.metric_file = None
        cls.tracking_uri = f"file:///{cls.test_dir}/mlruns"
        cls.experiment_name = "fairops_tests"

        mlflow.set_tracking_uri(cls.tracking_uri)
        mlflow.set_experiment(cls.experiment_name)

        cls.logger = LoggerFactory.get_logger("mlflow")

        cls.test_values = {
            "n_trials": 2,
            "trial_test_values": [
                {
                    "param_loss": 0.001,
                    "param_beta_1": 0.02,
                    "param_model_type": "nn",
                    "metric_accuracies": [0.1, 0.2, 0.4, 0.6, 0.8],
                    "metric_test_accuracy": 0.75,
                    "metric_test_specificity": 0.9
                },
                {
                    "param_loss": 0.005,
                    "param_beta_1": 0.01,
                    "param_model_type": "cnn",
                    "metric_accuracies": [0.15, 0.3, 0.5, 0.7, 0.85],
                    "metric_test_accuracy": 0.78,
                    "metric_test_specificity": 0.92
                }
            ]
        }

        # Run experiment and export metrics once for all tests
        with mlflow.start_run() as parent_run:
            mlflow.log_param("n_trials", cls.test_values["n_trials"])

            for i, test_value in enumerate(cls.test_values["trial_test_values"]):
                with mlflow.start_run(nested=True) as run:
                    mlflow.log_param("loss", test_value["param_loss"])
                    mlflow.log_params({
                        "beta_1": test_value["param_beta_1"],
                        "model_type": test_value["param_model_type"],
                        "idx": i
                    })

                    for step, val in enumerate(test_value["metric_accuracies"]):
                        mlflow.log_metric("accuracy", val, step=step)

                    mlflow.log_metrics({
                        "test_accuracy": test_value["metric_test_accuracy"],
                        "test_specificity": test_value["metric_test_specificity"]
                    })

                    cls.logger.export_logs_as_artifact()

            cls.logger.export_logs_as_artifact()

        cls.logger.get_experiment_metrics(output_path=cls.test_dir)

        pattern = re.compile(r"^trial_metrics_[a-fA-F0-9]+\.json$")
        cls.metric_file = next(
            (os.path.join(cls.test_dir, f) for f in os.listdir(cls.test_dir) if pattern.match(f)),
            None
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def test_metric_file_exists(self):
        self.assertIsNotNone(self.metric_file, "Could not find trial_metrics_*.json file")

    def test_metrics_to_dataframe(self):
        results_helper = ResultsHelper()
        df = results_helper.metrics_to_dataframe(self.metric_file)

        self.assertFalse(df.empty)
        self.assertIn("last_test_accuracy", df.columns)
        self.assertIn("last_test_specificity", df.columns)


if __name__ == "__main__":
    unittest.main()
