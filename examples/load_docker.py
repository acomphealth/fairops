from fairops.devops.container import DockerImage


docker_image = DockerImage()
docker_image.load_image("data/images/alpine.3.20.tar.gz")
