#include <iostream>
#include <cstdlib>

#include "CameraThread.h"

int main() {
    CameraThread cap1(5555, 1920, 1920);
    CameraThread cap2(5556, 1920, 1920);

    cap1.start();
    cap2.start();

    while (cv::waitKey(1000) != 27) {
        //std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    cap1.stop();
    cap2.stop();

    return 0;
}
