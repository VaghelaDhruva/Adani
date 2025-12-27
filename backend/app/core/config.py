from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Clinker Supply Chain Optimization"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # JWT
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Routing APIs
    ROUTING_PROVIDER: str = "auto"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    ORS_BASE_URL: str = "https://api.openrouteservice.org"
    ORS_API_KEY: Optional[str] = None
    ROUTING_TIMEOUT_SECONDS: int = 10
    ROUTING_MAX_RETRIES: int = 3

    # Demand streaming
    DEMAND_SOURCE_TYPE: str = "rest"
    DEMAND_POLL_URL: Optional[str] = None
    DEMAND_POLL_INTERVAL_SECONDS: int = 300

    # Kafka (optional)
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = None
    KAFKA_DEMAND_TOPIC: str = "clinker_demand"
    KAFKA_GROUP_ID: str = "clinker-consumer"

    # Celery
    BROKER_URL: str = Field(..., env="BROKER_URL")
    RESULT_BACKEND: str = Field(..., env="RESULT_BACKEND")

    # Solver
    DEFAULT_SOLVER: str = "cbc"
    SOLVER_TIME_LIMIT_SECONDS: int = 600
    SOLVER_MIP_GAP: float = 0.01

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
