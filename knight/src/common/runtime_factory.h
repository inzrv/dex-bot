#pragma once

#include "gateway.h"
#include "config.h"
#include "queue.h"

#include <boost/asio/io_context.hpp>
#include <boost/asio/ssl/context.hpp>

struct RuntimeComponents
{
    std::shared_ptr<IQueue> queue;
    std::unique_ptr<Gateway> gateway;
};

class RuntimeFactory final
{
public:
    explicit RuntimeFactory(Config config);

    RuntimeComponents create(boost::asio::io_context& io_ctx);

private:
    Config m_config;
};
