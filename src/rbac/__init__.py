"""
Role-Based Access Control (RBAC) System
"""

from .roles import Role, RoleHierarchy, Permission
from .rbac import RBACManager, require_permission, check_permission

__all__ = [
    'Role',
    'RoleHierarchy',
    'Permission',
    'RBACManager',
    'require_permission',
    'check_permission'
]
