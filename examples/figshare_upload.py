from fairops.figshare.client import FigshareClient
from dotenv import load_dotenv
import os


load_dotenv()
figshare_token = os.getenv("FIGSHARE_API_TOKEN")
figshare = FigshareClient(api_token=figshare_token)

project_id = figshare.create_project(
        title="DEMO: FAIRops library",
        description=""
    )

example_data_path = "data/example.json"
figshare.upload_files_to_project(
    project_id=project_id,
    title="Example data file",
    file_paths=[example_data_path]
)
