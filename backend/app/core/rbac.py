from enum import Enum
from typing import List, Set


class Role(str, Enum):
    ADMIN = "admin"
    PLANNER = "planner"
    VIEWER = "viewer"


# Minimal permission model
class Permission(str, Enum):
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    RUN_OPTIMIZATION = "run_optimization"
    MANAGE_SCENARIOS = "manage_scenarios"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT = "view_audit"


ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.RUN_OPTIMIZATION,
        Permission.MANAGE_SCENARIOS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT,
    },
    Role.PLANNER: {
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.RUN_OPTIMIZATION,
        Permission.MANAGE_SCENARIOS,
    },
    Role.VIEWER: {
        Permission.READ_DATA,
    },
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
