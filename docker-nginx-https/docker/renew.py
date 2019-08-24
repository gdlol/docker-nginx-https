import datetime
import json
import os
import sched
import sys
import docker


# Load configurations.
with open("/root/docker/config.json") as file:
    config = json.load(file)
data_path = config["data_path"]
container_prefix = config["container_prefix"]
domain_name = config["domain_name"]
email = config["email"]
certbot_image_name = config["certbot_image_name"]

host_nginx_webroot_path = os.path.join(data_path, "nginx", "webroot")
host_certbot_data_path = os.path.join(data_path, "certbot")

scheduler = sched.scheduler()
day_seconds = int(datetime.timedelta(days=1).total_seconds())
week_seconds = int(datetime.timedelta(weeks=1).total_seconds())


def log_time_daily():
    scheduler.enter(day_seconds, 0, log_time_daily)
    print(datetime.datetime.now())


def renew_cert():
    scheduler.enter(week_seconds, 0, renew_cert)
    client = docker.from_env()
    print("Renew Certificate:")
    logs = client.containers.run(
        certbot_image_name,
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
                 "--email", email,
                 "--no-eff-email",
                 "--webroot-path", "/var/www"])
    for line in logs:
        sys.stdout.write(line.decode("utf-8"))
    print("Reload Nginx:")
    nginx_container = client.containers.get(container_prefix + "nginx")
    (_, logs) = nginx_container.exec_run(cmd=["nginx", "-s", "reload"],
                                         stream=True)
    for line in logs:
        sys.stdout.write(line.decode("utf-8"))


scheduler.enter(0, 0, log_time_daily)
scheduler.enter(0, 0, renew_cert)
scheduler.run()
