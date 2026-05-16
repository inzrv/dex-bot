#pragma once

#include "common/config.h"
#include "common/queue.h"
#include "builder/rest_client.h"
#include "builder/pending_feed.h"

#include <boost/asio/io_context.hpp>

#include <memory>

namespace runtime
{

struct RuntimeComponents
{
    std::shared_ptr<IQueue> pending_queue;
    std::unique_ptr<builder::PendingFeed> builder_pending_feed;
    std::unique_ptr<builder::RestClient> builder_rest_client;
};

class RuntimeFactory final
{
public:
    explicit RuntimeFactory(Config config);

    RuntimeComponents create(boost::asio::io_context& io_ctx);

private:
    Config m_config;
};

} // namespace runtime
