import docker
import os


# TODO: Add documentation
class DockerImage:
    def __init__(self):
        self.client = docker.from_env()

    def package_image(self, repository, tag, output_path, remote=False):
        # TODO: Add error handling
        if remote:
            self.client.images.pull(repository, tag)

        image = self.client.images.get(f"{repository}:{tag}")
        os.makedirs(output_path, exist_ok=True)

        archive_file = os.path.join(output_path, f"{repository}.{tag}.tar.gz")

        # Save the image as a tar archive
        with open(archive_file, 'wb') as f:
            for chunk in image.save(named=True):  # `named=True` ensures tag info is preserved
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
