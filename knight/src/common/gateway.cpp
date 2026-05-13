#include "gateway.h"

#include "log.h"

#include <stdexcept>
#include <utility>

Gateway::Gateway(Config config,
                 net::io_context& io_ctx,
                 std::shared_ptr<IQueue> queue)
    : m_config(std::move(config))
    , m_io_ctx(io_ctx)
    , m_queue(std::move(queue))
{
    const auto& endpoint = m_config.builder_ws_endpoint;
    log::info("Gateway", "mempool stream endpoint: {}", m_config.builder_ws_url);

    m_ws_source = std::make_unique<network::WsSource>(
        m_io_ctx,
        m_queue,
        endpoint.use_tls,
        m_config.tls_verify_peer,
        endpoint.host,
        endpoint.port,
        endpoint.target,
        [this](beast::error_code ec, std::string_view where) {
            on_ws_error(ec, where);
        },
        [this](network::WsSource::State state) {
            on_ws_state(state);
        },
        []() {
            log::warn("Gateway", "drop queue overflow");
        }
    );
}

void Gateway::open()
{
    if (m_state == State::OPEN) {
        return;
    }

    log::info("Gateway", "opening mempool stream...");
    m_ws_source->start();
}

void Gateway::close()
{
    if (m_state == State::CLOSED) {
        return;
    }

    log::info("Gateway", "closing mempool stream...");
    m_ws_source->stop();
}

void Gateway::reopen()
{
    log::info("Gateway", "reopen requested");
    m_ws_source->restart();
}

void Gateway::on_ws_state(network::WsSource::State state)
{
    std::lock_guard lock{m_state_mutex};
    log::info("Gateway", "websocket state: {}", ws_source_state_to_string(state));
    switch (state) {
        case network::WsSource::State::STOPPED:
            m_state = State::CLOSED;
            break;
        case network::WsSource::State::STARTING:
            break;
        case network::WsSource::State::RUNNING:
            m_state = State::OPEN;
            break;
        case network::WsSource::State::STOPPING:
            break;
        case network::WsSource::State::FAILED:
            m_state = State::FAILED;
            break;
    }

    m_state_cv.notify_all();
}

void Gateway::on_ws_error(beast::error_code ec, std::string_view where)
{
    log::error("Gateway", "websocket error: {} {}", where, ec.message());
    m_state = State::FAILED;
}

std::expected<void, GatewayError> Gateway::wait_until_ready(std::chrono::milliseconds timeout)
{
    std::unique_lock lock{m_state_mutex};
    const bool ok = m_state_cv.wait_for(lock, timeout, [this] {
        return m_state == State::OPEN || m_state == State::FAILED;
    });

    if (!ok) {
        return std::unexpected(GatewayError::TIMEOUT);
    }

    if (m_state == State::FAILED) {
        return std::unexpected(GatewayError::REQUEST_ERROR);
    }

    return {};
}
