#pragma once

#include <string_view>

enum class GatewayError
{
    REQUEST_ERROR,
    TIMEOUT
};

inline std::string_view error_to_string(GatewayError error) noexcept
{
    switch (error) {
        case GatewayError::REQUEST_ERROR: return "REQUEST_ERROR";
        case GatewayError::TIMEOUT: return "TIMEOUT";
    }

    return "UNKNOWN_GATEWAY_ERROR";
}
