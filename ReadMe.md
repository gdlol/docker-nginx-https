# docker-nginx-https
This image runs a Python script to:
1. Launch a Nginx container
2. Run Certbot to obtain HTTPS certificates from Let's Encrypt
3. Configure Nginx to use HTTPS
4. Schedule periodic certificate renewal

## Example
### 1. Launch container:
```
docker run --rm --volume /var/run/docker.sock:/var/run/docker.sock v2net/nginx-https
```
### 2. Enter domain name in browser.

## Notes

### Build
```
docker build --force-rm --tag v2net/nginx-https .
```

### Customize config.json
```
docker run \
    --rm \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /root/https/config.json:/root/docker/config.json \
    v2net/nginx-https
```

### Customize Nginx configuration
Modify the file `nginx/conf.d/https.conf` under `/root/https/`, and reload Nginx:
```
docker exec https-nginx nginx -s reload
```
