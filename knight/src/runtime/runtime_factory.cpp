#include "runtime/runtime_factory.h"

#include "common/log.h"
#include "common/queue.h"

#include <utility>

namespace runtime
{

RuntimeFactory::RuntimeFactory(Config config)
    : m_config(std::move(config))
{}

RuntimeComponents RuntimeFactory::create(boost::asio::io_context& io_ctx)
{
    log::info("RuntimeFactory", "creating components...");

    RuntimeComponents components;

    components.pending_queue = std::make_shared<Queue<10'000>>();
    components.builder_rest_client = std::make_unique<builder::RestClient>(m_config, io_ctx);
    components.builder_pending_feed = std::make_unique<builder::PendingFeed>(
        m_config,
        io_ctx,
        components.pending_queue);

    log::info("RuntimeFactory", "created all components");
    return components;
}

} // namespace runtime
