#!/usr/bin/env bash
set -euo pipefail

readonly image="registry.home.siczb.de/siczb/teltonika-rms-ci:${BUILD_NUMBER}"

printf '%s\n' \
  'FROM registry.home.siczb.de/siczb/python-ci:latest' \
  'WORKDIR /build' \
  'USER root' \
  'RUN (apt-get update && apt-get install -y git curl ca-certificates) || (apk add --no-cache git curl ca-certificates) || true' \
  'COPY requirements.txt ./' \
  'RUN python3 -m pip install --upgrade pip --index-url https://artifacts.home.siczb.de/repository/pypi-proxy/simple/' \
  'RUN python3 -m pip install --index-url https://artifacts.home.siczb.de/repository/pypi-proxy/simple/ -r requirements.txt' \
  'COPY pyproject.toml pytest.ini .coveragerc ./' \
  'COPY custom_components ./custom_components' \
  'COPY tests ./tests' \
  'COPY tools ./tools' \
  > Dockerfile.ci

podman build --pull=never --tag "${image}" --file Dockerfile.ci .
