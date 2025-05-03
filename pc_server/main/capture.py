import threading
import cv2
    
class StreamTracker(threading.Thread):
    """
    Uses GStreamer to read a video stream from a UDP port, storing only the latest frame.
    """
    def __init__(self, port):
        super().__init__()
        self.cap = cv2.VideoCapture()
        self.port = port
        self._stop_event = threading.Event()
        self.latest_data = None
        
    def run(self):
        pipeline = (
            # Uncomment to use H.264
            f'udpsrc port={self.port} caps="application/x-rtp, encoding-name=H264, payload=96" ! rtph264depay ! avdec_h264 ! videoconvert ! appsink'
            # Uncomment to use JPEG
            # f"udpsrc port={self.port} ! application/x-rtp, encoding-name=JPEG ! "
            # "rtpjpegdepay ! jpegdec ! videoconvert ! queue ! appsink"
            )

        if not self.cap.open(pipeline, cv2.CAP_GSTREAMER):
            print("Error opening video stream or file")
            return
        
        while not self._stop_event.is_set():
            ret, frame = self.cap.read()
            if ret:
                self.latest_data = frame

    def stop(self):
        self._stop_event.set()
        self.cap.release()
        cv2.destroyAllWindows()
    
class LatestResults:
    """
    Accumulates the latest results from multiple streams.
    """
    def __init__(self):
        self.pollers = [StreamTracker(5000 + i) for i in range(2)]

    def start(self):
        for poller in self.pollers:
            poller.start()

    def __call__(self):
        return [poller.latest_data for poller in self.pollers]
    
    def stop(self):
        for poller in self.pollers:
            poller.stop()    