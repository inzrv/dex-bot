#pragma once

#include "common/config.h"
#include "common/queue.h"
#include "gateway/gateway.h"

#include <boost/asio/io_context.hpp>

#include <memory>

namespace runtime
{

struct RuntimeComponents
{
    std::shared_ptr<IQueue> queue;
    std::unique_ptr<gateway::Gateway> gateway;
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
