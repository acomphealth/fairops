from fairops.repositories.zenodo import ZenodoClient
from dotenv import load_dotenv
import os


load_dotenv()
zenodo_token = os.getenv("ZENODO_API_TOKEN")
zenodo = ZenodoClient(api_token=zenodo_token)

project_id = zenodo.create_project(
    title="DEMO: FAIRops library",
    description=""
)

example_data_path = "data/example.json"
zenodo.upload_files_to_project(
    project_id=project_id,
    file_paths=[example_data_path]
)
