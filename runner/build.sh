#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
	echo "docker is not installed or not in PATH" >&2
	exit 1
fi

echo "Building Docker image 'runner-service' (no cache)..."
docker build --no-cache -t runner-service .
echo "Built runner-service"