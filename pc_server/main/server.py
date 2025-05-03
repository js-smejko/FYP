###
# Serves data to the web
###

import threading
from flask import Flask, send_from_directory, abort
from flask_cors import CORS
import os
import asyncio
import threading
import json
import websockets
from queue import Queue

# Point to where the HLS files are stored
HLS_DIR = r"C:\Development\Project\var\www\html"

app = Flask(__name__)
CORS(app)

# Route all incoming file get requests to the HLS directory.
@app.route('/<path:filename>')
def serve_hls(filename: str):
    filepath = os.path.join(HLS_DIR, filename)
    if os.path.exists(filepath):
        if filename.endswith('.m3u8'):
            # Ensure that the correct MIME type is used for HLS playlists
            return send_from_directory(HLS_DIR, filename, mimetype='application/vnd.apple.mpegurl')
        elif filename.endswith('.ts'):
            return send_from_directory(HLS_DIR, filename, mimetype='video/MP2T')
        else:
            return send_from_directory(HLS_DIR, filename)
    else:
        return abort(404)
    
class WebSocketServer:
    """
    Interfaces asynchronous websockets in a parallelised synchronous context.
    """
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.data_queue = Queue()

    async def broadcaster(self):
        """
        Continuously checks the data queue for new data and sends it to all connected clients.
        """
        while True:
            if not self.data_queue.empty():
                data = self.data_queue.get()
                disconnected_clients = set()
                clients = list(self.clients)

                for client in clients:
                    try:
                        await client.send(data)
                    except websockets.exceptions.ConnectionClosed:
                        # Don't change the set size while iterating over it
                        disconnected_clients.add(client)

                self.clients.difference_update(disconnected_clients)
            # Ensure the thread doesn't get completely consumed
            await asyncio.sleep(0.01)

    async def handler(self, websocket):
        """
        Handles incoming websocket connections by adding them to the set of clients.
        """
        self.clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")

    async def run(self):
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await self.broadcaster()

    def send_data(self, data):
        """
        Puts data into the queue to be sent to all connected clients.
        """
        self.data_queue.put(json.dumps(data))

    def start(self):
        """
        Asynchronously starts the websocket server in a separate thread.
        """
        threading.Thread(target=lambda: asyncio.run(self.run()), daemon=True).start()