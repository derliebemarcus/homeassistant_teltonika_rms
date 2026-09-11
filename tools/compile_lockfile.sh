#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK=0
UPGRADE=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK=1 ;;
    --upgrade) UPGRADE=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

compile_args=(
  --no-strip-extras
  --no-emit-index-url
  --no-emit-trusted-host
  requirements-dev.in
  -o requirements.txt
)
if [ "$UPGRADE" -eq 1 ]; then
  compile_args=(--upgrade "${compile_args[@]}")
fi

compile_in() {
  local workdir="$1"

  if [ "$(uname -s)" = "Linux" ] && command -v pip-compile >/dev/null 2>&1; then
    (cd "$workdir" && unset PIP_NO_INDEX && pip-compile "${compile_args[@]}")
    return
  fi

  local engine=""
  if command -v podman >/dev/null 2>&1; then
    engine="podman"
  elif command -v docker >/dev/null 2>&1; then
    engine="docker"
  else
    echo "Podman or Docker is required to generate the canonical Linux lockfile." >&2
    exit 1
  fi

  local relative_workdir="${workdir#"$ROOT"}"
  relative_workdir="${relative_workdir#/}"

  "$engine" run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -v "$ROOT:/work" \
    -w "/work${relative_workdir:+/$relative_workdir}" \
    python:3.14-slim \
    sh -c 'python -m pip install --user pip-tools==7.6.1 >/dev/null && /tmp/.local/bin/pip-compile "$@"' \
    sh "${compile_args[@]}"
}

if [ "$CHECK" -eq 1 ]; then
  tmpdir="$(mktemp -d "$ROOT/.lockcheck.XXXXXX")"
  trap 'rm -rf "$tmpdir"' EXIT
  cp "$ROOT/requirements-dev.in" "$ROOT/requirements.txt" "$tmpdir/"
  compile_in "$tmpdir"
  diff -u "$ROOT/requirements.txt" "$tmpdir/requirements.txt"
else
  compile_in "$ROOT"
fi
