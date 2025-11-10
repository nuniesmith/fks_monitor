"""
Metrics endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from src.services.metrics_collector import MetricsCollector

# Import getter function to avoid circular import
def get_metrics_collector():
    """Get the global metrics collector instance."""
    from src.main import metrics_collector
    if metrics_collector is None:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    return metrics_collector

router = APIRouter()


@router.get("")
async def get_all_metrics(
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
) -> Dict[str, Any]:
    """Get all aggregated metrics."""
    return metrics_collector.get_all_metrics()


@router.get("/prometheus")
async def prometheus_metrics() -> Response:
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

