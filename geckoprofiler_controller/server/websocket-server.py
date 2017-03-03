#!/usr/bin/env python
"""
This websocket-server will start a Web Socket server
for listening the connections from Gecko-Profiler Add-on and Python client.
The Gecko-Profiler Add-on will wait for commands from this server, while the commands come from Python client.
"""

import json
import thread
import logging
from tornado import websocket, web, ioloop

import commands


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

server = None
addon_clients = []
py_clients = []


class AddonSocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in addon_clients:
            logger.info('[WebSocket] a Add-on client connected.')
            addon_clients.append(self)

    def on_close(self):
        if self in addon_clients:
            logger.info('[WebSocket] a Add-on client disconnected.')
            addon_clients.remove(self)

    def on_message(self, message):
        input_data = json.loads(message)
        logger.info('[WebSocket] AddonSocketHandler get: {}'.format(input_data))
        if commands.KEY_NAME in input_data \
                and commands.KEY_DATA in input_data:
            for client in py_clients:
                client.write_message(input_data)


class PythonSocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in py_clients:
            logger.info('[WebSocket] a Python client connected.')
            py_clients.append(self)

    def on_close(self):
        if self in py_clients:
            logger.info('[WebSocket] a Python client disconnected.')
            py_clients.remove(self)

    def on_message(self, message):
        input_data = json.loads(message)
        logger.info('[WebSocket] PythonSocketHandler get: {}'.format(input_data))

        if input_data.get(commands.KEY_NAME, '').lower() == commands.VALUE_STOP:
            logger.info('[WebSocket] Stopping Server ...')
            for client in addon_clients:
                client.close()
            for client in py_clients:
                client.close()
            thread.start_new_thread(stop_server, (server,))
            logger.info('[WebSocket] Server stopped!')
            return

        if commands.KEY_NAME in input_data \
                and commands.KEY_DATA in input_data:
            for client in addon_clients:
                client.write_message(input_data)

app = web.Application([
    (r'/addon', AddonSocketHandler),
    (r'/py', PythonSocketHandler),
])


def stop_server(server_handler):
    server_handler.stop()


if __name__ == '__main__':
    app.listen(8888)
    logger.info('[WebSocket] Server is listening on port 8888 ...')
    server = ioloop.IOLoop.instance()
    server.start()
