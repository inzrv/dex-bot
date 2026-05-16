#pragma once

#include "common/config.h"
#include "builder/errors.h"
#include "network/rest_client.h"

#include <chrono>
#include <expected>
#include <memory>
#include <string>
#include <string_view>

namespace builder
{

class RestClient final
{
public:
    RestClient(Config config, net::io_context& io_ctx);

    std::expected<std::string, Error> request_snapshot() const;

private:
    Config m_config;
    std::unique_ptr<network::RestClient> m_rest_client;

    static constexpr std::string_view kPendingSnapshotTarget{"/public/pending"};
    static constexpr int kSnapshotMaxAttempts{3};
    static constexpr std::chrono::milliseconds kSnapshotBaseBackoff{200};
};

} // namespace builder
