#!/bin/bash
# Entrypoint script for FKS Monitor Service

set -e

# Default values
SERVICE_NAME=${SERVICE_NAME:-fks_monitor}
SERVICE_PORT=${SERVICE_PORT:-${MONITOR_PORT:-8009}}
HOST=${HOST:-0.0.0.0}

echo "Starting ${SERVICE_NAME} on ${HOST}:${SERVICE_PORT}"

# Run the service
exec uvicorn src.main:app \
    --host "${HOST}" \
    --port "${SERVICE_PORT}" \
    --no-access-log \
    --log-level info

