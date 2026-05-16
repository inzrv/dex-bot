#pragma once

#include "runtime/runtime_factory.h"

#include <boost/asio.hpp>

#include <atomic>
#include <memory>
#include <thread>

namespace net = boost::asio;

namespace runtime
{

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

    std::shared_ptr<IQueue> m_pending_queue;
    std::unique_ptr<builder::PendingFeed> m_builder_pending_feed;
    std::unique_ptr<builder::RestClient> m_builder_rest_client;
};

} // namespace runtime
