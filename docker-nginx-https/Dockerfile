FROM python:3.7.4-alpine3.10
COPY ./docker/ /root/docker/
COPY ./requirements.txt /tmp/
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt
CMD ["python", "-u", "/root/docker/main.py"]
