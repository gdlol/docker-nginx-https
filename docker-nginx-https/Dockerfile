FROM node:lts AS build
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

FROM python:3
RUN pip install --no-cache-dir docker websockets
COPY --from=files /root/ /root/
CMD ["python", "-u", "/root/docker/main.py"]
