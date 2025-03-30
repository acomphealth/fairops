from fairops.devops.container import DockerImage


docker_image = DockerImage()
docker_image.package_image("nginx", "latest", "data/images")
