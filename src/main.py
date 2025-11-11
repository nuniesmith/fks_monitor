"""
FKS Monitor Service - Main Application
Centralized monitoring service for all FKS services.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import os

from src.core.config import get_settings
from src.services.health_collector import HealthCollector
from src.services.metrics_collector import MetricsCollector
from src.services.test_collector import TestCollector
from src.api.routes import health, services, metrics, tests

logger = logging.getLogger(__name__)

# Global service instances
health_collector: Optional[HealthCollector] = None
metrics_collector: Optional[MetricsCollector] = None
test_collector: Optional[TestCollector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global health_collector, metrics_collector, test_collector
    
    # Startup
    logger.info("Starting FKS Monitor Service...")
    settings = get_settings()
    
    # Initialize collectors
    health_collector = HealthCollector(
        services_config=settings.SERVICES_CONFIG,
        update_interval=settings.HEALTH_CHECK_INTERVAL
    )
    metrics_collector = MetricsCollector(
        prometheus_url=settings.PROMETHEUS_URL,
        grafana_url=settings.GRAFANA_URL,
        update_interval=settings.METRICS_UPDATE_INTERVAL
    )
    test_collector = TestCollector(
        services_config=settings.SERVICES_CONFIG,
        update_interval=settings.TEST_CHECK_INTERVAL,
        google_ai_key=settings.GOOGLE_AI_API_KEY
    )
    
    # Start background tasks
    await health_collector.start()
    await metrics_collector.start()
    await test_collector.start()
    
    logger.info("FKS Monitor Service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FKS Monitor Service...")
    if health_collector:
        await health_collector.stop()
    if metrics_collector:
        await metrics_collector.stop()
    if test_collector:
        await test_collector.stop()
    logger.info("FKS Monitor Service stopped")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="FKS Monitor Service",
    description="Centralized monitoring service for FKS platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(tests.router, prefix="/api/v1/tests", tags=["tests"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "service": "fks_monitor",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "services": "/api/v1/services",
            "metrics": "/api/v1/metrics",
            "tests": "/api/v1/tests",
            "prometheus": "/metrics"
        }
    }


@app.get("/api/v1/summary")
async def get_summary() -> Dict[str, Any]:
    """Get overall system health summary."""
    if not health_collector or not metrics_collector or not test_collector:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Get aggregated data
    all_health = health_collector.get_all_health()
    all_metrics = metrics_collector.get_all_metrics()
    all_tests = test_collector.get_all_tests()
    
    # Calculate summary
    total_services = len(all_health)
    healthy_services = sum(1 for h in all_health.values() if h.get("status") == "healthy")
    unhealthy_services = total_services - healthy_services
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "total": total_services,
            "healthy": healthy_services,
            "unhealthy": unhealthy_services,
            "health_percentage": round((healthy_services / total_services * 100) if total_services > 0 else 0, 2)
        },
        "metrics": {
            "services_with_metrics": len(all_metrics),
            "total_metrics": sum(len(m.get("metrics", [])) for m in all_metrics.values())
        },
        "tests": {
            "services_with_tests": len(all_tests),
            "total_tests": sum(t.get("total_tests", 0) for t in all_tests.values()),
            "passing_tests": sum(t.get("passing_tests", 0) for t in all_tests.values()),
            "coverage_avg": round(sum(t.get("coverage", 0) for t in all_tests.values()) / len(all_tests) if all_tests else 0, 2)
        }
    }


def get_health_collector() -> HealthCollector:
    """Dependency to get health collector."""
    if health_collector is None:
        raise HTTPException(status_code=503, detail="Health collector not initialized")
    return health_collector


def get_metrics_collector() -> MetricsCollector:
    """Dependency to get metrics collector."""
    if metrics_collector is None:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    return metrics_collector


def get_test_collector() -> TestCollector:
    """Dependency to get test collector."""
    if test_collector is None:
        raise HTTPException(status_code=503, detail="Test collector not initialized")
    return test_collector

