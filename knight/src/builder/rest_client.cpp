#include "builder/rest_client.h"

#include "common/log.h"

#include <thread>
#include <utility>

namespace builder
{

RestClient::RestClient(Config config, net::io_context& io_ctx)
    : m_config(std::move(config))
{
    const auto& endpoint = m_config.builder_ws_endpoint;
    m_rest_client = std::make_unique<network::RestClient>(
        io_ctx,
        endpoint.use_tls,
        m_config.tls_verify_peer,
        endpoint.host,
        endpoint.port);
}

std::expected<std::string, Error> RestClient::request_snapshot() const
{
    auto last_error = network::RestError::UNKNOWN_ERROR;

    for (int attempt = 1; attempt <= kSnapshotMaxAttempts; ++attempt) {
        log::debug("BuilderRestClient",
                   "requesting pending snapshot {} (attempt {}/{})",
                   kPendingSnapshotTarget,
                   attempt,
                   kSnapshotMaxAttempts);

        const auto res = m_rest_client->get(kPendingSnapshotTarget);
        if (res) {
            log::debug("BuilderRestClient", "pending snapshot request succeeded");
            return *res;
        }

        last_error = res.error();
        if (attempt == kSnapshotMaxAttempts) {
            break;
        }

        const auto backoff = kSnapshotBaseBackoff * (1 << (attempt - 1));
        log::warn("BuilderRestClient",
                  "pending snapshot request failed: {}, retrying in {} ms",
                  network::error_to_string(res.error()),
                  backoff.count());
        std::this_thread::sleep_for(backoff);
    }

    log::error("BuilderRestClient",
               "pending snapshot request failed after {} attempts: {}",
               kSnapshotMaxAttempts,
               network::error_to_string(last_error));
    return std::unexpected(Error::REQUEST_ERROR);
}

} // namespace builder
