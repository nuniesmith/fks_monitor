"""
Configuration management for FKS Monitor Service.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Service Configuration
    SERVICE_NAME: str = "fks_monitor"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8009
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "https://fkstrading.xyz",
        "https://api.fkstrading.xyz",
    ]
    
    # Service Discovery
    SERVICES_CONFIG: str = "/app/config/services.yaml"
    AUTO_DISCOVER: bool = True
    
    # Prometheus & Grafana
    PROMETHEUS_URL: str = "http://prometheus:9090"
    GRAFANA_URL: str = "http://grafana:3000"
    
    # Update Intervals (seconds)
    HEALTH_CHECK_INTERVAL: int = 30
    METRICS_UPDATE_INTERVAL: int = 60
    TEST_CHECK_INTERVAL: int = 300  # 5 minutes
    
    # Google AI API (for test analysis)
    GOOGLE_AI_API_KEY: str = ""
    
    # Timeouts
    HEALTH_CHECK_TIMEOUT: int = 5
    METRICS_FETCH_TIMEOUT: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

