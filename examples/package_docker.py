from fairops.devops.container import DockerImage
import hashlib


def get_file_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


docker_image = DockerImage()
archive_path = docker_image.package_image("alpine", "3.20", "data/images")

print("SHA-256:", get_file_sha256(archive_path))
