from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.deps import get_db
from app.core.config import get_settings
from app.core.security import verify_password, create_access_token, verify_token
from app.schemas.auth import Token, UserCreate, User
# Role is in app.db.models.user, not app.core.rbac
# from app.core.rbac import Role  # Removed - not needed here

router = APIRouter()
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# Stub user lookup; replace with real user model later
def fake_user_lookup(username: str):
    """
    PHASE 6: Placeholder user lookup for development.
    
    This will be replaced with real user model queries when the authentication
    system is fully implemented with proper user management.
    """
    if username == "admin":
        return {"username": "admin", "role": "admin", "hashed_password": "$2b$12$placeholder"}  # dummy
    return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = fake_user_lookup(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    PHASE 6: Authenticate user with placeholder implementation.
    
    This endpoint provides basic authentication functionality for development.
    Will be enhanced with proper user management and security features.
    """
    user = fake_user_lookup(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    PHASE 6: Get current user information.
    
    Returns current user details. Will be enhanced when full user management
    system is implemented with proper user profiles and permissions.
    """
    return User(
        id=1,
        username=current_user["username"],
        email="placeholder@example.com",
        full_name="Placeholder User",
        role=current_user["role"],
        is_active=True,
    )
