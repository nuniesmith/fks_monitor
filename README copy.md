# FKS Monitor

A monitoring service for the FKS ecosystem that aggregates health check data from all FKS services and provides metrics for Prometheus and Grafana.

## Overview

`fks_monitor` periodically polls health endpoints of other FKS services (like `/health` and `/ready`) and consolidates the data. It exposes this information via an API for `fks_main` to consume and provides a Prometheus metrics endpoint for integration with monitoring tools.

## Setup

### Installation

1. **Clone the Repository**: If not already done, clone the FKS repository to your local machine.
2. **Navigate to Monitor Directory**: `cd /path/to/fks/repo/core/monitor`
3. **Install Dependencies**: Run `pip install -r requirements.txt`
4. **Run the Service**: Start the service with `python app.py` or use a process manager like `uvicorn` directly: `uvicorn app:app --host 0.0.0.0 --port 8002`

### Configuration

- **Service Endpoints**: By default, `fks_monitor` monitors predefined services. Add or modify services in `SERVICE_ENDPOINTS` dictionary in `app.py` or use the `/monitor/register` endpoint to dynamically add services.
- **Monitoring Interval**: The default interval for health checks is 30 seconds, adjustable in `app.py` under `update_health_data()` function.
- **Port**: The service runs on port `8002` by default. Change this via the `PORT` environment variable if needed.

## Usage

### API Endpoints

- **Health Check**: `GET /health` - Returns the health status of `fks_monitor` itself.
- **Readiness Check**: `GET /ready` - Indicates if `fks_monitor` is ready to serve requests.
- **All Services Health**: `GET /monitor/services` - Returns detailed health data for all monitored services.
- **Specific Service Health**: `GET /monitor/services/{service_name}` - Get health data for a specific service.
- **Health Summary**: `GET /monitor/summary` - Provides a summarized view of all services' health status.
- **Register Service**: `POST /monitor/register` - Register a new service for monitoring. Requires JSON payload with `name` and `endpoint`.
- **Metrics**: `GET /metrics` - Prometheus-compatible metrics endpoint for scraping by Prometheus server.

### Example API Calls

- **Get All Services Health**:
  ```bash
  curl http://localhost:8002/monitor/services
  ```
- **Register a New Service**:
  ```bash
  curl -X POST http://localhost:8002/monitor/register -H "Content-Type: application/json" -d '{"name": "new-service", "endpoint": "http://new-service:8080/health"}'
  ```

### Prometheus and Grafana Integration

- **Prometheus**: Configure Prometheus to scrape metrics from `http://localhost:8002/metrics`. A sample `prometheus.yml` configuration is provided.
- **Grafana**: Import the provided `grafana_dashboard.json` to visualize FKS services' status and latency metrics. Ensure Grafana is connected to your Prometheus data source.

## Development

### Contributing

Contributions to `fks_monitor` are welcome. Please follow these steps:
1. Fork the repository or create a branch.
2. Make your changes and test them locally.
3. Submit a pull request with a clear description of your changes.

### Testing

To test the service:
1. Run the application locally.
2. Use tools like `curl` or Postman to interact with the API endpoints.
3. Verify health data aggregation by simulating different service states if possible.
