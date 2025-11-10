# FKS Monitor Service

Centralized monitoring service that aggregates health checks, metrics, and test results from all FKS services and provides a unified API for `fks_main` orchestration.

## 🎯 Purpose

`fks_monitor` serves as the single source of truth for:
- **Health Status**: Aggregates `/health` and `/ready` endpoints from all FKS services
- **Metrics**: Collects Prometheus metrics from services and Grafana
- **Test Results**: Aggregates test status and coverage from all repos
- **Service Discovery**: Maintains registry of all FKS services and their endpoints

## 🏗️ Architecture

```
All FKS Services → fks_monitor → fks_main (Rust API)
     ↓                ↓              ↓
  /health         Aggregation    K8s Control
  /metrics        Prometheus     Orchestration
  /tests          Grafana        Service Mgmt
```

## 🚀 Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn src.main:app --reload --host 0.0.0.0 --port 8009
```

### Docker

```bash
# Build and run
docker-compose up --build

# Or use the start script
./start.sh
```

## 📡 API Endpoints

### Health & Status

- `GET /health` - Monitor service health
- `GET /ready` - Readiness check
- `GET /live` - Liveness probe

### Service Monitoring

- `GET /api/v1/services` - List all monitored services
- `GET /api/v1/services/{name}` - Get specific service status
- `GET /api/v1/services/{name}/metrics` - Get service metrics
- `GET /api/v1/services/{name}/tests` - Get service test results
- `POST /api/v1/services/register` - Register new service

### Aggregated Views

- `GET /api/v1/summary` - Overall system health summary
- `GET /api/v1/metrics` - All Prometheus metrics
- `GET /api/v1/tests` - All test results
- `GET /api/v1/health` - All service health statuses

### Prometheus Integration

- `GET /metrics` - Prometheus-compatible metrics endpoint

## 🔧 Configuration

### Environment Variables

```bash
# Service Configuration
MONITOR_PORT=8009
MONITOR_HOST=0.0.0.0

# Service Discovery
FKS_SERVICES_CONFIG=/app/config/services.yaml
AUTO_DISCOVER=true

# Prometheus
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000

# Google AI API (for test analysis)
GOOGLE_AI_API_KEY=your_key_here

# Update Intervals
HEALTH_CHECK_INTERVAL=30  # seconds
METRICS_UPDATE_INTERVAL=60  # seconds
TEST_CHECK_INTERVAL=300  # seconds (5 minutes)
```

### Service Registry

Services are configured in `config/services.yaml`:

```yaml
services:
  fks_api:
    name: fks_api
    health_url: http://fks-api:8001/health
    metrics_url: http://fks-api:8001/metrics
    port: 8001
    
  fks_app:
    name: fks_app
    health_url: http://fks-app:8002/health
    metrics_url: http://fks-app:8002/metrics
    port: 8002
    
  # ... other services
```

## 📊 Features

### 1. Health Check Aggregation

Periodically polls all FKS services:
- `/health` - Basic health
- `/ready` - Readiness (dependencies)
- `/live` - Liveness (process alive)

### 2. Metrics Collection

- Scrapes Prometheus metrics from services
- Aggregates Grafana dashboard data
- Provides unified metrics endpoint

### 3. Test Result Aggregation

- Checks test status from each service
- Aggregates coverage reports
- Uses Google AI API for test analysis (optional)

### 4. Service Discovery

- Auto-discovers services via Kubernetes
- Manual registration via API
- Maintains service registry

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v
```

## 🐳 Docker

### Build

```bash
docker build -t nuniesmith/fks_monitor:latest .
```

### Run

```bash
docker run -p 8009:8009 \
  -e PROMETHEUS_URL=http://prometheus:9090 \
  -e GRAFANA_URL=http://grafana:3000 \
  nuniesmith/fks_monitor:latest
```

## 📈 Integration with fks_main

`fks_main` (Rust API) consumes `fks_monitor` for:
- Service health status
- Metrics for K8s HPA decisions
- Test results for deployment gates
- Service discovery for orchestration

## 🔗 Related Services

- **fks_main**: Master orchestration (consumes monitor API)
- **Prometheus**: Metrics source
- **Grafana**: Dashboard data source
- **All FKS Services**: Health/metrics providers

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Service Registry](docs/SERVICE_REGISTRY.md)
- [Metrics Collection](docs/METRICS.md)

---

**Repository**: [nuniesmith/fks_monitor](https://github.com/nuniesmith/fks_monitor)

