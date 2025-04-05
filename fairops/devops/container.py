import os

import docker
import docker.errors


# TODO: Add documentation
class DockerImage:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except docker.errors.DockerException as e:
            raise RuntimeError(
                "Docker is not available. Please ensure Docker is installed and the daemon is running."
            ) from e

    def image_exists_locally(self, repository: str, tag: str) -> bool:
        image_name = f"{repository}:{tag}"
        try:
            self.client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def package_image(self, repository, tag, output_path):
        if not self.image_exists_locally(repository, tag):
            self.client.images.pull(repository, tag)

        image = self.client.images.get(f"{repository}:{tag}")
        os.makedirs(output_path, exist_ok=True)

        archive_file = os.path.join(output_path, f"{repository}.{tag}.tar.gz")

        # Save the image as a tar archive
        with open(archive_file, 'wb') as f:
            for chunk in image.save(named=True):  # named=True ensures tag info is preserved
                f.write(chunk)

        return archive_file

    def load_image(self, archive_path):
        if not os.path.exists(archive_path):
            raise Exception(f"Archive not found: {archive_path}")

        # TODO: Add error handling
        with open(archive_path, 'rb') as f:
            images = self.client.images.load(f.read())

        for image in images:
            if len(image.tags) > 0:
                print(f"Loaded image: {image.tags[0]}")
            else:
                print(f"Loaded image: {image.id}")
