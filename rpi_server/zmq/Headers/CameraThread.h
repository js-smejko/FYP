#pragma once

#include "PublishThread.h"

#include <opencv2/opencv.hpp>
#include <vector>
#include <iostream>

/// @brief Thread that captures frames from a camera and sends them to a socket.
class CameraThread : public PublishThread {
    static int cameraCount;
    cv::VideoCapture capture;

    void run();

protected:
	void setupCapture(int width, int height);

	inline int nextCamera() { return cameraCount++; }

public:
    CameraThread(int port, int width, int height);
    CameraThread(int port, std::string pipeline, int width, int height);

    void stop();
};
