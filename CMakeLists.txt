# SPDX-License-Identifier: GPL-3.0-only
cmake_minimum_required(VERSION 3.24)
project(OpenOblivion VERSION 0.0.1 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(OO_OPENMW_SOURCE "" CACHE PATH "Unmodified pinned OpenMW source checkout")
if(NOT OO_OPENMW_SOURCE)
    message(FATAL_ERROR "Set OO_OPENMW_SOURCE; see tools/fetch_upstream.py and README.md")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
execute_process(COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/check_upstream.py"
    "${OO_OPENMW_SOURCE}" RESULT_VARIABLE source_check OUTPUT_VARIABLE source_report
    ERROR_VARIABLE source_error)
if(NOT source_check EQUAL 0)
    message(FATAL_ERROR "${source_report}${source_error}")
endif()
message(STATUS "${source_report}")
add_custom_target(oo_verify_upstream
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/check_upstream.py" "${OO_OPENMW_SOURCE}"
    COMMENT "Verify pinned upstream source and notices")
find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)

# Compile the audited upstream slice unchanged. No upstream files are vendored.
set(OO_UPSTREAM_SOURCES
    components/esm4/reader.cpp
    components/esm4/loadtes4.cpp
    components/esm/formid.cpp
    components/esm/refid.cpp
    components/esm/stringrefid.cpp
    components/esm/generatedrefid.cpp
    components/esm/indexrefid.cpp
    components/esm/esm3exteriorcellrefid.cpp
    components/files/constrainedfilestreambuf.cpp
    components/files/conversion.cpp
    components/platform/fileposix.cpp
    components/toutf8/toutf8.cpp
    components/debug/debuglog.cpp
    components/vfs/manager.cpp)
list(TRANSFORM OO_UPSTREAM_SOURCES PREPEND "${OO_OPENMW_SOURCE}/")
add_library(oo_openmw_reader STATIC ${OO_UPSTREAM_SOURCES})
add_dependencies(oo_openmw_reader oo_verify_upstream)
target_include_directories(oo_openmw_reader SYSTEM PUBLIC "${OO_OPENMW_SOURCE}")
target_link_libraries(oo_openmw_reader PUBLIC ZLIB::ZLIB Threads::Threads)
add_executable(openoblivion-inspect src/inspect.cpp)
add_dependencies(openoblivion-inspect oo_verify_upstream)
target_link_libraries(openoblivion-inspect PRIVATE oo_openmw_reader)
target_compile_options(openoblivion-inspect PRIVATE -Wall -Wextra -Wpedantic -Werror)

option(OO_BUILD_VULKAN_PROBE "Build Vulkan device enumeration tool" ON)
if(OO_BUILD_VULKAN_PROBE)
    if(ANDROID)
        find_library(OO_VULKAN_LIBRARY vulkan REQUIRED)
        add_library(oo_vulkan INTERFACE)
        target_link_libraries(oo_vulkan INTERFACE "${OO_VULKAN_LIBRARY}")
    else()
        find_package(Vulkan REQUIRED)
        add_library(oo_vulkan INTERFACE)
        target_link_libraries(oo_vulkan INTERFACE Vulkan::Vulkan)
    endif()
    add_executable(openoblivion-vulkan-probe src/vulkan_probe.cpp)
    target_link_libraries(openoblivion-vulkan-probe PRIVATE oo_vulkan)
    target_compile_options(openoblivion-vulkan-probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

include(CTest)
if(BUILD_TESTING AND NOT ANDROID)
    add_executable(oo_native_grounded_eye_test tests/test_native_grounded_eye.cpp)
    target_include_directories(oo_native_grounded_eye_test PRIVATE tools/native)
    target_compile_options(oo_native_grounded_eye_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME native-grounded-eye-fixtures COMMAND oo_native_grounded_eye_test)
    add_test(NAME native-build-receipt-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_native_build.py")
    find_program(OO_LUA_EXECUTABLE NAMES luajit lua5.1 lua REQUIRED)
    add_test(NAME original-tes4-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_inspect.py" "$<TARGET_FILE:openoblivion-inspect>")
    add_test(NAME content-guard-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_content_guard.py")
    add_test(NAME upstream-lock-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_upstream.py")
    add_test(NAME android-preview-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_android_preview.py")
    add_test(NAME player-movement-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_player_movement.py")
    add_test(NAME grounded-eye-fixtures COMMAND "${OO_LUA_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_grounded_eye.lua" "${CMAKE_SOURCE_DIR}")
endif()
