FROM python:3.7.4-alpine3.10
COPY ./requirements.txt /tmp/
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt
COPY ./docker/ /root/docker/
CMD ["python", "-u", "/root/docker/main.py"]
