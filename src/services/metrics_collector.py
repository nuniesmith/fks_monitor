"""
Metrics Collector Service
Collects metrics from Prometheus and Grafana.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects metrics from Prometheus and Grafana."""
    
    def __init__(
        self,
        prometheus_url: str = "http://prometheus:9090",
        grafana_url: str = "http://grafana:3000",
        update_interval: int = 60
    ):
        """Initialize metrics collector."""
        self.prometheus_url = prometheus_url.rstrip("/")
        self.grafana_url = grafana_url.rstrip("/")
        self.update_interval = update_interval
        self.metrics_data: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def fetch_prometheus_metrics(self, query: str) -> Dict[str, Any]:
        """Fetch metrics from Prometheus."""
        url = f"{self.prometheus_url}/api/v1/query"
        params = {"query": query}
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Prometheus query failed: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching Prometheus metrics: {e}")
            return {}
    
    async def fetch_all_metrics(self):
        """Fetch metrics for all FKS services."""
        # Common Prometheus queries for FKS services
        queries = {
            "http_requests_total": 'sum(rate(http_requests_total[5m])) by (service)',
            "http_request_duration_seconds": 'sum(rate(http_request_duration_seconds_sum[5m])) by (service)',
            "service_health": 'up{job=~"fks-.*"}',
            "cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{name=~"fks-.*"}[5m])) by (name)',
            "memory_usage": 'sum(container_memory_usage_bytes{name=~"fks-.*"}) by (name)',
        }
        
        metrics = {}
        for metric_name, query in queries.items():
            result = await self.fetch_prometheus_metrics(query)
            if result:
                metrics[metric_name] = result
        
        self.metrics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "prometheus",
            "metrics": metrics
        }
    
    async def fetch_grafana_dashboards(self) -> List[Dict[str, Any]]:
        """Fetch dashboard data from Grafana."""
        # This would require Grafana API authentication
        # For now, return empty list
        return []
    
    async def update_all_metrics(self):
        """Update all metrics."""
        await self.fetch_all_metrics()
        logger.debug("Updated metrics data")
    
    async def _background_task(self):
        """Background task to periodically update metrics."""
        while self.running:
            try:
                await self.update_all_metrics()
            except Exception as e:
                logger.error(f"Error in metrics update task: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the metrics collector."""
        if self.running:
            return
        
        self.running = True
        # Initial update
        await self.update_all_metrics()
        # Start background task
        self._task = asyncio.create_task(self._background_task())
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop the metrics collector."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics data."""
        return self.metrics_data.copy()
    
    def get_service_metrics(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific service."""
        # Extract service-specific metrics from aggregated data
        if not self.metrics_data:
            return None
        
        service_metrics = {}
        metrics = self.metrics_data.get("metrics", {})
        
        for metric_name, metric_data in metrics.items():
            # Filter metrics for this service
            if isinstance(metric_data, dict) and "data" in metric_data:
                service_data = [
                    item for item in metric_data["data"].get("result", [])
                    if service_name in str(item)
                ]
                if service_data:
                    service_metrics[metric_name] = service_data
        
        return {
            "service": service_name,
            "timestamp": self.metrics_data.get("timestamp"),
            "metrics": service_metrics
        }

