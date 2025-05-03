#include "GStreamerPipeline.h"

namespace GStreamerPipeline {
    // Function to start a GStreamer pipeline
    void startPipeline(int device_num, int port, int width, int height) {
        gst_init(nullptr, nullptr);

        /*
        There are three options for encoding:
        1. H.264 encoding using the CPU
        2. H.264 encoding using the discrete codec (Max 1920x1080, 30fps!)
        3. JPEG encoding
        Uncomment the appropriate line in the pipeline string below to select the desired encoding method.
        For H.264 encoding, use ! h264parse config-interval=1 ! to allow joining mid-stream. Useful for debugging!
        */
        std::string pipeline_str =
            // Uncomment for H.264 encoding using the CPU
            "v4l2src device=/dev/video" + std::to_string(device_num) + " ! "
            "video/x-raw, width=" + std::to_string(width) + ", height=" + std::to_string(height) + ", framerate=20/1 ! videoconvert ! "
            // "x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast ! rtph264pay ! " // 1
            // "v4l2h264enc ! video/x-h264, level=4 ! h264parse config-interval=1 ! " // 2
            // "jpegenc ! rtpjpegpay ! " // 3
            "udpsink host=192.168.0.159 port=" + std::to_string(port);

        std::cout << "Starting pipeline for /dev/video" << device_num << " on port " << (5000 + device_num) << "...\n";

        GstElement* pipeline = gst_parse_launch(pipeline_str.c_str(), nullptr);
        if (!pipeline) {
            std::cerr << "Failed to create pipeline for device " << device_num << "!\n";
            return;
        }

        if (gst_element_set_state(pipeline, GST_STATE_PLAYING) == GST_STATE_CHANGE_FAILURE) {
            std::cerr << "Failed to start the pipeline for device " << device_num << "!\n";
            gst_object_unref(pipeline);
            return;
        }

        GstBus* bus = gst_element_get_bus(pipeline);
        GstMessage* msg;
        do {
            msg = gst_bus_timed_pop_filtered(bus, GST_CLOCK_TIME_NONE,
                static_cast<GstMessageType>(GST_MESSAGE_ERROR | GST_MESSAGE_EOS));
        } while (!msg);

        if (msg) gst_message_unref(msg);
        gst_object_unref(bus);
        gst_element_set_state(pipeline, GST_STATE_NULL);
        gst_object_unref(pipeline);

        std::cout << "Pipeline for /dev/video" << device_num << " stopped.\n";
    }

    // Function to launch multiple pipelines in parallel
    void launchPipelines(int port, int width, int height, const std::vector<int>& devices) {
        std::vector<std::thread> threads;

        for (int device : devices) {
            threads.emplace_back(startPipeline, device, port + device, width, height);
        }

        // Wait for all threads to finish
        for (auto& t : threads) {
            t.join();
        }
    }

} // namespace GStreamerPipeline

