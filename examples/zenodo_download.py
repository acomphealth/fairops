import os
from fairops.repositories.zenodo import ZenodoClient
from fairops.utils.envpath import load_fairops_env


def download_data_doi(zenodo_api_token, zenodo_doi, output_path):
    os.makedirs(output_path, exist_ok=True)
    zenodo_client = ZenodoClient(zenodo_api_token)
    data_path = zenodo_client.download_files_by_doi(
        zenodo_doi,
        output_path
    )
    return data_path


def download_data_id(zenodo_api_token, zenodo_record_id, output_path):
    os.makedirs(output_path, exist_ok=True)
    zenodo_client = ZenodoClient(zenodo_api_token)
    data_path = zenodo_client.download_files_by_id(
        zenodo_record_id,
        output_path
    )
    return data_path


if __name__ == "__main__":
    load_fairops_env()

    zenodo_api_token = os.getenv("ZENODO_API_TOKEN")
    zenodo_doi = os.getenv("ZENODO_DOI")
    zenodo_record_id = os.getenv("ZENODO_RECORD_ID")

    raw_data_path = "data/input"
    raw_data_path = download_data_id(
        zenodo_api_token=zenodo_api_token,
        zenodo_record_id=zenodo_record_id,
        output_path=raw_data_path
    )
