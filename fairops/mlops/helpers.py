import pandas as pd
import json


class ResultsHelper:
    def metrics_to_dataframe(self, metrics_file_path):
        metrics = None
        with open(metrics_file_path) as metrics_file:
            metrics = json.load(metrics_file)

        df = pd.DataFrame(metrics)

        # Expand 'params' and 'last_metrics' into separate columns
        params_df = df['params'].apply(pd.Series).add_prefix("param_")
        metrics_df = df['last_metrics'].apply(pd.Series).add_prefix("last_")

        # Drop the original nested columns and join expanded ones
        df = df.drop(columns=['params', 'last_metrics'])
        df = pd.concat([df, params_df, metrics_df], axis=1)

        return df
