#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[monitor] Stopping existing containers..."
docker compose down

echo "[monitor] Rebuilding images..."
docker compose build

echo "[monitor] Starting containers in detached mode..."
docker compose up -d
