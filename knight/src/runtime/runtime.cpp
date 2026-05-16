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
    m_pending_queue = std::move(components.pending_queue);
    m_builder_pending_feed = std::move(components.builder_pending_feed);
    m_builder_rest_client = std::move(components.builder_rest_client);

    if (!m_pending_queue || !m_builder_pending_feed || !m_builder_rest_client) {
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

    m_builder_pending_feed->open();

    const auto wait_res = m_builder_pending_feed->wait_until_ready(std::chrono::seconds{10});
    if (!wait_res) {
        log::error("Runtime", "failed to open builder pending feed: {}", builder::error_to_string(wait_res.error()));
        return;
    }

    log::info("Runtime", "builder pending feed ready");

    run_core_loop();
}

void Runtime::stop()
{
    if (!m_running.exchange(false)) {
        return;
    }

    log::info("Runtime", "stopping...");
    m_builder_pending_feed->close();
    m_pending_queue->close();
    m_work_guard.reset();
    m_io_ctx.stop();

    if (m_io_thread.joinable()) {
        m_io_thread.join();
    }
}

void Runtime::run_core_loop()
{
    const auto snapshot = m_builder_rest_client->request_snapshot();
    if (snapshot) {
        log::info("Runtime", "pending snapshot: {}", *snapshot);
    } else {
        log::error("Runtime", "failed to request pending snapshot: {}", builder::error_to_string(snapshot.error()));
    }

    for (;;) {
        auto item = m_pending_queue->wait_pop();

        if (!item) {
            log::info("Runtime", "input queue closed, stopping core loop");
            return;
        }

        log::info("Runtime", "envelope: source={}, payload={}", item->source, item->payload);
    }
}

} // namespace runtime
