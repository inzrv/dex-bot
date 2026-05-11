#pragma once

#include "time.h"

#include <string>

struct InputEnvelope
{
    latency_time_point ingress_time;
    std::string source;
    std::string payload;
};
