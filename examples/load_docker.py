from fairops.devops.container import DockerImage


docker_image = DockerImage()
docker_image.load_image("data/images/nginx.latest.tar.gz")
