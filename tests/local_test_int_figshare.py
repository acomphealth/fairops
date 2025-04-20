import os
import json
import unittest
import tempfile
import shutil
import hashlib
from parameterized import parameterized

from fairops.repositories.figshare import FigshareClient
from fairops.repositories.zenodo import ZenodoClient
from fairops.utils.envpath import load_fairops_env


# Probably a better way to do this, but sandbox API requires OAuth
# Currently, must be run locally for user's Figshare API token
class TestRepositories(unittest.TestCase):
    def hash_file(self, filepath, algorithm='sha256', chunk_size=8192):
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def setUp(self):
        load_fairops_env()

        self.output_dir = tempfile.mkdtemp()
        self.test_file_name_1 = "test.json"
        self.test_file_path_1 = os.path.join(self.output_dir, self.test_file_name_1)
        self.test_file_name_2 = "test2.json"
        self.test_file_path_2 = os.path.join(self.output_dir, self.test_file_name_2)

        test_dict_1 = {
            "example": "json",
            "id": 1
        }

        test_dict_2 = {
            "example": "more_json",
            "id": 2
        }

        with open(self.test_file_path_1, 'w') as test_file:
            json.dump(test_dict_1, test_file)
        with open(self.test_file_path_2, 'w') as test_file:
            json.dump(test_dict_2, test_file)

    def tearDown(self):
        shutil.rmtree(self.output_dir)
        if self.article_id is not None:
            self.repository_client.delete_article(self.article_id)
        if self.project_id is not None:
            self.repository_client.delete_project(self.project_id)

    # TODO: Better test resolution for library, additional assertions from get project/get article when implemented
    @parameterized.expand([
        ("figshare"),
        # ("zenodo"),
    ])
    def test_single_publish_delete(self, name):
        # TODO: Change to getclient method
        self.repository_client = None
        if name == "figshare":
            self.repository_client = FigshareClient(api_token=os.getenv("FIGSHARE_API_TOKEN"))
        elif name == "zenodo":
            self.repository_client = ZenodoClient(api_token=os.getenv("FIGSHARE_API_TOKEN"))

        self.project_id = self.repository_client.create_project(
            title="Temp: FAIRops Integration Test",
            description=""
        )

        self.assertIsNotNone(self.project_id)

        result = self.repository_client.upload_files_to_project(
            project_id=self.project_id,
            title="Example data file",
            file_paths=[self.test_file_path_1]
        )

        self.assertIn("article_id", result)
        self.article_id = result["article_id"]
        self.assertIn("url", result)

        download_dir = os.path.join(self.output_dir, str(result["article_id"]))
        os.makedirs(download_dir)

        download_path = self.repository_client.download_files_by_id(
            result["article_id"],
            download_dir
        )

        downloaded_files = os.listdir(download_path)
        self.assertEqual(len(downloaded_files), 1)

        download_file_path = os.path.join(download_path, self.test_file_name_1)
        self.assertEqual(self.hash_file(download_file_path), self.hash_file(self.test_file_path_1))

        deleted_article_id = self.repository_client.delete_article(self.article_id)
        self.assertEqual(deleted_article_id, self.article_id)
        self.article_id = None

        deleted_project_id = self.repository_client.delete_project(self.project_id)
        self.assertEqual(deleted_project_id, self.project_id)
        self.project_id = None

    @parameterized.expand([
        ("figshare"),
        # ("zenodo"),
    ])
    def test_multi_publish_delete(self, name):
        # TODO: Change to getclient method
        self.repository_client = None
        if name == "figshare":
            self.repository_client = FigshareClient(api_token=os.getenv("FIGSHARE_API_TOKEN"))
        elif name == "zenodo":
            self.repository_client = ZenodoClient(api_token=os.getenv("FIGSHARE_API_TOKEN"))

        self.project_id = self.repository_client.create_project(
            title="Temp: FAIRops Integration Test",
            description=""
        )

        self.assertIsNotNone(self.project_id)

        result = self.repository_client.upload_files_to_project(
            project_id=self.project_id,
            title="Example data file",
            file_paths=[self.test_file_path_1, self.test_file_path_2]
        )

        self.assertIn("article_id", result)
        self.article_id = result["article_id"]
        self.assertIn("url", result)

        download_dir = os.path.join(self.output_dir, str(result["article_id"]))
        os.makedirs(download_dir)

        download_path = self.repository_client.download_files_by_id(
            result["article_id"],
            download_dir
        )

        downloaded_files = os.listdir(download_path)
        self.assertEqual(len(downloaded_files), 2)

        download_file_path = os.path.join(download_path, self.test_file_name_1)
        self.assertEqual(self.hash_file(download_file_path), self.hash_file(self.test_file_path_1))

        download_file_path = os.path.join(download_path, self.test_file_name_2)
        self.assertEqual(self.hash_file(download_file_path), self.hash_file(self.test_file_path_2))

        deleted_article_id = self.repository_client.delete_article(self.article_id)
        self.assertEqual(deleted_article_id, self.article_id)
        self.article_id = None

        deleted_project_id = self.repository_client.delete_project(self.project_id)
        self.assertEqual(deleted_project_id, self.project_id)
        self.project_id = None
