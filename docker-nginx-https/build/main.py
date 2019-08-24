import subprocess

subprocess.run(["pip", "install", "docker"], check=True)
requirements = subprocess.check_output(["pip", "freeze"])
with open("/root/source/requirements.txt", "wb") as file:
    file.write(requirements)
