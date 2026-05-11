#pragma once

#include "config.h"
#include "queue.h"

#include <boost/asio/io_context.hpp>
#include <boost/asio/ssl/context.hpp>

struct RuntimeComponents
{
    std::shared_ptr<IQueue> queue;
};

class RuntimeFactory final
{
public:
    explicit RuntimeFactory(Config config);

    RuntimeComponents create(boost::asio::io_context& io_ctx,
                             boost::asio::ssl::context& ssl_ctx);

private:
    Config m_config;
};
