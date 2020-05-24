import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import time

import docker

client = docker.from_env()
api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
hostname = socket.gethostname()
current_container = client.containers.get(hostname)


def run(*cmd):
    subprocess.run(cmd, check=True)


# Populate directory structure in the data directory.
nginx_data_path = "/root/https/nginx"
nginx_config_path = os.path.join(nginx_data_path, "conf.d")
nginx_webroot_path = os.path.join(nginx_data_path, "webroot")
certbot_data_path = "/root/https/certbot"
logs_path = "root/https/logs"
run("mkdir", "-p", nginx_data_path)
run("mkdir", "-p", nginx_config_path)
run("mkdir", "-p", nginx_webroot_path)
run("mkdir", "-p", certbot_data_path)
run("mkdir", "-p", logs_path)

# Get logger
log_file_path = os.path.join(logs_path, "logs.txt")
logging.basicConfig(level=logging.INFO,
                    handlers=[logging.FileHandler(log_file_path, mode="w"),
                              logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("https")


def container_run(container, cmd):
    (exit_code, output) = container.exec_run(cmd)
    logger.info(output.decode("utf-8").rstrip())
    if exit_code != 0:
        sys.exit(exit_code)


# Load configurations.
with open("/root/docker/config.json") as file:
    config = json.load(file)
data_path = config["data_path"]
network_name = config["network_name"]
container_prefix = config["container_prefix"]
domain_name = config["domain_name"]
email = config["email"]
nginx_image_name = config["nginx_image_name"]
certbot_image_name = config["certbot_image_name"]

# Copy Nginx configurations.
nginx_default_config_path = os.path.join(nginx_config_path, "nginx.conf")
nginx_http_config_path = os.path.join(nginx_config_path, "http.conf")
nginx_https_config_path = os.path.join(nginx_config_path, "https.conf")
with open(nginx_default_config_path, "w") as file:
    file.write("include /root/nginx/conf.d/http.conf;\n")
run("cp", "/root/docker/http.conf", nginx_http_config_path)
if not os.path.exists(nginx_https_config_path):
    run("cp", "/root/docker/https.conf", nginx_https_config_path)

# Pull images
logger.info(f"Pulling {nginx_image_name}:")
for line in api_client.pull(nginx_image_name, stream=True, decode=True):
    logger.info(json.dumps(line, indent=4))
logger.info(f"Pulling {certbot_image_name}:")
for line in api_client.pull(certbot_image_name, stream=True, decode=True):
    logger.info(json.dumps(line, indent=4))

# Remove existing containers.
web_container_name = container_prefix + "web"
nginx_container_name = container_prefix + "nginx"
renew_container_name = container_prefix + "renew"
for container_name in [web_container_name,
                       nginx_container_name,
                       renew_container_name]:
    containers = client.containers.list(filters={"name": container_name})
    for container in containers:
        logger.info(f"Removing {container_name}")
        container.remove(v=True, force=True)

# Create network
if not client.networks.list(names=[network_name]):
    client.networks.create(network_name)

# Create HTTP Nginx container.
if not domain_name:
    domain_name_file_path = os.path.join(logs_path, "domain_name.txt")
    if os.path.exists(domain_name_file_path):
        with open(domain_name_file_path, "r") as domain_name_file:
            domain_name = domain_name_file.read().strip()
if not domain_name:
    domain_name_file = open(domain_name_file_path, "w")
    domain_name_file.close()
    shutil.copytree("/root/web/root",
                    nginx_webroot_path,
                    dirs_exist_ok=True)
    run("cp", "/root/web/nginx/http.conf", nginx_http_config_path)
    web = api_client.create_container(
        current_container.image.id,
        command=["python", "-u", "/root/web/server/main.py"],
        detach=True,
        host_config=api_client.create_host_config(
            binds={data_path: {"bind": "/root/https/",
                               "mode": "rw"}}),
        name=web_container_name,
        networking_config=api_client.create_networking_config({
            network_name: api_client.create_endpoint_config(aliases=[
                                                            "web"])
        }),
        volumes=["/root/https/"])
    api_client.start(container=web.get('Id'))
logger.info(f"Running {nginx_image_name}.")
host_nginx_config_path = os.path.join(data_path, "nginx", "conf.d")
host_nginx_webroot_path = os.path.join(data_path, "nginx", "webroot")
host_certbot_data_path = os.path.join(data_path, "certbot")
nginx_container = client.containers.run(
    nginx_image_name,
    entrypoint="nginx",
    command=["-c", "/root/nginx/conf.d/nginx.conf",
             "-g", "daemon off;"],
    detach=True,
    links={web_container_name: "web"},
    name=nginx_container_name,
    network=network_name,
    ports={80: 80,
           443: 443},
    restart_policy={"Name": "always",
                    "MaximumRetryCount": 0},
    stream=True,
    volumes={host_nginx_config_path: {"bind": "/root/nginx/conf.d",
                                      "mode": "rw"},
             host_nginx_webroot_path: {"bind": "/var/www",
                                       "mode": "rw"},
             host_certbot_data_path: {"bind": "/etc/letsencrypt",
                                      "mode": "rw"}})
if not domain_name:
    logger.info("Waiting web request (enter domain name in browser).")
    domain_name_file = open(domain_name_file_path, "r")
    while True:
        line = domain_name_file.readline()
        if line:
            domain_name = line.strip()
            break
        else:
            time.sleep(0.01)

# Run certbot to obtain certificates.
logger.info(f"Running {certbot_image_name}.")
if email:
    email_options = ["--email", email]
else:
    email_options = ["--register-unsafely-without-email"]
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
             *email_options,
             "--no-eff-email",
             "--webroot-path", "/var/www"])
for line in certbot_container.logs(stream=True):
    logger.info(line.decode("utf-8").rstrip())
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
client.containers.run(
    current_container.image.id,
    command=["python", "-u", "/root/docker/renew.py"],
    detach=True,
    name=renew_container_name,
    restart_policy={"Name": "always",
                    "MaximumRetryCount": 0},
    volumes={data_path: {"bind": "/root/https",
                         "mode": "rw"},
             "/var/run/docker.sock": {"bind": "/var/run/docker.sock",
                                      "mode": "rw"}})

containers = client.containers.list(filters={"name": web_container_name})
for container in containers:
    container.remove(v=True, force=True)

logger.info("Done.")
