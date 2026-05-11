#pragma once

#include "runtime_factory.h"

#include <boost/asio.hpp>
#include <boost/beast/ssl.hpp>

#include <atomic>
#include <chrono>
#include <expected>
#include <memory>
#include <thread>

namespace net = boost::asio;
namespace ssl = net::ssl;

class Runtime
{
public:
    explicit Runtime(RuntimeFactory& factory);
    ~Runtime();

    void run();
    void stop();

private:
    void run_core_loop();

private:
    net::io_context m_io_ctx;
    net::executor_work_guard<net::io_context::executor_type> m_work_guard;
    std::thread m_io_thread;
    std::atomic<bool> m_running{false};

    std::shared_ptr<IQueue> m_queue;
    std::unique_ptr<Gateway> m_gateway;
};
