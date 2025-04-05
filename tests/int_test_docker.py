import os
import unittest
import tempfile
import shutil
from docker.errors import ImageNotFound

from fairops.devops.container import DockerImage


class TestDockerImageIntegration(unittest.TestCase):
    def setUp(self):
        self.docker_image = DockerImage()
        self.repo = "alpine"
        self.tag = "3.20"
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

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

        # Remove image locally
        self.docker_image.client.images.remove(f"{self.repo}:{self.tag}", force=True)
        self.assertFalse(self.docker_image.image_exists_locally(self.repo, self.tag))

        # Load it back
        self.docker_image.load_image(archive_path)
        self.assertTrue(self.docker_image.image_exists_locally(self.repo, self.tag))


if __name__ == '__main__':
    unittest.main()
