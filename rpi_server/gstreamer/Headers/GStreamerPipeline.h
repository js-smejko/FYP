#ifndef GSTREAMER_PIPELINE_H
#define GSTREAMER_PIPELINE_H

#include <iostream>
#include <thread>
#include <vector>
#include <gst/gst.h>

namespace GStreamerPipeline {
    // Function to start a GStreamer pipeline in a separate thread
    void startPipeline(int device_num, int port, int width, int height);

    // Function to launch multiple pipelines in parallel
    void launchPipelines(int port, int width, int height, const std::vector<int>& devices);
}

#endif // GSTREAMER_PIPELINE_H
