#include "GStreamerPipeline.h"

int main() {
    GStreamerPipeline::launchPipelines(5000, 960, 960, {0, 1});
    return 0;
}
