#include "runtime/runtime.h"

#include "common/log.h"

#include <chrono>
#include <stdexcept>
#include <utility>

namespace runtime
{

Runtime::Runtime(RuntimeFactory& factory)
    : m_io_ctx()
    , m_work_guard(net::make_work_guard(m_io_ctx))
{
    auto components = factory.create(m_io_ctx);
    m_queue = std::move(components.queue);
    m_gateway = std::move(components.gateway);

    if (!m_queue || !m_gateway) {
        throw std::invalid_argument("runtime factory returned incomplete components");
    }

    log::info("Runtime", "Runtime initialized with all components");
}

Runtime::~Runtime()
{
    stop();
}

void Runtime::run()
{
    log::info("Runtime", "starting...");
    m_running = true;

    m_io_thread = std::thread([this]() {
        m_io_ctx.run();
    });

    m_gateway->open();

    const auto wait_res = m_gateway->wait_until_ready(std::chrono::seconds{10});
    if (!wait_res) {
        log::error("Runtime", "failed to open gateway: {}", gateway::error_to_string(wait_res.error()));
        return;
    }

    log::info("Runtime", "gateway ready");

    run_core_loop();
}

void Runtime::stop()
{
    if (!m_running.exchange(false)) {
        return;
    }

    log::info("Runtime", "stopping...");
    m_queue->close();
    m_work_guard.reset();
    m_io_ctx.stop();

    if (m_io_thread.joinable()) {
        m_io_thread.join();
    }
}

void Runtime::run_core_loop()
{
    for (;;) {
        auto item = m_queue->wait_pop();

        if (!item) {
            log::info("Runtime", "input queue closed, stopping core loop");
            return;
        }

        log::info("Runtime", "envelope: source={}, payload={}", item->source, item->payload);
    }
}

} // namespace runtime
