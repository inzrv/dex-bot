#include "runtime.h"

#include "common/log.h"

#include <stdexcept>
#include <utility>

Runtime::Runtime()
{
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
