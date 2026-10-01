# Research build environment; no game data and no executable engine source.
# SPDX-License-Identifier: GPL-3.0-only
FROM ubuntu@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates git g++ cmake ninja-build python3 \
    libboost-program-options-dev libboost-iostreams-dev libboost-system-dev libboost-filesystem-dev \
    libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libswresample-dev \
    libsdl2-dev libopenal-dev libtinyxml-dev libbullet-dev liblz4-dev \
    libpng-dev libjpeg-dev libfreetype6-dev libfontconfig1-dev \
    libluajit-5.1-dev libsqlite3-dev libicu-dev libyaml-cpp-dev \
    libopenscenegraph-dev libcollada-dom-dev libgl1-mesa-dev \
    libxrandr-dev libxinerama-dev xvfb xauth mesa-utils \
    && rm -rf /var/lib/apt/lists/*
COPY build.sh /usr/local/bin/openoblivion-build-upstream
ENTRYPOINT ["bash", "/usr/local/bin/openoblivion-build-upstream"]

