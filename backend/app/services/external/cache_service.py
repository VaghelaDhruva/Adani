from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from sqlalchemy import Column, String, Float, DateTime, Text
from datetime import datetime, timedelta


class RouteCache(Base):
    __tablename__ = "route_cache"
    id = Column(String, primary_key=True)  # e.g., "origin;destination"
    distance_km = Column(Float)
    duration_seconds = Column(Float)
    provider = Column(String)
    raw_response = Column(Text)  # optional full JSON for debugging
    created_at = Column(DateTime, server_default="now()")
    expires_at = Column(DateTime)


Base.metadata.create_all(bind=engine)


def get_cached_route(origin: str, destination: str, db: Session) -> Optional[Dict[str, Any]]:
    """Return cached route if not expired."""
    cache_key = f"{origin};{destination}"
    record = db.query(RouteCache).filter(RouteCache.id == cache_key).filter(RouteCache.expires_at > datetime.utcnow()).first()
    if record:
        return {
            "distance_km": record.distance_km,
            "duration_seconds": record.duration_seconds,
            "provider": record.provider,
        }
    return None


def cache_route(origin: str, destination: str, distance_km: float, duration_seconds: float, provider: str, db: Session, ttl_hours: int = 24):
    """Cache a route result with TTL."""
    cache_key = f"{origin};{destination}"
    expires = datetime.utcnow() + timedelta(hours=ttl_hours)
    record = RouteCache(
        id=cache_key,
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        provider=provider,
        expires_at=expires,
    )
    db.merge(record)  # upsert
    db.commit()
