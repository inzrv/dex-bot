#include "runtime_factory.h"

#include "common/log.h"
#include "common/queue.h"

#include <stdexcept>
#include <utility>

RuntimeFactory::RuntimeFactory(Config config)
    : m_config(std::move(config))
{}

RuntimeComponents RuntimeFactory::create(boost::asio::io_context& io_ctx,
                                         boost::asio::ssl::context& ssl_ctx)
{
    log::info("RuntimeFactory", "creating components...");

    RuntimeComponents components;

    components.queue = std::make_shared<Queue<10'000>>();

    log::info("RuntimeFactory", "created all components");
    return components;
}
