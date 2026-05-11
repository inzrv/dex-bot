#include "runtime.h"

#include "common/log.h"

#include <stdexcept>
#include <utility>

Runtime::Runtime(RuntimeFactory& factory)    
    : m_io_ctx()
    , m_ssl_ctx(ssl::context::tls_client)
    , m_work_guard(net::make_work_guard(m_io_ctx))
{
    m_ssl_ctx.set_default_verify_paths();
    m_ssl_ctx.set_verify_mode(ssl::verify_peer);

    auto components = factory.create(m_io_ctx, m_ssl_ctx);
    m_queue = std::move(components.queue);

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
    run_core_loop();
}

void Runtime::stop()
{
    if (!m_running.exchange(false)) {
        return;
    }

    log::info("Runtime", "stopping...");
}

void Runtime::run_core_loop()
{
    for (;;) {
        if (!m_running) {
            return;
        }
    }

    return;
}
