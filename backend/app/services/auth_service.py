from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import get_password_hash, verify_password
from app.schemas.auth import UserCreate, UserUpdate
# TODO: import User model once created

# Placeholder user table; replace with real model later
class FakeUser:
    def __init__(self, username: str, email: str, full_name: Optional[str], role: str, hashed_password: str):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role
        self.hashed_password = hashed_password
        self.is_active = True


# In-memory stub for demo; replace with DB queries
fake_users_db = {
    "admin": FakeUser(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        hashed_password=get_password_hash("admin123"),
    )
}


def get_user_by_username(db: Session, username: str) -> Optional[FakeUser]:
    return fake_users_db.get(username)


def create_user(db: Session, user: UserCreate) -> FakeUser:
    if user.username in fake_users_db:
        raise ValueError("User already exists")
    hashed = get_password_hash(user.password)
    new_user = FakeUser(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed,
    )
    fake_users_db[user.username] = new_user
    return new_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[FakeUser]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
