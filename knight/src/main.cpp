#include "common/log.h"
#include "common/runtime.h"
#include "common/signal_listener.h"

#include <stdexcept>
#include <string>
#include <string_view>
#include <fstream>
#include <iterator>
#include <memory>

int main(int argc, char* argv[])
{
    log::info("Main", "knight starting...");

    if (argc < 2) {
        log::error("Main", "usage: knight <config_path>");
        return 1;
    }

    const std::string config_path = argv[1];
    log::debug("Main", "config path: {}", config_path);

    std::ifstream config_file(config_path, std::ios::binary);
    if (!config_file) {
        log::error("Main", "failed to open config file: {}", config_path);
        return 1;
    }

    const std::string config_payload{
        std::istreambuf_iterator<char>{config_file},
        std::istreambuf_iterator<char>{}
    };

    log::info("Main", "Config payload: {}", config_payload);

    Runtime runtime;

    SignalListener signal_listener([&runtime](int signal) {
        log::info("Main", "received signal {}, requesting shutdown", signal);
        runtime.stop();
    });

    if (!signal_listener.start()) {
        log::error("Main", "failed to start signal listener");
        return 1;
    }

    runtime.run();
    signal_listener.stop();

    log::info("Main", "Knight stopped");

    return 0;
}
