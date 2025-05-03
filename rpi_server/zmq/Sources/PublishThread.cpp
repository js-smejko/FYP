#include "PublishThread.h"

/// @brief Abstract class for a thread that publishes data to a socket.
/// @param port Port to send the data on
PublishThread::PublishThread(int port)
    : running(true), context(1), socket(context, ZMQ_PUB) {
    int conflate = 1;
    zmq_setsockopt(socket, ZMQ_CONFLATE, &conflate, sizeof(conflate));
    int immediate = 1;
    zmq_setsockopt(socket, ZMQ_IMMEDIATE, &immediate, sizeof(immediate));
    int sndhwm = 1;
    socket.setsockopt(ZMQ_SNDHWM, &sndhwm, sizeof(sndhwm));

    std::string address = "tcp://*:" + std::to_string(port);
    socket.bind(address);
}

void PublishThread::setsockopt(int option, const void* value) {
	zmq_setsockopt(socket, option, value, sizeof(value));
}

void PublishThread::send(const zmq::mutable_buffer& buf, zmq::send_flags flags) {
	socket.send(zmq::buffer(buf.data(), buf.size()), flags);
}

void PublishThread::sleep(int duration) {
    std::this_thread::sleep_for(std::chrono::milliseconds(duration));
}

void PublishThread::start() {
    thread = std::thread(&PublishThread::run, this);
}

void PublishThread::stop() {
    running = false;
    if (thread.joinable()) {
        thread.join();
    }
    socket.close();
}

PublishThread::~PublishThread() {
    stop();
}
