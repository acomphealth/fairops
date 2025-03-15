import os
from fairops.figshare.client import FigshareClient
from dotenv import load_dotenv


def download_data(figshare_api_token, figshare_doi, output_path):
    os.makedirs(output_path, exist_ok=True)
    figshare_client = FigshareClient(figshare_api_token)
    data_path = figshare_client.download_files_by_doi(
        figshare_doi,
        output_path
    )
    return data_path


if __name__ == "__main__":
    load_dotenv()

    figshare_api_token = os.getenv("FIGSHARE_API_TOKEN")
    figshare_doi = os.getenv("FIGSHARE_DOI")

    raw_data_path = "data/input"
    raw_data_path = download_data(
        figshare_api_token=figshare_api_token,
        figshare_doi=figshare_doi,
        output_path=raw_data_path
    )
