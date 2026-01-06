"""
RBAC (Role-Based Access Control) Module

Implements:
- JWT token with user_id, role, allowed_IUs, allowed_GUs, expiry
- Node-level filtering for data access
- Role-based permissions
- Audit logging
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_db
from app.db.models.user import User
from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()


class RBACService:
    """RBAC service for access control and node-level filtering."""
    
    # Role definitions
    ROLES = {
        "admin": {
            "description": "Full system access",
            "permissions": ["*"]  # All permissions
        },
        "central_planner": {
            "description": "Can view and run optimizations across all nodes",
            "permissions": ["view_all", "run_optimization", "create_scenario", "approve_plan"]
        },
        "iu_manager": {
            "description": "Can manage IU/plant data and view related optimizations",
            "permissions": ["view_iu", "edit_iu_data", "view_optimization"]
        },
        "gu_manager": {
            "description": "Can manage GU/customer data and view related optimizations",
            "permissions": ["view_gu", "edit_gu_data", "view_optimization"]
        },
        "viewer": {
            "description": "Read-only access to assigned nodes",
            "permissions": ["view_iu", "view_gu", "view_optimization"]
        }
    }
    
    @staticmethod
    def create_access_token(
        user_id: str,
        username: str,
        role: str,
        allowed_ius: Optional[List[str]] = None,
        allowed_gus: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token with RBAC claims.
        
        Token contains:
        - user_id
        - username
        - role
        - allowed_IUs (list of IU IDs)
        - allowed_GUs (list of GU IDs)
        - exp (expiry)
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": username,  # Subject (username for backward compatibility)
            "user_id": user_id,
            "role": role,
            "allowed_IUs": allowed_ius or [],
            "allowed_GUs": allowed_gus or [],
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        
        logger.info(f"Access token created for user {user_id} with role {role}")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and extract claims.
        
        Returns:
            Dictionary with user_id, role, allowed_IUs, allowed_GUs, or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("sub"),
                "role": payload.get("role"),
                "allowed_IUs": payload.get("allowed_IUs", []),
                "allowed_GUs": payload.get("allowed_GUs", []),
                "exp": payload.get("exp")
            }
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    def check_permission(user_role: str, permission: str) -> bool:
        """Check if user role has the required permission."""
        role_perms = RBACService.ROLES.get(user_role, {}).get("permissions", [])
        
        # Admin has all permissions
        if "*" in role_perms:
            return True
        
        # Check specific permission
        return permission in role_perms
    
    @staticmethod
    def filter_nodes_by_access(
        nodes: List[str],
        node_type: str,  # "iu" or "gu"
        user_allowed_nodes: List[str],
        user_role: str
    ) -> List[str]:
        """
        Filter nodes based on user access.
        
        Args:
            nodes: List of node IDs to filter
            node_type: "iu" or "gu"
            user_allowed_nodes: Nodes user is allowed to access
            user_role: User's role
            
        Returns:
            Filtered list of node IDs
        """
        # Admin and central_planner can access all nodes
        if user_role in ["admin", "central_planner"]:
            return nodes
        
        # Other roles are restricted to allowed nodes
        if not user_allowed_nodes:
            return []  # No access if no allowed nodes specified
        
        # Return intersection
        return [node for node in nodes if node in user_allowed_nodes]
    
    @staticmethod
    def log_audit_action(
        db: Session,
        user_id: str,
        username: str,
        action: str,
        status: str,
        accessed_ius: Optional[List[str]] = None,
        accessed_gus: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log user action to audit log."""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user=username,
                action=action,
                status=status,
                accessed_ius=accessed_ius,
                accessed_gus=accessed_gus,
                context=context,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    Returns:
        Dictionary with user_id, username, role, allowed_IUs, allowed_GUs
    """
    token = credentials.credentials
    payload = RBACService.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.user_id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload["user_id"],
        "username": payload["username"],
        "role": payload["role"],
        "allowed_IUs": payload.get("allowed_IUs", []),
        "allowed_GUs": payload.get("allowed_GUs", [])
    }


def require_role(allowed_roles: List[str]):
    """
    Dependency to require specific role(s).
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(current_user = Depends(require_role(["admin"]))):
            ...
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency to require specific permission.
    
    Usage:
        @router.get("/optimize")
        def optimize_endpoint(current_user = Depends(require_permission("run_optimization"))):
            ...
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not RBACService.check_permission(current_user["role"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )
        return current_user
    
    return permission_checker
