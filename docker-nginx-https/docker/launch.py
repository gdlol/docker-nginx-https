import json
import os
import socket
import subprocess
import sys
import docker


def run(*cmd):
    subprocess.run(cmd, check=True)


def container_run(container, cmd):
    (exit_code, output) = container.exec_run(cmd)
    print(output.decode("utf-8"), end="")
    if exit_code != 0:
        sys.exit(exit_code)


# Load configurations.
with open("/root/docker/config.json") as file:
    config = json.load(file)
data_path = config["data_path"]
container_prefix = config["container_prefix"]
domain_name = config["domain_name"]
email = config["email"]
nginx_image_name = config["nginx_image_name"]
certbot_image_name = config["certbot_image_name"]

# Populate directory structure in the data directory.
nginx_data_path = "/root/https/nginx"
nginx_config_path = os.path.join(nginx_data_path, "conf.d")
nginx_webroot_path = os.path.join(nginx_data_path, "webroot")
certbot_data_path = "/root/https/certbot"
run("mkdir", "-p", nginx_data_path)
run("mkdir", "-p", nginx_config_path)
run("mkdir", "-p", nginx_webroot_path)
run("mkdir", "-p", certbot_data_path)

# Copy Nginx configurations.
nginx_default_config_path = os.path.join(nginx_config_path, "nginx.conf")
nginx_http_config_path = os.path.join(nginx_config_path, "http.conf")
nginx_https_config_path = os.path.join(nginx_config_path, "https.conf")
with open(nginx_default_config_path, "w") as file:
    file.write("include /root/nginx/conf.d/http.conf;\n")
if not os.path.exists(nginx_http_config_path):
    run("cp", "/root/docker/http.conf", nginx_http_config_path)
if not os.path.exists(nginx_https_config_path):
    run("cp", "/root/docker/https.conf", nginx_https_config_path)

# Remove existing containers.
client = docker.from_env()
nginx_container_name = container_prefix + "nginx"
renew_container_name = container_prefix + "renew"
for container in client.containers.list():
    if container.name in [nginx_container_name, renew_container_name]:
        container.remove(v=True, force=True)

# Create HTTP Nginx container.
print(f"Running {nginx_image_name}.")
host_nginx_config_path = os.path.join(data_path, "nginx", "conf.d")
host_nginx_webroot_path = os.path.join(data_path, "nginx", "webroot")
host_certbot_data_path = os.path.join(data_path, "certbot")
nginx_container = client.containers.run(
    nginx_image_name,
    entrypoint="nginx",
    command=["-c", "/root/nginx/conf.d/nginx.conf",
             "-g", "daemon off;"],
    detach=True,
    network="host",
    name=nginx_container_name,
    restart_policy={"Name": "always",
                    "MaximumRetryCount": 0},
    stream=True,
    volumes={host_nginx_config_path: {"bind": "/root/nginx/conf.d",
                                      "mode": "rw"},
             host_nginx_webroot_path: {"bind": "/var/www",
                                       "mode": "rw"},
             host_certbot_data_path: {"bind": "/etc/letsencrypt",
                                      "mode": "rw"}})

# Run certbot to obtain certificates.
print(f"Running {certbot_image_name}.")
certbot_container = client.containers.run(
    certbot_image_name,
    detach=True,
    volumes={host_nginx_webroot_path: {"bind": "/var/www",
                                       "mode": "rw"},
             host_certbot_data_path: {"bind": "/etc/letsencrypt",
                                      "mode": "rw"}},
    command=["certonly",
             "--webroot",
             "--non-interactive",
             "--domain", domain_name,
             "--agree-tos",
             "--email", email,
             "--no-eff-email",
             "--webroot-path", "/var/www"])
for line in certbot_container.logs(stream=True):
    print(line.decode("utf-8"), end="")
status = certbot_container.wait()["StatusCode"]
certbot_container.remove(v=True, force=True)
if status != 0:
    sys.exit(status)

# Create symbolic links to certificate files and reload nginx.
container_run(nginx_container, ["mkdir", "-p", "/root/nginx/ssl"])
for file_name in ["fullchain.pem", "privkey.pem", "chain.pem"]:
    cmd = ["ln", "-sf",
           f"/etc/letsencrypt/live/{domain_name}/{file_name}",
           f"/root/nginx/ssl/{file_name}"]
    container_run(nginx_container, cmd)
with open(nginx_default_config_path, "w") as file:
    file.write("include /root/nginx/conf.d/https.conf;\n")
container_run(nginx_container, ["nginx", "-s", "reload"])

# Run renew.py using the current image.
hostname = socket.gethostname()
current_container = client.containers.get(hostname)
client.containers.run(
    current_container.image.id,
    command=["python", "-u", "/root/docker/renew.py"],
    detach=True,
    name=renew_container_name,
    restart_policy={"Name": "always",
                    "MaximumRetryCount": 0},
    volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock",
                                      "mode": "rw"}})

print("Done.")
