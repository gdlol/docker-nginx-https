import subprocess

subprocess.run(["pip", "install", "docker"], check=True)
subprocess.run(["pip", "install", "websockets"], check=True)
requirements = subprocess.check_output(["pip", "freeze"])
with open("/root/requirements.txt", "wb") as file:
    file.write(requirements)
