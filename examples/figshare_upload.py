import os

from fairops.repositories.figshare import FigshareClient
from fairops.utils.envpath import load_fairops_env


load_fairops_env()

figshare_token = os.getenv("FIGSHARE_API_TOKEN")
figshare = FigshareClient(api_token=figshare_token)

project_id = figshare.create_project(
    title="DEMO: FAIRops library",
    description=""
)

example_data_path = "data/example.json"
result = figshare.upload_files_to_project(
    project_id=project_id,
    title="Example data file",
    file_paths=[example_data_path]
)

print(f"Upload complete: {result['url']}")

deleted_article_id = figshare.delete_article(result["article_id"])
print(f"Deleted article {deleted_article_id}")

deleted_project_id = figshare.delete_project(project_id)
print(f"Deleted project {deleted_project_id}")
