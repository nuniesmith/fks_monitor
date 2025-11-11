"""
Test Collector Service
Collects test results and coverage from all FKS services.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import json
import os

logger = logging.getLogger(__name__)


class TestCollector:
    """Collects test results from all FKS services."""
    
    def __init__(
        self,
        services_config: str = "/app/config/services.yaml",
        update_interval: int = 300,
        google_ai_key: str = ""
    ):
        """Initialize test collector."""
        self.services_config = Path(services_config)
        self.update_interval = update_interval
        self.google_ai_key = google_ai_key
        self.services: Dict[str, Dict[str, Any]] = {}
        self.test_data: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Load service configuration
        self._load_services()
    
    def _load_services(self):
        """Load services from configuration file."""
        if not self.services_config.exists():
            logger.warning(f"Services config not found: {self.services_config}")
            self.services = {}
            return
        
        try:
            with open(self.services_config, "r") as f:
                config = yaml.safe_load(f)
                self.services = config.get("services", {})
        except Exception as e:
            logger.error(f"Error loading services config: {e}")
            self.services = {}
    
    async def check_service_tests(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check test status for a service."""
        # This would typically check the service's test endpoint or run tests
        # For now, return a placeholder structure
        
        result = {
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": 0,
            "passing_tests": 0,
            "failing_tests": 0,
            "coverage": 0.0,
            "status": "unknown"
        }
        
        # In a real implementation, this would:
        # 1. Check if service has a /tests endpoint
        # 2. Or run tests in the service's test directory
        # 3. Parse test results
        # 4. Get coverage reports
        
        return result
    
    async def update_all_tests(self):
        """Update test results for all services."""
        tasks = []
        for service_name, service_config in self.services.items():
            tasks.append(self.check_service_tests(service_name, service_config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error checking service tests: {result}")
                continue
            self.test_data[result["service"]] = result
        
        logger.debug(f"Updated test results for {len(self.test_data)} services")
    
    async def _background_task(self):
        """Background task to periodically update tests."""
        while self.running:
            try:
                await self.update_all_tests()
            except Exception as e:
                logger.error(f"Error in test update task: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the test collector."""
        if self.running:
            return
        
        self.running = True
        # Initial update
        await self.update_all_tests()
        # Start background task
        self._task = asyncio.create_task(self._background_task())
        logger.info("Test collector started")
    
    async def stop(self):
        """Stop the test collector."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Test collector stopped")
    
    def get_all_tests(self) -> Dict[str, Dict[str, Any]]:
        """Get all test data."""
        return self.test_data.copy()
    
    def get_service_tests(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get test results for a specific service."""
        return self.test_data.get(service_name)

