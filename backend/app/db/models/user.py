"""
User and Role Models for RBAC

Supports:
- Admin
- Central Planner
- IU Manager
- GU Manager
- Viewer
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """User model with RBAC support."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Role
    role = Column(String(50), nullable=False, index=True)  # admin, central_planner, iu_manager, gu_manager, viewer
    
    # Node-level access control
    allowed_ius = Column(JSON, nullable=True)  # List of IU/plant IDs user can access
    allowed_gus = Column(JSON, nullable=True)  # List of GU/customer IDs user can access
    
    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")


class Role(Base):
    """Role definition table."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # Permissions (stored as JSON for flexibility)
    permissions = Column(JSON, nullable=True)  # List of permission strings
    
    created_at = Column(DateTime, server_default=func.now())


class UserSession(Base):
    """Active user sessions for token management."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False, index=True)
    token_id = Column(String(255), unique=True, nullable=False, index=True)  # JWT jti claim
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # User agent and IP for security
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)

