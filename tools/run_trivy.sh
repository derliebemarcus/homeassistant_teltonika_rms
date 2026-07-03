#!/usr/bin/env bash
set -u

readonly report="build/reports/trivy/trivy-report.json"
mkdir -p "$(dirname "${report}")"

set +e
podman run --rm \
  --volume "${PWD}:/workspace:z" \
  --workdir /workspace \
  docker.io/aquasec/trivy:latest \
  fs . \
  --scanners vuln,secret \
  --ignorefile /workspace/.trivyignore \
  --severity HIGH,CRITICAL \
  --exit-code 1 \
  --format json \
  --output "${report}" \
  --no-progress
status=$?
set -e

if [ "${status}" -ne 0 ]; then
  python3 tools/report_trivy_findings.py "${report}"
fi

exit "${status}"
