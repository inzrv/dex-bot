#include "runtime_factory.h"

#include "gateway.h"
#include "log.h"
#include "queue.h"

#include <stdexcept>
#include <utility>

RuntimeFactory::RuntimeFactory(Config config)
    : m_config(std::move(config))
{}

RuntimeComponents RuntimeFactory::create(boost::asio::io_context& io_ctx)
{
    log::info("RuntimeFactory", "creating components...");

    RuntimeComponents components;

    components.queue = std::make_shared<Queue<10'000>>();
    components.gateway = std::make_unique<Gateway>(
        m_config,
        io_ctx,
        components.queue);

    log::info("RuntimeFactory", "created all components");
    return components;
}
