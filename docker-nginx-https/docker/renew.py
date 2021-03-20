import datetime
import json
import logging
import os
import sched
import sys

import docker

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("renew_cert")

# Load configurations.
config_file_path = "/root/https/config.json"
if not os.path.exists(config_file_path):
    config_file_path = "/root/docker/config.json"
with open(config_file_path) as file:
    config = json.load(file)
data_path = config["data_path"]
container_prefix = config["container_prefix"]
domain_name = config["domain_name"]
email = config["email"]
certbot_image_name = config["certbot_image_name"]
if not domain_name:
    logs_path = "root/https/logs"
    domain_name_file_path = os.path.join(logs_path, "domain_name.txt")
    with open(domain_name_file_path, "r") as domain_name_file:
        domain_name = domain_name_file.read().strip()

certbot_container_name = container_prefix + "certbot"

host_nginx_webroot_path = os.path.join(data_path, "nginx", "webroot")
host_certbot_data_path = os.path.join(data_path, "certbot")

scheduler = sched.scheduler()
day_seconds = int(datetime.timedelta(days=1).total_seconds())
week_seconds = int(datetime.timedelta(weeks=1).total_seconds())


def remove_certbot_container(client: docker.DockerClient):
    containers = client.containers.list(
        all=True,
        filters={"name": certbot_container_name})
    for container in containers:
        print(f"Removing {certbot_container_name}")
        container.remove(v=True, force=True)


def log_time_daily():
    scheduler.enter(day_seconds, 0, log_time_daily)
    logger.info(datetime.datetime.now())


def renew_cert():
    scheduler.enter(week_seconds, 0, renew_cert)
    try:
        client = docker.from_env()
        logger.info("Renew certificate:")
        remove_certbot_container(client)
        if email:
            email_options = ["--email", email]
        else:
            email_options = ["--register-unsafely-without-email"]
        logs = client.containers.run(
            certbot_image_name,
            name=certbot_container_name,
            remove=True,
            stream=True,
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
        for line in logs:
            print(line.decode("utf-8"), end="")
        logger.info("Reload Nginx:")
        nginx_container = client.containers.get(container_prefix + "nginx")
        (_, logs) = nginx_container.exec_run(cmd=["nginx", "-s", "reload"],
                                             stream=True)
        for line in logs:
            print(line.decode("utf-8"), end="")
    except Exception:
        logger.exception("Error renewing certificate:")
    finally:
        remove_certbot_container(client)


scheduler.enter(0, 0, log_time_daily)
scheduler.enter(0, 0, renew_cert)
scheduler.run()
