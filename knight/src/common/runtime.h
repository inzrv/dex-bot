#pragma once

#include <boost/asio.hpp>
#include <boost/beast/ssl.hpp>

#include <atomic>
#include <chrono>
#include <expected>
#include <memory>
#include <thread>

class Runtime
{
public:
    explicit Runtime();
    ~Runtime();

    void run();
    void stop();

private:
    void run_core_loop();

private:
    std::thread m_io_thread;
    std::atomic<bool> m_running{false};
};
