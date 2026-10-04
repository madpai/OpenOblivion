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
    add_executable(oo_tes4_animation_test tests/test_tes4_animation.cpp)
    target_include_directories(oo_tes4_animation_test PRIVATE tools/native)
    target_compile_options(oo_tes4_animation_test PRIVATE -Wall -Wextra -Wpedantic -Werror -UNDEBUG)
    add_test(NAME tes4-animation-fixtures COMMAND oo_tes4_animation_test)
    find_path(OO_OSG_INCLUDE_DIR osg/Vec3f REQUIRED)
    find_library(OO_OSG_LIBRARY osg REQUIRED)
    find_library(OO_OSGDB_LIBRARY osgDB REQUIRED)
    add_executable(oo_player_collision_model_test tests/test_player_collision_model.cpp)
    target_include_directories(oo_player_collision_model_test SYSTEM PRIVATE "${OO_OSG_INCLUDE_DIR}")
    target_link_libraries(oo_player_collision_model_test PRIVATE "${OO_OSGDB_LIBRARY}" "${OO_OSG_LIBRARY}")
    target_compile_options(oo_player_collision_model_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME player-collision-model-fixture COMMAND oo_player_collision_model_test
        "${CMAKE_SOURCE_DIR}/tools/android/meshes/basicplayer.osgt")
    add_executable(oo_reference_lock_test tests/test_reference_locks.cpp
        "${OO_OPENMW_SOURCE}/components/esm4/loadrefr.cpp")
    target_include_directories(oo_reference_lock_test PRIVATE tools/native)
    target_include_directories(oo_reference_lock_test SYSTEM PRIVATE "${OO_OSG_INCLUDE_DIR}")
    target_link_libraries(oo_reference_lock_test PRIVATE oo_openmw_reader)
    target_compile_options(oo_reference_lock_test PRIVATE -Wall -Wextra -Wpedantic)
    add_test(NAME reference-lock-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_reference_locks.py" "$<TARGET_FILE:oo_reference_lock_test>")
    add_executable(oo_native_grounded_eye_test tests/test_native_grounded_eye.cpp)
    target_include_directories(oo_native_grounded_eye_test PRIVATE tools/native)
    target_compile_options(oo_native_grounded_eye_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME native-grounded-eye-fixtures COMMAND oo_native_grounded_eye_test)
    add_executable(oo_authored_strips_test tests/test_authored_strips.cpp)
    target_include_directories(oo_authored_strips_test PRIVATE tools/native)
    target_compile_options(oo_authored_strips_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME authored-strip-fixtures COMMAND oo_authored_strips_test)
    find_path(OO_BULLET_INCLUDE_DIR btBulletCollisionCommon.h PATH_SUFFIXES bullet REQUIRED)
    find_library(OO_BULLET_COLLISION_LIBRARY BulletCollision REQUIRED)
    find_library(OO_BULLET_MATH_LIBRARY LinearMath REQUIRED)
    add_executable(oo_tes4_body_test tests/test_tes4_body.cpp)
    target_include_directories(oo_tes4_body_test PRIVATE tools/native "${OO_OPENMW_SOURCE}/apps/openmw/mwphysics")
    target_include_directories(oo_tes4_body_test SYSTEM PRIVATE
        "${OO_OPENMW_SOURCE}" "${OO_OSG_INCLUDE_DIR}" "${OO_BULLET_INCLUDE_DIR}")
    target_link_libraries(oo_tes4_body_test PRIVATE "${OO_BULLET_COLLISION_LIBRARY}" "${OO_BULLET_MATH_LIBRARY}")
    target_compile_options(oo_tes4_body_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME tes4-body-fixtures COMMAND oo_tes4_body_test)
    add_executable(oo_tes4_movement_test tests/test_tes4_movement.cpp)
    target_include_directories(oo_tes4_movement_test PRIVATE tools/native)
    target_compile_options(oo_tes4_movement_test PRIVATE -Wall -Wextra -Wpedantic -Werror)
    add_test(NAME tes4-movement-fixtures COMMAND oo_tes4_movement_test)
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
    add_test(NAME look-name-fixtures COMMAND "${OO_LUA_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_look_name.lua" "${CMAKE_SOURCE_DIR}")
    add_test(NAME container-fixtures COMMAND "${OO_LUA_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_container.lua" "${CMAKE_SOURCE_DIR}")
    add_test(NAME tes4-items-fixtures COMMAND "${OO_LUA_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_tes4_items.lua" "${CMAKE_SOURCE_DIR}")
    add_test(NAME tes4-combat-fixtures COMMAND "${OO_LUA_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_tes4_combat.lua" "${CMAKE_SOURCE_DIR}")
    add_test(NAME door-activation-fixtures COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_SOURCE_DIR}/tests/test_door_activation.py")
endif()
