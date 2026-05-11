file(GLOB_RECURSE PROJECT_SOURCES CONFIGURE_DEPENDS
    "*.cpp"
)

add_executable(knight ${PROJECT_SOURCES})

target_include_directories(knight
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${Boost_INCLUDE_DIRS}
)

target_link_libraries(knight
    PRIVATE
        Boost::boost
        OpenSSL::SSL
        OpenSSL::Crypto
        spdlog::spdlog
        solabi::solabi
)

if(APPLE)
    target_compile_options(knight PRIVATE -Wall -Wextra -Wpedantic)
endif()
