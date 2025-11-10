from fastapi import FastAPI, Response, status, HTTPException

from prometheus_client import make_asgi_app, Counter, Gauge, Histogram
from typing import Dict, Any, List
import aiohttp
import asyncio
import os
import logging
import json
from pydantic import BaseModel

app = FastAPI(title="FKS Monitor", description="Monitoring service for FKS ecosystem")

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
health_check_requests = Counter('health_check_requests_total', 'Total health check requests')
health_check_success = Counter('health_check_success_total', 'Successful health checks', ['service'])
health_check_failure = Counter('health_check_failure_total', 'Failed health checks', ['service'])
service_status = Gauge('service_status', 'Status of monitored services (1=healthy, 0=unhealthy)', ['service'])
health_check_latency = Histogram('health_check_latency_seconds', 'Health check latency', ['service'])

# Service endpoints to monitor (will be configurable)
SERVICE_ENDPOINTS = {
    "fks-execution": "http://fks-execution:8000/health",
    "fks-web": "http://fks-web:8000/health",
    "fks-api": "http://fks-api:8000/health"
}

# Store health data
health_data: Dict[str, Any] = {}

# Configuration for dynamic service discovery (placeholder for future implementation)
SERVICE_DISCOVERY_ENABLED = os.getenv("SERVICE_DISCOVERY", "false").lower() == "true"

class ServiceHealth(BaseModel):
    status: str
    data: Dict[str, Any] = {}
    error: str = ""
    latency: float = 0.0

class ServiceRegistration(BaseModel):
    name: str
    endpoint: str

@app.get("/health")
async def health_check():
    """Basic health check for fks_monitor itself."""
    return {"status": "healthy", "service": "fks-monitor"}

@app.get("/ready")
async def readiness_check():
    """Readiness check for fks_monitor."""
    return {"status": "ready", "service": "fks-monitor"}

@app.get("/monitor/services", response_model=Dict[str, Any])
async def get_services_health():
    """Get aggregated health status of all monitored services."""
    overall_status = "healthy"
    for service, data in health_data.items():
        if data.get("status") != "healthy":
            overall_status = "degraded"
            break
    return {
        "service": "fks-monitor",
        "status": overall_status,
        "services": health_data
    }

@app.get("/monitor/services/{service_name}", response_model=Dict[str, Any])
async def get_service_health(service_name: str):
    """Get health status of a specific service."""
    if service_name not in health_data:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    return {
        "service": service_name,
        "health": health_data[service_name]
    }

@app.get("/monitor/summary", response_model=Dict[str, Any])
async def get_health_summary():
    """Get a summarized view of all services' health status."""
    summary = {}
    for service, data in health_data.items():
        summary[service] = {
            "status": data.get("status"),
            "latency": data.get("latency", 0.0)
        }
    overall_status = "healthy" if all(d.get("status") == "healthy" for d in health_data.values()) else "degraded"
    return {
        "overall_status": overall_status,
        "services": summary
    }

@app.post("/monitor/register", response_model=Dict[str, str])
async def register_service(service: ServiceRegistration):
    """Register a new service endpoint for monitoring."""
    service_name = service.name
    endpoint = service.endpoint
    if not service_name or not endpoint:
        return {"status": "error", "message": "Missing name or endpoint"}
    SERVICE_ENDPOINTS[service_name] = endpoint
    logger.info(f"Registered new service: {service_name} at {endpoint}")
    return {"status": "success", "message": f"Registered {service_name}"}

async def fetch_health(service_name: str, endpoint: str) -> Dict[str, Any]:
    """Fetch health data from a service endpoint."""
    health_check_requests.inc()
    start_time = asyncio.get_event_loop().time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, timeout=5) as response:
                latency = asyncio.get_event_loop().time() - start_time
                health_check_latency.labels(service=service_name).observe(latency)
                if response.status == 200:
                    data = await response.json()
                    health_check_success.labels(service=service_name).inc()
                    service_status.labels(service=service_name).set(1)
                    return {"status": "healthy", "data": data, "latency": latency}
                else:
                    health_check_failure.labels(service=service_name).inc()
                    service_status.labels(service=service_name).set(0)
                    return {"status": "unhealthy", "error": f"Status code {response.status}", "latency": latency}
    except Exception as e:
        latency = asyncio.get_event_loop().time() - start_time
        health_check_latency.labels(service=service_name).observe(latency)
        logger.error(f"Error fetching health from {endpoint}: {str(e)}")
        health_check_failure.labels(service=service_name).inc()
        service_status.labels(service=service_name).set(0)
        return {"status": "unhealthy", "error": str(e), "latency": latency}

async def discover_services() -> Dict[str, str]:
    """Placeholder for dynamic service discovery."""
    # Future implementation could query a service registry or use DNS-SD
    return {}

async def update_health_data():
    """Periodically update health data from all services."""
    while True:
        current_endpoints = SERVICE_ENDPOINTS.copy()
        if SERVICE_DISCOVERY_ENABLED:
            discovered = await discover_services()
            current_endpoints.update(discovered)
            logger.info(f"Discovered services: {list(discovered.keys())}")
        for service, endpoint in current_endpoints.items():
            health_data[service] = await fetch_health(service, endpoint)
            logger.info(f"Updated health for {service}: {health_data[service]['status']}")
        await asyncio.sleep(30)  # Check every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    asyncio.create_task(update_health_data())
    logger.info("Started background health check task")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8002)))
