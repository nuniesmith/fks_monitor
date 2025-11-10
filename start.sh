#!/bin/bash
# Start script for FKS Monitor Service

set -e

echo "🚀 Starting FKS Monitor Service..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
docker-compose up -d

echo "✅ FKS Monitor Service started"
echo ""
echo "📊 Services:"
echo "  - Monitor API: http://localhost:8009"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop: docker-compose down"
echo "  - Restart: docker-compose restart"

