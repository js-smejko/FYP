###
# Send images of choice to "host" program for testing
# Change "host" to use zmq_capture.py for capture class
###

import os
import cv2
import zmq

context = zmq.Context()
sockets = [context.socket(zmq.PUB) for _ in range(2)]
for i, socket in enumerate(sockets):
    socket.bind(f"tcp://*:555{5 + i}")

dir = r"C:\Development\Project\video_blank"
iteration = 0

for image_file in os.listdir(dir):
    image_path = os.path.join(dir, image_file)
    if os.path.isfile(image_path):
        frame = cv2.imread(image_path)
        _, buffer = cv2.imencode('.jpg', frame)
        # Oscillate between port 5555 and 5556
        sockets[iteration].send(buffer.tobytes())
        # Send both perspectives before delay
        if iteration == 1:
            cv2.waitKey(1000)
        iteration = (iteration + 1) % 2