import json
import socket

import docker


client = docker.from_env()

config_file_path = "/root/docker/config.json"
with open(config_file_path) as file:
    config = json.load(file)
    print("Configuration:")
    print(json.dumps(config, indent=4))
container_prefix = config["container_prefix"]
data_path = config["data_path"]

# Remove existing containers.
launch_container_name = container_prefix + "launch"
containers = client.containers.list(all=True,
                                    filters={"name": launch_container_name})
for container in containers:
    print(f"Removing {launch_container_name}")
    container.remove(v=True, force=True)

# Run launch.py using current image, with the configured data path mounted.
hostname = socket.gethostname()
current_container = client.containers.get(hostname)
current_image = current_container.commit()
launch = client.containers.run(
    current_image.id,
    command=["python", "-u", "/root/docker/launch.py"],
    detach=True,
    name=launch_container_name,
    volumes={data_path: {"bind": "/root/https",
                         "mode": "rw"},
             "/var/run/docker.sock": {"bind": "/var/run/docker.sock",
                                      "mode": "rw"}})
for line in launch.logs(stream=True):
    print(line.decode("utf-8"), end="")
launch.remove(v=True, force=True)
