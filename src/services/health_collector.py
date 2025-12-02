"""
Health Check Collector Service
Polls health endpoints from all FKS services and aggregates status.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import time

logger = logging.getLogger(__name__)


class HealthCollector:
    """Collects health status from all FKS services."""
    
    def __init__(
        self,
        services_config: str = "/app/config/services.yaml",
        update_interval: int = 30
    ):
        """Initialize health collector."""
        self.services_config = Path(services_config)
        self.update_interval = update_interval
        self.services: Dict[str, Dict[str, Any]] = {}
        self.health_data: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Load service configuration
        self._load_services()
    
    def _load_services(self):
        """Load services from configuration file."""
        if not self.services_config.exists():
            logger.warning(f"Services config not found: {self.services_config}, using defaults")
            self.services = self._get_default_services()
            return
        
        try:
            with open(self.services_config, "r") as f:
                config = yaml.safe_load(f)
                self.services = config.get("services", {})
        except Exception as e:
            logger.error(f"Error loading services config: {e}")
            self.services = self._get_default_services()
    
    def _get_default_services(self) -> Dict[str, Dict[str, Any]]:
        """Get default FKS services configuration."""
        return {
            "fks_api": {
                "name": "fks_api",
                "health_url": "http://fks-api:8001/health",
                "ready_url": "http://fks-api:8001/ready",
                "live_url": "http://fks-api:8001/live",
                "port": 8001
            },
            "fks_app": {
                "name": "fks_app",
                "health_url": "http://fks-app:8002/health",
                "ready_url": "http://fks-app:8002/ready",
                "live_url": "http://fks-app:8002/live",
                "port": 8002
            },
            "fks_data": {
                "name": "fks_data",
                "health_url": "http://fks-data:8003/health",
                "ready_url": "http://fks-data:8003/ready",
                "live_url": "http://fks-data:8003/live",
                "port": 8003
            },
            "fks_execution": {
                "name": "fks_execution",
                "health_url": "http://fks-execution:8006/health",
                "ready_url": "http://fks-execution:8006/ready",
                "live_url": "http://fks-execution:8006/live",
                "port": 8006
            },
            "fks_web": {
                "name": "fks_web",
                "health_url": "http://fks-web:8000/health",
                "ready_url": "http://fks-web:8000/ready",
                "live_url": "http://fks-web:8000/live",
                "port": 8000
            },
            "fks_ai": {
                "name": "fks_ai",
                "health_url": "http://fks-ai:8007/health",
                "ready_url": "http://fks-ai:8007/ready",
                "live_url": "http://fks-ai:8007/live",
                "port": 8007
            },
            "fks_analyze": {
                "name": "fks_analyze",
                "health_url": "http://fks-analyze:8008/health",
                "ready_url": "http://fks-analyze:8008/ready",
                "live_url": "http://fks-analyze:8008/live",
                "port": 8008
            },
            "fks_monitor": {
                "name": "fks_monitor",
                "health_url": "http://fks-monitor:8013/health",
                "ready_url": "http://fks-monitor:8013/ready",
                "live_url": "http://fks-monitor:8013/live",
                "port": 8013
            },
            "fks_crypto": {
                "name": "fks_crypto",
                "health_url": "http://fks-crypto:8014/health",
                "ready_url": "http://fks-crypto:8014/ready",
                "live_url": "http://fks-crypto:8014/live",
                "port": 8014
            }
        }
    
    async def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service."""
        health_url = service_config.get("health_url")
        ready_url = service_config.get("ready_url", health_url.replace("/health", "/ready"))
        live_url = service_config.get("live_url", health_url.replace("/health", "/live"))
        
        result = {
            "service": service_name,
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            # Check health endpoint
            try:
                async with session.get(health_url) as response:
                    result["checks"]["health"] = {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "status_code": response.status,
                        "response_time_ms": round(response.headers.get("X-Response-Time", 0), 2)
                    }
                    if response.status == 200:
                        result["checks"]["health"]["data"] = await response.json()
            except Exception as e:
                result["checks"]["health"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Check readiness endpoint
            try:
                async with session.get(ready_url) as response:
                    result["checks"]["ready"] = {
                        "status": "ready" if response.status == 200 else "not_ready",
                        "status_code": response.status
                    }
            except Exception as e:
                result["checks"]["ready"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Check liveness endpoint
            try:
                async with session.get(live_url) as response:
                    result["checks"]["live"] = {
                        "status": "alive" if response.status == 200 else "dead",
                        "status_code": response.status
                    }
            except Exception as e:
                result["checks"]["live"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall status
        health_status = result["checks"].get("health", {}).get("status")
        ready_status = result["checks"].get("ready", {}).get("status")
        live_status = result["checks"].get("live", {}).get("status")
        
        if health_status == "healthy" and ready_status == "ready" and live_status == "alive":
            result["status"] = "healthy"
        elif live_status == "alive":
            result["status"] = "degraded"
        else:
            result["status"] = "unhealthy"
        
        return result
    
    async def update_all_health(self):
        """Update health status for all services."""
        tasks = []
        for service_name, service_config in self.services.items():
            tasks.append(self.check_service_health(service_name, service_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error checking service health: {result}")
                continue
            self.health_data[result["service"]] = result
        
        logger.debug(f"Updated health for {len(self.health_data)} services")
    
    async def _background_task(self):
        """Background task to periodically update health."""
        while self.running:
            try:
                await self.update_all_health()
            except Exception as e:
                logger.error(f"Error in health update task: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the health collector."""
        if self.running:
            return
        
        self.running = True
        # Initial update
        await self.update_all_health()
        # Start background task
        self._task = asyncio.create_task(self._background_task())
        logger.info("Health collector started")
    
    async def stop(self):
        """Stop the health collector."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health collector stopped")
    
    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Get all health data."""
        return self.health_data.copy()
    
    def get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get health for a specific service."""
        return self.health_data.get(service_name)
    
    def register_service(self, service_name: str, service_config: Dict[str, Any]):
        """Register a new service for monitoring."""
        self.services[service_name] = service_config
        logger.info(f"Registered service: {service_name}")

