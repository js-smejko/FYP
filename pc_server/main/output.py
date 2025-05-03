###
# A collection of debugging utilities
###

import threading
import numpy as np
import cv2
from typing import List, Tuple
from matplotlib import pyplot as plt
import queue
import time

def show_tracks(images, track=None):
    """
    Writes 2D tracks onto frames and displays them.
    """
    if images is None:
        return

    if track is not None:
        points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(images[0], [points], False, (0, 255, 0), 2)

    for i, image in enumerate(images):
        # resized = cv2.resize(image, (640, 480))
        cv2.imshow(f"Camera {i}", image)

def plot(last_audio_time, location, time_spec, freq_spec):
    """
    2D plotting for audio data
    """
    if last_audio_time is None or location is None or time_spec is None or freq_spec is None:
        return
    
    plt.ion()
    plt.clf()
    
    plt.subplot(2, 1, 1)
    plt.plot(time_spec[0], time_spec[1])
    plt.title("Original Signal")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")

    plt.subplot(2, 1, 2)
    plt.plot(freq_spec[0], freq_spec[1])
    plt.title("FFT of the Signal")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude")
    plt.tight_layout()

    print(f"Location: x: {location[0]}, y: {location[1]}, z: {location[2]} at time {last_audio_time}")
    plt.show()

class Visualise3D:
    """
    3D Scatter graph. Beware: Matplotlib insists on using the main thread and is slow.
    """
    def __init__(self, resolution):
        width, height = resolution
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        plt.ion()
        self.width = width
        self.height = height

    def __call__(self, x, y, z):
        self.ax.clear()
        self.ax.scatter(x, z, self.height-y, c=y, cmap='viridis')

        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')

        self.ax.set_xlim(0, self.width)
        self.ax.set_ylim(0, self.height)
        self.ax.set_zlim(0, self.height)

        plt.draw()
        plt.pause(0.001)

class Trackbars:
    """
    Makes the creation of trackbars easier.
    """
    def __init__(self, window_name: str, trackbars: List[Tuple[str, int]]):
        self.window_name = window_name
        self.trackbars = trackbars

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 240, 120)

        for name, limit in trackbars:
            cv2.createTrackbar(name, window_name, 0, max(1, limit), self._callback)

    def _callback(self, value):
        pass

    def __getitem__(self, trackbar: str):
        return cv2.getTrackbarPos(trackbar, self.window_name)

class ImageWriter:
    """
    Creates unannotated datasets from video stream by saving images at a specified interval.
    """
    def __init__(self, interval: int, max_writes: int):
        self.interval = interval
        self.max_writes = max_writes
        self.write_count = 0
        self.timer = None
        self.lock = threading.Lock()

    def _queue_image(self, image):
        with self.lock:
            cv2.imwrite(fr"C:\Development\Project\no_annotation\img{self.write_count}.jpg", image)
            print(f"Writing image {self.write_count}")
            self.write_count = (self.write_count + 1) % self.max_writes
            self.timer = None

    def offer_for_write(self, image):
        if self.timer is None:
            self.timer = threading.Timer(self.interval, self._queue_image, args=(image,))
            self.timer.start()

class MultiImageWriter(ImageWriter):
    """
    Creates unannotated datasets from video stream by saving images at a specified interval.
    Synchronises canon frames in the resulting dataset.
    """
    def __init__(self, interval: int, max_writes: int):
        super().__init__(interval, max_writes)

    def _queue_image(self, images: List[cv2.Mat]):
        with self.lock:
            for i, image in enumerate(images):
                cv2.imwrite(fr"C:\Development\Project\video\output{self.write_count}_{i}.jpg", image)
            self.write_count = (self.write_count + 1) % self.max_writes
            self.timer = None

class HLSEncoder(threading.Thread):
    """
    Encodes video streams using GStreamer and saves them as HLS segments.
    """
    def __init__(self, resolution, dir):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue()

        gst_pipeline = (
            'appsrc ! videoconvert ! x264enc ! h264parse ! mpegtsmux ! '
            f'hlssink location={dir}/segment_%05d.ts '
            f'playlist-location={dir}/playlist.m3u8 '
            'target-duration=4 max-files=15 playlist-length=15'
        )

        self.video_out = cv2.VideoWriter(
            gst_pipeline,
            cv2.CAP_GSTREAMER,
            0,  # FourCC ignored when using GStreamer
            20,
            resolution,
            True
        )

    def run(self):
        if not self.video_out.isOpened():
            print("Error opening video stream or file")
            return
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.1)
                if frame is not None:
                    self.video_out.write(frame)
            except queue.Empty:
                continue
    
    def push_frame(self, frame):
        if not self.stop_event.is_set():
            self.frame_queue.put(frame)

    def stop(self):
        self.stop_event.set()
        self.video_out.release()
        cv2.destroyAllWindows()

class FPSCounter:
    """
    Monitors the average frames per second (FPS) of a dual camera setup.
    """
    def __init__(self):
        self.start_time = None
        self.iterations = 0
        self.prev_frames = [None, None]

    def update(self, frames: List[cv2.Mat]):
        if all(frame is None for frame in self.prev_frames) or self.start_time is None:
            self.start_time = time.time()
        else:
            self.iterations += sum(not np.array_equal(plot, prev_frame) for plot, prev_frame in zip(frames, self.prev_frames))

        self.prev_frames = frames
    
    def show_fps(self):
        if self.prev_frames[0] is None:
            return
        now = time.time()
        fps = self.iterations / ((now - self.start_time) * 2 + 0.001)
        print(f"FPS: {fps:.2f}, Resolution: {self.prev_frames[0].shape[1]}x{self.prev_frames[0].shape[0]}")

    def show_prev_frames(self):
        for i, frame in enumerate(self.prev_frames):
            if frame is not None:
                plot = cv2.resize(frame, (640, 640))
                cv2.imshow(f"Previous Frame {i}", plot)