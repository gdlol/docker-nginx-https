import json
import os
import socket
import docker

config_file_path = "/root/docker/config.json"
if not os.path.exists(config_file_path):
    raise RuntimeError(config_file_path)

# Load configurations.
with open(config_file_path) as file:
    config = json.load(file)
    print(json.dumps(config, indent=4))
data_path = config["data_path"]

# Get current container.
client = docker.from_env()
hostname = socket.gethostname()
current_container = client.containers.get(hostname)

# Run launch.py using the current image, with the configured data path mounted.
current_image = current_container.commit()
launch = client.containers.run(
    current_image.id,
    command=["python", "-u", "/root/docker/launch.py"],
    detach=True,
    volumes={data_path: {"bind": "/root/https",
                         "mode": "rw"},
             "/var/run/docker.sock": {"bind": "/var/run/docker.sock",
                                      "mode": "rw"}})
for line in launch.logs(stream=True):
    print(line.decode("utf-8"), end="")
launch.remove(v=True, force=True)
