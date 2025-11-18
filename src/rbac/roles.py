"""
Role and Permission Definitions
"""

from enum import Enum
from typing import Set, Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System Permissions"""
    # Filing permissions
    FILINGS_READ = "filings.read"
    FILINGS_WRITE = "filings.write"
    FILINGS_DELETE = "filings.delete"

    # Prediction permissions
    PREDICTIONS_READ = "predictions.read"
    PREDICTIONS_WRITE = "predictions.write"
    PREDICTIONS_DELETE = "predictions.delete"

    # Signal permissions
    SIGNALS_READ = "signals.read"
    SIGNALS_WRITE = "signals.write"
    SIGNALS_DELETE = "signals.delete"

    # Validation permissions
    VALIDATION_READ = "validation.read"
    VALIDATION_WRITE = "validation.write"

    # User management
    USERS_READ = "users.read"
    USERS_WRITE = "users.write"
    USERS_DELETE = "users.delete"

    # System administration
    SYSTEM_CONFIG = "system.config"
    SYSTEM_LOGS = "system.logs"
    SYSTEM_AUDIT = "system.audit"

    # API key management
    API_KEYS_READ = "api_keys.read"
    API_KEYS_WRITE = "api_keys.write"
    API_KEYS_DELETE = "api_keys.delete"


class Role(BaseModel):
    """Role Definition"""
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional[List[str]] = None  # Parent roles

    class Config:
        use_enum_values = True


class RoleHierarchy:
    """
    Manages role hierarchy and permission inheritance
    """

    def __init__(self):
        """Initialize with predefined roles"""
        self.roles: dict[str, Role] = {}

        # Define standard roles
        self._define_standard_roles()

        logger.info(f"RoleHierarchy initialized with {len(self.roles)} roles")

    def _define_standard_roles(self):
        """Define standard system roles"""

        # Guest role - read-only access to public data
        self.roles["guest"] = Role(
            name="guest",
            description="Guest user with read-only access",
            permissions={
                Permission.FILINGS_READ,
                Permission.PREDICTIONS_READ,
                Permission.SIGNALS_READ,
                Permission.VALIDATION_READ
            }
        )

        # Analyst role - read/write access to data
        self.roles["analyst"] = Role(
            name="analyst",
            description="Analyst with read/write access to data",
            permissions={
                Permission.FILINGS_READ,
                Permission.FILINGS_WRITE,
                Permission.PREDICTIONS_READ,
                Permission.PREDICTIONS_WRITE,
                Permission.SIGNALS_READ,
                Permission.SIGNALS_WRITE,
                Permission.VALIDATION_READ,
                Permission.VALIDATION_WRITE
            },
            inherits_from=["guest"]
        )

        # API User role - programmatic access
        self.roles["api_user"] = Role(
            name="api_user",
            description="API user with programmatic access",
            permissions={
                Permission.FILINGS_READ,
                Permission.PREDICTIONS_READ,
                Permission.SIGNALS_READ,
                Permission.VALIDATION_READ,
                Permission.API_KEYS_READ
            },
            inherits_from=["guest"]
        )

        # Manager role - user management capabilities
        self.roles["manager"] = Role(
            name="manager",
            description="Manager with user management capabilities",
            permissions={
                Permission.USERS_READ,
                Permission.USERS_WRITE,
                Permission.API_KEYS_READ,
                Permission.API_KEYS_WRITE
            },
            inherits_from=["analyst"]
        )

        # Admin role - full system access
        self.roles["admin"] = Role(
            name="admin",
            description="Administrator with full system access",
            permissions={
                Permission.FILINGS_READ,
                Permission.FILINGS_WRITE,
                Permission.FILINGS_DELETE,
                Permission.PREDICTIONS_READ,
                Permission.PREDICTIONS_WRITE,
                Permission.PREDICTIONS_DELETE,
                Permission.SIGNALS_READ,
                Permission.SIGNALS_WRITE,
                Permission.SIGNALS_DELETE,
                Permission.VALIDATION_READ,
                Permission.VALIDATION_WRITE,
                Permission.USERS_READ,
                Permission.USERS_WRITE,
                Permission.USERS_DELETE,
                Permission.SYSTEM_CONFIG,
                Permission.SYSTEM_LOGS,
                Permission.SYSTEM_AUDIT,
                Permission.API_KEYS_READ,
                Permission.API_KEYS_WRITE,
                Permission.API_KEYS_DELETE
            },
            inherits_from=["manager"]
        )

    def add_role(self, role: Role):
        """
        Add or update role definition

        Args:
            role: Role to add
        """
        self.roles[role.name] = role
        logger.info(f"Added role: {role.name}")

    def remove_role(self, role_name: str) -> bool:
        """
        Remove role definition

        Args:
            role_name: Name of role to remove

        Returns:
            True if removed, False if not found
        """
        if role_name in self.roles:
            del self.roles[role_name]
            logger.info(f"Removed role: {role_name}")
            return True
        return False

    def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get role definition

        Args:
            role_name: Role name

        Returns:
            Role if found, None otherwise
        """
        return self.roles.get(role_name)

    def get_effective_permissions(self, role_names: List[str]) -> Set[Permission]:
        """
        Get all effective permissions for given roles (including inherited)

        Args:
            role_names: List of role names

        Returns:
            Set of all effective permissions
        """
        permissions = set()
        processed_roles = set()

        def process_role(role_name: str):
            """Recursively process role and its parents"""
            if role_name in processed_roles:
                return
            processed_roles.add(role_name)

            role = self.roles.get(role_name)
            if not role:
                logger.warning(f"Role not found: {role_name}")
                return

            # Add role's permissions
            permissions.update(role.permissions)

            # Process parent roles
            if role.inherits_from:
                for parent_role in role.inherits_from:
                    process_role(parent_role)

        # Process all provided roles
        for role_name in role_names:
            process_role(role_name)

        return permissions

    def has_permission(
        self,
        role_names: List[str],
        required_permission: Permission
    ) -> bool:
        """
        Check if roles have required permission

        Args:
            role_names: List of role names
            required_permission: Required permission

        Returns:
            True if permission is granted
        """
        effective_permissions = self.get_effective_permissions(role_names)
        return required_permission in effective_permissions

    def has_any_permission(
        self,
        role_names: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if roles have any of the required permissions

        Args:
            role_names: List of role names
            required_permissions: List of required permissions

        Returns:
            True if any permission is granted
        """
        effective_permissions = self.get_effective_permissions(role_names)
        return any(perm in effective_permissions for perm in required_permissions)

    def has_all_permissions(
        self,
        role_names: List[str],
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if roles have all required permissions

        Args:
            role_names: List of role names
            required_permissions: List of required permissions

        Returns:
            True if all permissions are granted
        """
        effective_permissions = self.get_effective_permissions(role_names)
        return all(perm in effective_permissions for perm in required_permissions)

    def list_roles(self) -> List[str]:
        """
        List all role names

        Returns:
            List of role names
        """
        return list(self.roles.keys())

    def get_role_hierarchy(self, role_name: str) -> List[str]:
        """
        Get full hierarchy for a role (including parents)

        Args:
            role_name: Role name

        Returns:
            List of role names in hierarchy
        """
        hierarchy = []
        processed = set()

        def build_hierarchy(name: str):
            if name in processed:
                return
            processed.add(name)
            hierarchy.append(name)

            role = self.roles.get(name)
            if role and role.inherits_from:
                for parent in role.inherits_from:
                    build_hierarchy(parent)

        build_hierarchy(role_name)
        return hierarchy
