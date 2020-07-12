FROM node:14.5.0-stretch AS build
COPY ./web/client/package.json /root/web/client/
WORKDIR /root/web/client/
RUN npm install
COPY ./web/ /root/web/
RUN npm run build

FROM scratch AS files
COPY ./docker/ /root/docker/
COPY --from=build /root/web/nginx/ /root/web/nginx/
COPY --from=build /root/web/server/ /root/web/server/
COPY --from=build /root/web/root/ /root/web/root/

FROM python:3.8.3-alpine3.12
COPY ./requirements/requirements.txt /tmp/
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt
COPY --from=files /root/ /root/
CMD ["python", "-u", "/root/docker/main.py"]
