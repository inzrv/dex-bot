#pragma once

#include "utils/utils.h"

#include <boost/json.hpp>

#include <cstdint>
#include <optional>
#include <string>

struct Config final
{
    bool from_json(const boost::json::object& json)
    {
        const auto host_json = json_string(json, "host");
        const auto port_json = json_int64(json, "port");

        if (!host_json || !port_json) {
            return false;
        }

        host = *host_json;
        port = static_cast<uint16_t>(*port_json);
        return true;
    }

    bool from_string(std::string_view s)
    {
        const auto parse_to_json_res = parse_to_json_object(s);
        if (!parse_to_json_res) {
            return false;
        }

        return from_json(*parse_to_json_res);
    }

    std::string host;
    uint16_t port{0};
};
