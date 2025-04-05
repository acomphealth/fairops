import os
import unittest
import tempfile
import shutil
from docker.errors import ImageNotFound
import hashlib

from fairops.devops.container import DockerImage


class TestDockerImageIntegration(unittest.TestCase):
    def setUp(self):
        self.docker_image = DockerImage()
        self.repo = "alpine"
        self.tag = "3.20"
        self.archive_hash = "4dd766dea72b9bcf1d36087dcc45ab6c93e1ce56fbadeedde7514cd1f6bbb90e"
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def get_file_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def test_image_exists_locally_and_pull(self):
        # Ensure image is not present
        try:
            self.docker_image.client.images.remove(f"{self.repo}:{self.tag}", force=True)
        except ImageNotFound:
            pass

        self.assertFalse(self.docker_image.image_exists_locally(self.repo, self.tag))

        # Should pull it now
        self.docker_image.client.images.pull(self.repo, self.tag)
        self.assertTrue(self.docker_image.image_exists_locally(self.repo, self.tag))

    def test_package_and_load_image(self):
        # Make sure image is present
        self.docker_image.client.images.pull(self.repo, self.tag)

        archive_path = self.docker_image.package_image(self.repo, self.tag, self.output_dir)
        self.assertTrue(os.path.exists(archive_path))
        self.assertTrue(archive_path.endswith(f"/{self.repo}.{self.tag}.tar.gz"))
        self.assertEqual(self.get_file_sha256(archive_path), self.archive_hash)

        # Remove image locally
        self.docker_image.client.images.remove(f"{self.repo}:{self.tag}", force=True)
        self.assertFalse(self.docker_image.image_exists_locally(self.repo, self.tag))

        # Load it back
        self.docker_image.load_image(archive_path)
        self.assertTrue(self.docker_image.image_exists_locally(self.repo, self.tag))


if __name__ == '__main__':
    unittest.main()
