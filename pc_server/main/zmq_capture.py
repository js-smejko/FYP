import threading
from typing import List
import zmq
import numpy as np
import cv2

class Poller(threading.Thread):
    """
    Base class for a parallelised ZMQ subscriber that polls for messages.
    """
    def __init__(self, zmq_address):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(zmq_address)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self._latest_data = None
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._latest_data = self.socket.recv()
            except zmq.Again:
                continue

    def stop(self):
        self._stop_event.set()
        self.socket.close()
        self.context.term()

class StreamTracker(Poller):
    """
    Poller specialisation for video streams
    """
    def __init__(self, zmq_address, resolution=(2048, 2048)):
        super().__init__(zmq_address)
        w, h = resolution
        self.socket.setsockopt(zmq.RCVBUF, w*h*3)
        self.socket.setsockopt(zmq.CONFLATE, 1)

    def get_latest_image(self):
        if self._latest_data is None:
            return None
        
        np_array = np.frombuffer(self._latest_data, dtype=np.uint8)
        return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

class LatestResults:
    """
    Accumulates the latest results from multiple streams.
    """
    def __init__(self, addresses: List[str], resolution=(2048, 2048)):
        self.pollers = [StreamTracker(address, resolution) for address in addresses]

    def start(self):
        for poller in self.pollers:
            poller.start()

    def __call__(self):
        return [poller.get_latest_image() for poller in self.pollers]
    
    def stop(self):
        for poller in self.pollers:
            poller.stop()