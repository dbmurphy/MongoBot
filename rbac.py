#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) System for MongoDB Slack Bot
Manages user permissions and access control for bot operations
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)


class RBACManager:
    """Manages role-based access control for the MongoDB Slack Bot"""

    def __init__(self, slack_client: AsyncWebClient):
        self.slack_client = slack_client
        self.admin_users: set[str] = set()
        self.admin_groups: set[str] = set()
        self.admin_operations: set[str] = set()
        self.user_operations: set[str] = set()
        self.self_service_operations: set[str] = set()
        self.rbac_enabled = True
        self.notify_admin_on_denied = True
        self.log_access_attempts = True

        # Cache for group memberships to reduce API calls
        self.group_membership_cache: dict[str, dict[str, Any]] = {}
        self.username_to_id_cache: dict[str, dict[str, Any]] = (
            {}
        )  # Cache for username to ID mapping
        self.cache_ttl = 300  # 5 minutes

        self.load_configuration()

    def load_configuration(self):
        """Load RBAC configuration from environment variables or config file"""
        try:
            # Try to import from config file first
            try:
                import config

                self.rbac_enabled = getattr(config, "RBAC_ENABLED", True)
                self.admin_users = set(getattr(config, "ADMIN_USERS", []))
                self.admin_groups = set(getattr(config, "ADMIN_GROUPS", []))
                self.admin_operations = set(getattr(config, "ADMIN_OPERATIONS", []))
                self.user_operations = set(getattr(config, "USER_OPERATIONS", []))
                self.self_service_operations = set(getattr(config, "SELF_SERVICE_OPERATIONS", []))
                self.notify_admin_on_denied = getattr(config, "RBAC_NOTIFY_ADMIN_ON_DENIED", True)
                self.log_access_attempts = getattr(config, "RBAC_LOG_ACCESS_ATTEMPTS", True)

                logger.info("RBAC configuration loaded from config file")

            except ImportError:
                # Fall back to environment variables
                self.rbac_enabled = os.getenv("RBAC_ENABLED", "true").lower() == "true"
                self.admin_users = set(
                    os.getenv("ADMIN_USERS", "").split(",") if os.getenv("ADMIN_USERS") else []
                )
                self.admin_groups = set(
                    os.getenv("ADMIN_GROUPS", "").split(",") if os.getenv("ADMIN_GROUPS") else []
                )

                # Default admin operations
                self.admin_operations = {
                    "create_cluster",
                    "create_user",
                    "reset_password",
                    "create_index",
                    "insert_document",
                    "update_document",
                    "delete_document",
                    "drop_collection",
                    "drop_database",
                    "manage_indexes",
                }

                # Default user operations
                self.user_operations = {
                    "list_clusters",
                    "list_databases",
                    "list_collections",
                    "schema_analysis",
                    "analyze_performance",
                    "slow_queries",
                    "missing_indexes",
                    "collection_stats",
                    "database_stats",
                    "help",
                }

                self.self_service_operations = {
                    "reset_own_password",
                    "view_own_user_info",
                    "add_ip_whitelist",
                }

                logger.info("RBAC configuration loaded from environment variables")

        except Exception as e:
            logger.error(f"Error loading RBAC configuration: {e}")
            # Default to secure configuration
            self.rbac_enabled = True
            self.admin_users = set()
            self.admin_groups = set()
            self.admin_operations = {"create_cluster", "create_user"}
            self.user_operations = {"list_clusters", "help"}
            self.self_service_operations = {"reset_password", "add_ip_whitelist"}

    async def check_user_permission(
        self, user_id: str, operation: str, target_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a user has permission to perform an operation

        Args:
            user_id: Slack user ID
            operation: Operation being attempted
            target_user: Target user for operations like password reset

        Returns:
            Dict with 'allowed' boolean and 'reason' string
        """
        if not self.rbac_enabled:
            return {"allowed": True, "reason": "RBAC disabled"}

        # Log access attempt
        if self.log_access_attempts:
            logger.info(f"Permission check: User {user_id} attempting {operation}")

        # Check if it's a self-service operation
        if operation in self.self_service_operations and target_user == user_id:
            return {"allowed": True, "reason": "Self-service operation"}

        # Check if user is admin
        is_admin = await self.is_user_admin(user_id)

        if is_admin:
            return {"allowed": True, "reason": "Admin user"}

        # Check if operation is allowed for regular users
        if operation in self.user_operations:
            return {"allowed": True, "reason": "User operation"}

        # Check if operation requires admin privileges
        if operation in self.admin_operations:
            reason = "Admin privileges required"
            if self.notify_admin_on_denied:
                await self.notify_admin_of_denied_access(user_id, operation)
            return {"allowed": False, "reason": reason}

        # Default deny for unknown operations
        return {"allowed": False, "reason": "Unknown operation"}

    async def is_user_admin(self, user_id: str) -> bool:
        """Check if a user is an admin"""
        # Check direct admin user list (supports both IDs and usernames)
        if user_id in self.admin_users:
            return True

        # Check if any admin user entry matches this user (by username)
        for admin_entry in self.admin_users:
            if await self.resolve_admin_entry_to_user_id(admin_entry) == user_id:
                return True

        # Check admin groups
        for group in self.admin_groups:
            if await self.is_user_in_group(user_id, group):
                return True

        return False

    async def resolve_admin_entry_to_user_id(self, admin_entry: str) -> Optional[str]:
        """Resolve an admin entry (username or ID) to a user ID"""
        # If it's already a user ID format, return as-is
        if admin_entry.startswith("U") and len(admin_entry) == 11:
            return admin_entry

        # Clean up the username
        username = admin_entry.lstrip("@")

        # Check cache first
        cache_key = f"username:{username}"
        if cache_key in self.username_to_id_cache:
            cached_data = self.username_to_id_cache[cache_key]
            if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["user_id"]

        # Resolve username to user ID
        user_id = await self.resolve_username_to_user_id(username)

        # Cache the result
        if user_id:
            self.username_to_id_cache[cache_key] = {
                "user_id": user_id,
                "timestamp": datetime.now().timestamp(),
            }

        return user_id

    async def resolve_username_to_user_id(self, username: str) -> Optional[str]:
        """Resolve a username to a Slack user ID"""
        try:
            # Try to find user by username
            response = await self.slack_client.users_list()

            if response["ok"]:
                for user in response["members"]:
                    if not user.get("deleted", False):
                        # Check various username formats
                        if (
                            user.get("name") == username
                            or user.get("real_name", "").lower() == username.lower()
                            or user.get("display_name") == username
                            or user.get("profile", {}).get("display_name") == username
                            or user.get("profile", {}).get("real_name", "").lower()
                            == username.lower()
                        ):
                            return user["id"]

            # If not found in users list, try users.lookupByEmail if it looks like an email
            if "@" in username:
                try:
                    email_response = await self.slack_client.users_lookupByEmail(email=username)
                    if email_response["ok"]:
                        return email_response["user"]["id"]
                except SlackApiError:
                    pass

        except SlackApiError as e:
            logger.error(f"Error resolving username {username}: {e}")

        return None

    async def is_user_in_group(self, user_id: str, group_name: str) -> bool:
        """Check if a user is in a specific group"""
        cache_key = f"{user_id}:{group_name}"

        # Check cache
        if cache_key in self.group_membership_cache:
            cached_data = self.group_membership_cache[cache_key]
            if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["is_member"]

        try:
            # Get user groups from Slack API
            response = await self.slack_client.usergroups_list()

            if response["ok"]:
                for usergroup in response["usergroups"]:
                    if usergroup["handle"] == group_name:
                        # Get usergroup members
                        members_response = await self.slack_client.usergroups_users_list(
                            usergroup=usergroup["id"]
                        )

                        if members_response["ok"]:
                            is_member = user_id in members_response["users"]

                            # Cache the result
                            self.group_membership_cache[cache_key] = {
                                "is_member": is_member,
                                "timestamp": datetime.now().timestamp(),
                            }

                            return is_member

        except SlackApiError as e:
            logger.error(f"Error checking group membership: {e}")

        return False

    async def notify_admin_of_denied_access(self, user_id: str, operation: str):
        """Notify admins when access is denied"""
        try:
            # Get user info
            user_info = await self.slack_client.users_info(user=user_id)
            username = user_info["user"]["name"] if user_info["ok"] else user_id

            message = (
                f"🚨 **Access Denied Alert**\n\n"
                f"User: @{username} ({user_id})\n"
                f"Attempted Operation: `{operation}`\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"This user attempted to perform an admin-only operation."
            )

            # Send notification to admin users
            for admin_user in self.admin_users:
                try:
                    await self.slack_client.chat_postMessage(channel=admin_user, text=message)
                except SlackApiError as e:
                    logger.error(f"Error notifying admin {admin_user}: {e}")

        except Exception as e:
            logger.error(f"Error in admin notification: {e}")

    def get_user_permissions(self, user_id: str) -> Dict[str, List[str]]:
        """Get a list of operations a user can perform"""
        permissions = {
            "allowed_operations": list(self.user_operations),
            "admin_operations": list(self.admin_operations),
            "self_service_operations": list(self.self_service_operations),
        }

        return permissions

    def get_operation_category(self, operation: str) -> str:
        """Get the category of an operation"""
        if operation in self.admin_operations:
            return "admin"
        elif operation in self.user_operations:
            return "user"
        elif operation in self.self_service_operations:
            return "self_service"
        else:
            return "unknown"

    async def get_admin_users_info(self) -> List[Dict[str, str]]:
        """Get information about admin users"""
        admin_info = []

        for user_id in self.admin_users:
            try:
                user_info = await self.slack_client.users_info(user=user_id)
                if user_info["ok"]:
                    admin_info.append(
                        {
                            "user_id": user_id,
                            "username": user_info["user"]["name"],
                            "real_name": user_info["user"]["real_name"],
                            "type": "direct",
                        }
                    )
            except SlackApiError as e:
                logger.error(f"Error getting admin user info for {user_id}: {e}")

        # Add group-based admins
        for group in self.admin_groups:
            admin_info.append(
                {
                    "user_id": f"@{group}",
                    "username": group,
                    "real_name": f"Group: {group}",
                    "type": "group",
                }
            )

        return admin_info

    def generate_rbac_report(self) -> str:
        """Generate a report of RBAC configuration"""
        report = f"""
🔐 **RBAC Configuration Report**

**Status:** {'Enabled' if self.rbac_enabled else 'Disabled'}

**Admin Users:** {len(self.admin_users)}
{chr(10).join(f"• {user}" for user in self.admin_users)}

**Admin Groups:** {len(self.admin_groups)}
{chr(10).join(f"• {group}" for group in self.admin_groups)}

**Admin Operations:** {len(self.admin_operations)}
{chr(10).join(f"• {op}" for op in sorted(self.admin_operations))}

**User Operations:** {len(self.user_operations)}
{chr(10).join(f"• {op}" for op in sorted(self.user_operations))}

**Self-Service Operations:** {len(self.self_service_operations)}
{chr(10).join(f"• {op}" for op in sorted(self.self_service_operations))}

**Notifications:** {'Enabled' if self.notify_admin_on_denied else 'Disabled'}
**Access Logging:** {'Enabled' if self.log_access_attempts else 'Disabled'}
        """

        return report.strip()

    async def clear_cache(self):
        """Clear the group membership cache"""
        self.group_membership_cache.clear()
        logger.info("RBAC cache cleared")

    def update_configuration(self, config_updates: Dict[str, Any]):
        """Update RBAC configuration at runtime"""
        for key, value in config_updates.items():
            if key == "admin_users":
                self.admin_users = set(value)
            elif key == "admin_groups":
                self.admin_groups = set(value)
            elif key == "admin_operations":
                self.admin_operations = set(value)
            elif key == "user_operations":
                self.user_operations = set(value)
            elif key == "rbac_enabled":
                self.rbac_enabled = value

        logger.info(f"RBAC configuration updated: {config_updates}")

        # Clear cache after configuration change
        self.group_membership_cache.clear()
