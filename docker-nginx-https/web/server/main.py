import asyncio
import os

import websockets

nginx_data_path = "/root/https/nginx"
nginx_webroot_path = os.path.join(nginx_data_path, "webroot")
logs_path = "root/https/logs"
log_file_path = os.path.join(logs_path, "logs.txt")
domain_name_file_path = os.path.join(logs_path, "domain_name.txt")


async def test(websocket, path):
    domain_name = os.path.split(path)[-1]
    with open(domain_name_file_path, "w") as file:
        file.writelines([domain_name])
    with open(log_file_path, "r") as log_file:
        while True:
            line = log_file.readline()
            if line:
                await websocket.send(line.strip())
            else:
                await asyncio.sleep(1)


start_server = websockets.serve(test, "0.0.0.0", 80)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
