# docker-nginx-https
This image runs a Python script to:
1. Launch a Nginx container
2. Run Certbot to obtain HTTPS certificates from Let's Encrypt
3. Configure Nginx to use HTTPS
4. Schedule periodic certificate renewal

## Example
### Create a configuration file `config.json`
```JSON
{
    "container_prefix": "https-",
    "data_path": "/root/https",
    "domain_name": "www.example.com",
    "email": "test@example.com",
    "nginx_image_name": "nginx:1.17.3",
    "certbot_image_name": "certbot/certbot:v0.38.0"
}
```

### Optionally, pull the images to be used
```
docker pull nginx:1.17.3
docker pull certbot/certbot:v0.38.0
```

### Launch containers
```
docker create --name https --rm --volume /var/run/docker.sock:/var/run/docker.sock v2net/nginx-https
docker cp ./config.json https:/root/docker/
docker start --attach https
```

### Customize Nginx configuration
Modify the file `nginx/conf.d/https.conf` under `data_path`, and reload Nginx:
```
docker exec https-nginx nginx -s reload
```

## Build
```
docker pull v2net/nginx-https:build
docker create --name nginx-https-build v2net/nginx-https:build
docker cp nginx-https-build:/root/source/ ./nginx-https
docker rm nginx-https-build
docker build --tag v2net/nginx-https ./nginx-https/
```
