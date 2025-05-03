#pragma once

#include <zmq.hpp>
#include <thread>
#include <atomic>

/// @brief Abstract class for a thread that publishes data to a socket.
class PublishThread {
    std::atomic<bool> running;
    zmq::context_t context;
    std::thread thread;
    zmq::socket_t socket;

protected:
    virtual void run() = 0;
    void send(const zmq::mutable_buffer& buf, zmq::send_flags flags = zmq::send_flags::none);
	void setsockopt(int option, const void* value);
	void sleep(int duration);

    inline bool isRunning() const { return running.load(); }

public:
    PublishThread(int port);
    ~PublishThread();

    void start();
    void stop();
};
