"""
Service monitoring endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from src.services.health_collector import HealthCollector

# Import getter function to avoid circular import
def get_health_collector() -> HealthCollector:
    """Get the global health collector instance."""
    from src.main import health_collector
    if health_collector is None:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
    return health_collector

router = APIRouter()


class ServiceRegistration(BaseModel):
    """Service registration model."""
    name: str
    health_url: str
    ready_url: Optional[str] = None
    live_url: Optional[str] = None
    port: int
    metrics_url: Optional[str] = None


@router.get("")
async def list_services(
    health_collector: HealthCollector = Depends(get_health_collector)
) -> Dict[str, Any]:
    """List all monitored services with their health status."""
    all_health = health_collector.get_all_health()
    return {
        "services": all_health,
        "count": len(all_health)
    }


@router.get("/{service_name}")
async def get_service_health(
    service_name: str,
    health_collector: HealthCollector = Depends(get_health_collector)
) -> Dict[str, Any]:
    """Get health status for a specific service."""
    health = health_collector.get_service_health(service_name)
    if not health:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    return health


@router.get("/{service_name}/metrics")
async def get_service_metrics(
    service_name: str,
    metrics_collector = None  # Will be injected
) -> Dict[str, Any]:
    """Get metrics for a specific service."""
    # This will be implemented with metrics_collector dependency
    return {"service": service_name, "metrics": {}}


@router.get("/{service_name}/tests")
async def get_service_tests(
    service_name: str,
    test_collector = None  # Will be injected
) -> Dict[str, Any]:
    """Get test results for a specific service."""
    # This will be implemented with test_collector dependency
    return {"service": service_name, "tests": {}}


@router.post("/register")
async def register_service(
    registration: ServiceRegistration,
    health_collector: HealthCollector = Depends(get_health_collector)
) -> Dict[str, Any]:
    """Register a new service for monitoring."""
    service_config = {
        "name": registration.name,
        "health_url": registration.health_url,
        "ready_url": registration.ready_url or registration.health_url.replace("/health", "/ready"),
        "live_url": registration.live_url or registration.health_url.replace("/health", "/live"),
        "port": registration.port,
        "metrics_url": registration.metrics_url
    }
    
    health_collector.register_service(registration.name, service_config)
    
    return {
        "status": "registered",
        "service": registration.name,
        "config": service_config
    }

