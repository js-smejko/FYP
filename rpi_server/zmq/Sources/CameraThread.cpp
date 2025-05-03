#include "CameraThread.h"

int CameraThread::cameraCount = 0;

/// @brief Launches a camera on a separate thread and sends the frames to a socket.
/// @param port Port to send the frames on
/// @param width Frame width
/// @param height Frame height
CameraThread::CameraThread(int port, int width, int height)
	: PublishThread(port), capture(nextCamera()) {
	setupCapture(width, height);
}

CameraThread::CameraThread(int port, std::string pipeline, int width, int height)
	: PublishThread(port) {
	capture.open(pipeline, cv::CAP_GSTREAMER);
	setupCapture(width, height);
}

void CameraThread::setupCapture(int width, int height) {
	if (!capture.isOpened()) {
		std::cerr << "Error: Could not open camera." << std::endl;
	}
	else {
		capture.set(cv::CAP_PROP_FRAME_WIDTH, width);
		capture.set(cv::CAP_PROP_FRAME_HEIGHT, height);

		// 3 bytes per pixel (RGB)
		int bufsize = width * height * 3;
		setsockopt(ZMQ_SNDBUF, &bufsize);
	}
}

void CameraThread::run() {
	// Adjust according to the bandwidth of the network / quality required
	std::vector<int> compressionParams = { cv::IMWRITE_JPEG_QUALITY, 100 };

    while (isRunning()) {
        cv::Mat frame;
        if (capture.read(frame)) {
            std::vector<uchar> buffer;
            cv::imencode(".jpg", frame, buffer, compressionParams);
            send(zmq::buffer(buffer));
        }
    }
}

void CameraThread::stop() {
	PublishThread::stop();
	capture.release();
}
