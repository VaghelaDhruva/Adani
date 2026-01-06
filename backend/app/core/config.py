"""
Configuration settings for the application.
"""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # Try alternative import path
        from pydantic.v1 import BaseSettings
    except ImportError:
        # Last resort - create a minimal BaseSettings class
        from pydantic import BaseModel
        
        class BaseSettings(BaseModel):
            class Config:
                env_file = ".env"
                case_sensitive = True


class Settings(BaseSettings):
    """Application settings."""
    
    # Basic app settings
    PROJECT_NAME: str = "Clinker Supply Chain Optimization"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./clinker_supply_chain.db"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_SECRET_KEY: str = "your-secret-key-here-change-in-production"  # For JWT tokens
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ERP Integration Settings
    SAP_BASE_URL: Optional[str] = None
    SAP_USERNAME: Optional[str] = None
    SAP_PASSWORD: Optional[str] = None
    SAP_CLIENT: Optional[str] = None
    
    ORACLE_HOST: Optional[str] = None
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: Optional[str] = None
    ORACLE_USERNAME: Optional[str] = None
    ORACLE_PASSWORD: Optional[str] = None
    
    # External API Settings
    WEATHER_API_KEY: Optional[str] = None
    MARKET_DATA_API_KEY: Optional[str] = None
    FUEL_PRICE_API_KEY: Optional[str] = None
    
    # PHASE 2: Routing API Settings
    ROUTING_PROVIDER: str = "auto"
    OSRM_BASE_URL: str = "http://router.project-osrm.org"
    ORS_BASE_URL: str = "https://api.openrouteservice.org"
    ORS_API_KEY: Optional[str] = None
    ROUTING_TIMEOUT_SECONDS: int = 30
    ROUTING_MAX_RETRIES: int = 3
    ROUTING_RETRY_DELAY: float = 1.0  # Initial delay in seconds
    ROUTING_RETRY_BACKOFF: float = 2.0  # Exponential backoff multiplier
    
    # Demand Streaming Settings
    DEMAND_SOURCE_TYPE: str = "rest"
    DEMAND_POLL_URL: str = "https://api.example.com/demand"
    DEMAND_POLL_INTERVAL_SECONDS: int = 300
    
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_DEMAND_TOPIC: str = "clinker_demand"
    KAFKA_GROUP_ID: str = "clinker-consumer"
    
    # Celery Settings
    BROKER_URL: str = "redis://localhost:6379/0"
    RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Real-time Streams Settings
    IOT_BROKER_URL: Optional[str] = None
    IOT_USERNAME: Optional[str] = None
    IOT_PASSWORD: Optional[str] = None
    
    REDIS_URL: str = "redis://localhost:6379"
    
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_USERNAME: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    # Optimization Settings
    DEFAULT_SOLVER: str = "cbc"
    SOLVER_TIME_LIMIT_SECONDS: int = 600
    SOLVER_MIP_GAP: float = 0.01
    DEFAULT_TIME_LIMIT: int = 600
    DEFAULT_MIP_GAP: float = 0.01
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env file


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()