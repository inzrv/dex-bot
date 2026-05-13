#pragma once

#include "common/config.h"
#include "common/queue.h"
#include "gateway/errors.h"
#include "network/ws_source.h"

#include <chrono>
#include <condition_variable>
#include <expected>
#include <memory>
#include <mutex>

namespace gateway
{

class Gateway final
{
public:
    enum class State
    {
        CLOSED,
        OPEN,
        FAILED
    };

    Gateway(Config config,
            net::io_context& io_ctx,
            std::shared_ptr<IQueue> queue);

    void open();
    void close();
    void reopen();
    std::expected<void, Error> wait_until_ready(std::chrono::milliseconds timeout);
    [[nodiscard]] State state() const noexcept
    {
        return m_state;
    }

private:
    void on_ws_state(network::WsSource::State state);
    void on_ws_error(beast::error_code ec, std::string_view where);

private:
    Config m_config;
    net::io_context& m_io_ctx;
    std::shared_ptr<IQueue> m_queue;
    std::unique_ptr<network::WsSource> m_ws_source;

    mutable std::mutex m_state_mutex;
    std::condition_variable m_state_cv;

    State m_state{State::CLOSED};
};

} // namespace gateway
