"""
RBAC Manager and Decorators
"""

from typing import List, Optional
from fastapi import Request, HTTPException, status
from functools import wraps
import logging

from .roles import RoleHierarchy, Permission
from ..security.audit import AuditLogger

logger = logging.getLogger(__name__)


class RBACManager:
    """
    Central RBAC manager for permission checking
    """

    def __init__(
        self,
        role_hierarchy: Optional[RoleHierarchy] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize RBACManager

        Args:
            role_hierarchy: RoleHierarchy instance (creates default if not provided)
            audit_logger: Optional AuditLogger for audit logging
        """
        self.role_hierarchy = role_hierarchy or RoleHierarchy()
        self.audit_logger = audit_logger

        logger.info("RBACManager initialized")

    def check_permission(
        self,
        user_roles: List[str],
        required_permission: Permission,
        user_id: Optional[str] = None,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if user has required permission

        Args:
            user_roles: User's roles
            required_permission: Required permission
            user_id: User identifier (for audit logging)
            resource: Resource being accessed (for audit logging)

        Returns:
            True if permission granted
        """
        has_permission = self.role_hierarchy.has_permission(
            user_roles,
            required_permission
        )

        # Audit log
        if self.audit_logger and user_id:
            self.audit_logger.log_authorization(
                user_id=user_id,
                resource=resource or "unknown",
                action=required_permission.value,
                granted=has_permission,
                required_permissions=[required_permission.value]
            )

        return has_permission

    def check_any_permission(
        self,
        user_roles: List[str],
        required_permissions: List[Permission],
        user_id: Optional[str] = None,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if user has any of the required permissions

        Args:
            user_roles: User's roles
            required_permissions: List of required permissions
            user_id: User identifier (for audit logging)
            resource: Resource being accessed (for audit logging)

        Returns:
            True if any permission granted
        """
        has_permission = self.role_hierarchy.has_any_permission(
            user_roles,
            required_permissions
        )

        if self.audit_logger and user_id:
            self.audit_logger.log_authorization(
                user_id=user_id,
                resource=resource or "unknown",
                action="any_of:" + ",".join(p.value for p in required_permissions),
                granted=has_permission,
                required_permissions=[p.value for p in required_permissions]
            )

        return has_permission

    def check_all_permissions(
        self,
        user_roles: List[str],
        required_permissions: List[Permission],
        user_id: Optional[str] = None,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if user has all required permissions

        Args:
            user_roles: User's roles
            required_permissions: List of required permissions
            user_id: User identifier (for audit logging)
            resource: Resource being accessed (for audit logging)

        Returns:
            True if all permissions granted
        """
        has_permission = self.role_hierarchy.has_all_permissions(
            user_roles,
            required_permissions
        )

        if self.audit_logger and user_id:
            self.audit_logger.log_authorization(
                user_id=user_id,
                resource=resource or "unknown",
                action="all_of:" + ",".join(p.value for p in required_permissions),
                granted=has_permission,
                required_permissions=[p.value for p in required_permissions]
            )

        return has_permission

    def get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """
        Get all effective permissions for user

        Args:
            user_roles: User's roles

        Returns:
            List of permission strings
        """
        permissions = self.role_hierarchy.get_effective_permissions(user_roles)
        return [p.value for p in permissions]


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def init_rbac(
    role_hierarchy: Optional[RoleHierarchy] = None,
    audit_logger: Optional[AuditLogger] = None
):
    """
    Initialize global RBAC manager

    Args:
        role_hierarchy: RoleHierarchy instance
        audit_logger: Optional AuditLogger
    """
    global _rbac_manager
    _rbac_manager = RBACManager(role_hierarchy, audit_logger)
    logger.info("Global RBAC manager initialized")


def get_rbac_manager() -> RBACManager:
    """
    Get global RBAC manager

    Returns:
        RBACManager instance

    Raises:
        RuntimeError: If RBAC not initialized
    """
    if _rbac_manager is None:
        raise RuntimeError("RBAC not initialized. Call init_rbac() first.")
    return _rbac_manager


def require_permission(
    permission: Permission,
    resource_name: Optional[str] = None
):
    """
    Decorator to require specific permission for endpoint

    Args:
        permission: Required permission
        resource_name: Optional resource name for audit logging

    Example:
        @require_permission(Permission.FILINGS_WRITE, "filings")
        async def create_filing(request: Request):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get user roles from request state
            user_roles = getattr(request.state, 'roles', [])
            user_id = getattr(request.state, 'user_id', None)

            # Check permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(
                user_roles=user_roles,
                required_permission=permission,
                user_id=user_id,
                resource=resource_name or request.url.path
            ):
                logger.warning(
                    f"Permission denied: {user_id} lacks {permission.value} "
                    f"for {resource_name or request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission.value} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission, resource_name: Optional[str] = None):
    """
    Decorator to require any of the specified permissions

    Args:
        permissions: Required permissions (any)
        resource_name: Optional resource name for audit logging

    Example:
        @require_any_permission(Permission.FILINGS_WRITE, Permission.ADMIN)
        async def endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            user_roles = getattr(request.state, 'roles', [])
            user_id = getattr(request.state, 'user_id', None)

            rbac = get_rbac_manager()
            if not rbac.check_any_permission(
                user_roles=user_roles,
                required_permissions=list(permissions),
                user_id=user_id,
                resource=resource_name or request.url.path
            ):
                logger.warning(
                    f"Permission denied: {user_id} lacks any of "
                    f"{[p.value for p in permissions]} for {resource_name or request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: one of {[p.value for p in permissions]} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(request: Request, permission: Permission) -> bool:
    """
    Helper function to check permission inline

    Args:
        request: FastAPI request
        permission: Required permission

    Returns:
        True if permission granted
    """
    user_roles = getattr(request.state, 'roles', [])
    user_id = getattr(request.state, 'user_id', None)

    rbac = get_rbac_manager()
    return rbac.check_permission(
        user_roles=user_roles,
        required_permission=permission,
        user_id=user_id
    )
