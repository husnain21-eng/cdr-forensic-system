"""Role-Based Access Control."""
from core.constants import ROLE_PERMISSIONS


class PermissionDenied(Exception):
    """Raised when a role lacks the required permission."""
    pass


def has_permission(role: str, permission: str) -> bool:
    """Return True if the role is granted the permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def require(role: str, permission: str) -> None:
    """Raise PermissionDenied if the role lacks the permission."""
    if not has_permission(role, permission):
        raise PermissionDenied(
            f"Role '{role}' is not authorized for '{permission}'."
        )