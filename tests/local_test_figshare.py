import os
import json
import unittest
import tempfile
import shutil
import hashlib

from fairops.repositories.figshare import FigshareClient
from fairops.utils.envpath import load_fairops_env


# Probably a better way to do this, but sandbox API requires OAuth
# Currently, must be run locally for user's Figshare API token
class TestFigshare(unittest.TestCase):
    def hash_file(self, filepath, algorithm='sha256', chunk_size=8192):
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def setUp(self):
        load_fairops_env()

        self.figshare_client = FigshareClient(api_token=os.getenv("FIGSHARE_API_TOKEN"))
        self.output_dir = tempfile.mkdtemp()
        self.test_file_name = "test.json"
        self.test_file_path = os.path.join(self.output_dir, self.test_file_name)

        test_dict = {
            "example": "json",
            "id": 1
        }

        with open(self.test_file_path, 'w') as test_file:
            json.dump(test_dict, test_file)

    def tearDown(self):
        shutil.rmtree(self.output_dir)
        if self.article_id is not None:
            self.figshare_client.delete_article(self.article_id)
        if self.project_id is not None:
            self.figshare_client.delete_project(self.project_id)

    # TODO: Better test resolution for library, additional assertions from get project/get article when implemented
    def test_publish_delete(self):
        self.project_id = self.figshare_client.create_project(
            title="Temp: FAIRops Integration Test",
            description=""
        )

        self.assertIsNotNone(self.project_id)

        result = self.figshare_client.upload_files_to_project(
            project_id=self.project_id,
            title="Example data file",
            file_paths=[self.test_file_path]
        )

        self.assertIn("article_id", result)
        self.article_id = result["article_id"]
        self.assertIn("url", result)

        download_path = self.figshare_client.download_files(
            result["article_id"],
            self.output_dir
        )

        download_file_path = os.path.join(download_path, self.test_file_name)
        self.assertEqual(self.hash_file(download_file_path), self.hash_file(self.test_file_path))

        deleted_article_id = self.figshare_client.delete_article(self.article_id)
        self.assertEqual(deleted_article_id, self.article_id)
        self.article_id = None

        deleted_project_id = self.figshare_client.delete_project(self.project_id)
        self.assertEqual(deleted_project_id, self.project_id)
        self.project_id = None
