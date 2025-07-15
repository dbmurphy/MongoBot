#!/usr/bin/env python3
"""
MongoDB Command Handler
Handles natural language commands and maps them to appropriate MCP tools
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MongoCommandHandler:
    """Handles MongoDB command processing and MCP tool orchestration"""

    def __init__(self, mcp_session):
        self.mcp_session = mcp_session
        self.available_tools = []
        self.tool_cache = {}

    async def refresh_tools(self):
        """Refresh available MCP tools"""
        try:
            tools_response = await self.mcp_session.list_tools()
            self.available_tools = [tool.name for tool in tools_response.tools]
            logger.info(f"Available tools: {self.available_tools}")
        except Exception as e:
            logger.error(f"Error refreshing tools: {e}")

    def categorize_command(self, command: str) -> Dict[str, Any]:
        """Categorize the command and extract key parameters"""
        command_lower = command.lower()
        result: Dict[str, Any] = {}

        # Atlas Management Commands
        if re.search(r"(list|show).*cluster", command_lower):
            result["category"] = "atlas_management"
            result["action"] = "list_clusters"
            result["tools"] = ["atlas-list-clusters"]

        if re.search(r"create.*cluster", command_lower):
            result["category"] = "atlas_management"
            result["action"] = "create_cluster"
            result["tools"] = ["atlas-create-free-cluster"]
            result["cluster_name"] = self._extract_cluster_name(command)

        if re.search(r"add.*ip.*whitelist", command_lower):
            result["category"] = "security"
            result["action"] = "add_ip_whitelist"
            result["tools"] = ["atlas-inspect-access-list", "atlas-create-access-list"]
            result["ip_address"] = self._extract_ip_address(command)

        if re.search(r"reset.*password", command_lower):
            result["category"] = "security"
            result["action"] = "reset_password"
            result["tools"] = ["atlas-list-db-users", "atlas-create-db-user"]

        # Performance Analysis Commands
        if re.search(r"analyz.*performance", command_lower):
            result["category"] = "performance"
            result["action"] = "analyze_performance"
            result["tools"] = ["atlas-list-clusters", "atlas-inspect-cluster"]
            result["cluster_name"] = self._extract_cluster_name(command)
            result["time_range"] = self._extract_time_range(command)

        if re.search(r"slow.*quer", command_lower):
            result["category"] = "performance"
            result["action"] = "slow_queries"
            result["tools"] = ["connect", "aggregate"]
            result["cluster_name"] = self._extract_cluster_name(command)

        if re.search(r"show.*collection", command_lower):
            result["category"] = "database"
            result["action"] = "list_collections"
            result["tools"] = ["connect", "list-collections"]
            result["database"] = self._extract_database_name(command)

        if re.search(r"analyz.*schema", command_lower):
            result["category"] = "database"
            result["action"] = "schema_analysis"
            result["tools"] = ["connect", "collection-schema"]
            result["collection"] = self._extract_collection_name(command)

        # RBAC Commands
        if re.search(r"rbac.*report|show.*rbac|rbac.*status", command_lower):
            result["category"] = "rbac"
            result["action"] = "rbac_report"
            result["tools"] = []

        if re.search(r"show.*admin|list.*admin", command_lower):
            result["category"] = "rbac"
            result["action"] = "list_admins"
            result["tools"] = []

        if re.search(r"my.*permission|what.*can.*do", command_lower):
            result["category"] = "rbac"
            result["action"] = "check_permissions"
            result["tools"] = []

        # Database Operations
        if re.search(r"list.*database", command_lower):
            result["category"] = "database"
            result["action"] = "list_databases"
            result["tools"] = ["connect", "list-databases"]

        if re.search(r"list.*collection", command_lower):
            result["category"] = "database"
            result["action"] = "list_collections"
            result["tools"] = ["connect", "list-collections"]
            result["database"] = self._extract_database_name(command)

        if re.search(r"missing.*index", command_lower):
            result["category"] = "optimization"
            result["action"] = "missing_indexes"
            result["tools"] = [
                "connect",
                "list-collections",
                "collection-indexes",
                "collection-schema",
            ]
            result["database"] = self._extract_database_name(command)

        if re.search(r"redundant.*index|duplicate.*index", command_lower):
            result["category"] = "optimization"
            result["action"] = "redundant_indexes"
            result["tools"] = ["connect", "list-collections", "collection-indexes"]
            result["database"] = self._extract_database_name(command)

        if re.search(r"schema.*analysis", command_lower):
            result["category"] = "database"
            result["action"] = "schema_analysis"
            result["tools"] = ["connect", "collection-schema"]
            result["collection"] = self._extract_collection_name(command)

        # Extract IP address from any command if not already extracted
        if "ip_address" not in result:
            ip_match = re.search(r"(?:\b|\D)((?:\d{1,3}\.){3}\d{1,3})(?:\b|\D)", command)
            if ip_match:
                result["ip_address"] = ip_match.group(1)

        # Extract cluster name for any command if not already set
        if "cluster_name" not in result:
            cluster_name = self._extract_cluster_name(command)
            if cluster_name:
                result["cluster_name"] = cluster_name

        # Default fallback only if no category was set
        if "category" not in result:
            result["category"] = "general"
            result["action"] = "help"
            result["tools"] = []

        return result

    def _extract_cluster_name(self, command: str) -> Optional[str]:
        """Extract cluster name from command"""
        patterns = [
            r"cluster[:\s]+([a-zA-Z0-9_-]+)",
            r"on\s+cluster\s+([a-zA-Z0-9_-]+)",
            r"called\s+([a-zA-Z0-9_-]+)",
            r"named\s+([a-zA-Z0-9_-]+)",
            r"for\s+cluster\s+([a-zA-Z0-9_-]+)",
            r"details\s+for\s+cluster\s+([a-zA-Z0-9_-]+)",
            r"issues\s+on\s+([a-zA-Z0-9_-]+)",
            r"performance\s+.*\s+([a-zA-Z0-9_-]+)",
            r"cluster\s+([a-zA-Z0-9_-]+)",  # Simple "cluster name" pattern
            r"([a-zA-Z0-9_-]+)\s+cluster",  # "name cluster" pattern
            r"cluster\s+called\s+([a-zA-Z0-9_-]+)",  # "cluster called name" pattern
            r"([a-zA-Z0-9_-]+)(?:\s+cluster|\s*$)",  # "name cluster" or "name" at end
        ]
        stopwords = ["called", "named", "for", "on", "in", "the", "a", "an"]
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                cluster_name = match.group(1)
                if cluster_name.lower() not in stopwords:
                    return cluster_name
        # Fallback: if 'cluster' is followed by a word, use that word
        fallback = re.search(r"cluster\s+([a-zA-Z0-9_-]+)", command, re.IGNORECASE)
        if fallback:
            cluster_name = fallback.group(1)
            if cluster_name.lower() not in stopwords:
                return cluster_name
        # Fallback: if command ends with 'on [word]' or 'for [word]', use that word
        fallback_on = re.search(r"on\s+([a-zA-Z0-9_-]+)\s*$", command, re.IGNORECASE)
        if fallback_on:
            cluster_name = fallback_on.group(1)
            if cluster_name.lower() not in stopwords:
                return cluster_name
        fallback_for = re.search(r"for\s+([a-zA-Z0-9_-]+)\s*$", command, re.IGNORECASE)
        if fallback_for:
            cluster_name = fallback_for.group(1)
            if cluster_name.lower() not in stopwords:
                return cluster_name
        # Final fallback: use the last word if not a stopword
        words = command.strip().split()
        if words:
            last_word = words[-1].strip(".,!?")
            if last_word.lower() not in stopwords:
                return last_word
        return None

    def _extract_ip_address(self, command: str) -> Optional[str]:
        """Extract IP address from command"""
        # Look for IP patterns with various keywords
        patterns = [
            r"IP\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
            r"whitelist\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
            r"access\s+from\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
            r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_time_range(self, command: str) -> Dict[str, Any]:
        """Extract time range from command"""
        time_patterns = {
            r"last\s+(\d+)\s+hour": lambda x: {"hours": int(x)},
            r"last\s+(\d+)\s+day": lambda x: {"days": int(x)},
            r"last\s+(\d+)\s+week": lambda x: {"weeks": int(x)},
            r"(\d+)\s+hour": lambda x: {"hours": int(x)},
            r"(\d+)\s+day": lambda x: {"days": int(x)},
        }

        for pattern, parser in time_patterns.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return parser(match.group(1))

        return {"hours": 24}  # Default to 24 hours

    def _extract_database_name(self, command: str) -> Optional[str]:
        """Extract database name from command"""
        patterns = [r"database[:\s]+(\w+)", r"in\s+(\w+)", r"from\s+(\w+)"]

        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_collection_name(self, command: str) -> Optional[str]:
        """Extract collection name from command"""
        patterns = [r"collection[:\s]+(\w+)", r"for\s+(\w+)", r"in\s+(\w+)"]

        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    async def execute_command(self, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tools based on command analysis"""
        results: Dict[str, Any] = {}

        try:
            category = command_info["category"]
            action = command_info["action"]

            if category == "atlas_management":
                results = await self._handle_atlas_management(action, command_info)
            elif category == "performance":
                results = await self._handle_performance_analysis(action, command_info)
            elif category == "database":
                results = await self._handle_database_operations(action, command_info)
            elif category == "optimization":
                results = await self._handle_optimization(action, command_info)
            elif category == "security":
                results = await self._handle_security(action, command_info)
            elif category == "rbac":
                results = await self._handle_rbac_commands(action, command_info)
            else:
                results = {"help": self._get_help_text()}

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            results = {"error": str(e)}

        return results

    async def _handle_atlas_management(
        self, action: str, command_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Atlas management commands"""
        results: Dict[str, Any] = {}

        if action == "list_clusters":
            clusters = await self.mcp_session.call_tool("atlas-list-clusters", {})
            results["clusters"] = clusters

        elif action == "create_cluster":
            cluster_name = command_info.get("cluster_name", "new-cluster")
            cluster_params = {
                "name": cluster_name,
                "provider": "AWS",
                "region": "US_EAST_1",
                "instanceSize": "M0",
            }
            cluster = await self.mcp_session.call_tool("atlas-create-free-cluster", cluster_params)
            results["cluster_creation"] = cluster

        return results

    async def _handle_performance_analysis(
        self, action: str, command_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle performance analysis commands"""
        results: Dict[str, Any] = {}

        if action == "analyze_performance":
            # First get clusters
            clusters = await self.mcp_session.call_tool("atlas-list-clusters", {})
            results["clusters"] = clusters

            # If specific cluster mentioned, get detailed info
            if command_info.get("cluster_name"):
                cluster_details = await self.mcp_session.call_tool(
                    "atlas-inspect-cluster", {"clusterName": command_info["cluster_name"]}
                )
                results["cluster_details"] = cluster_details

        elif action == "slow_queries":
            # Connect to database and analyze slow queries
            if command_info.get("cluster_name"):
                # This would require connecting to the specific cluster
                # and running performance analysis queries
                results["slow_queries"] = {
                    "note": "Slow query analysis requires connection to specific cluster"
                }

        return results

    async def _handle_database_operations(
        self, action: str, command_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle database operations"""
        results: Dict[str, Any] = {}

        try:
            # Get cluster name - required for all database operations
            cluster_name = command_info.get("cluster_name")
            if not cluster_name:
                results["error"] = (
                    "Cluster name required for database operations. Please specify which cluster to use."
                )
                return results

            # Connect to the specified cluster first
            connection_params = {"cluster": cluster_name}
            await self.mcp_session.call_tool("connect", connection_params)
            results["cluster_connected"] = cluster_name

            if action == "list_databases":
                databases = await self.mcp_session.call_tool("list-databases", {})
                results["databases"] = databases

            elif action == "list_collections":
                if command_info.get("database"):
                    collections = await self.mcp_session.call_tool(
                        "list-collections", {"database": command_info["database"]}
                    )
                    results["collections"] = collections
                else:
                    results["error"] = "Database name required"

            elif action == "schema_analysis":
                if command_info.get("collection"):
                    schema = await self.mcp_session.call_tool(
                        "collection-schema", {"collection": command_info["collection"]}
                    )
                    results["schema"] = schema
                else:
                    results["error"] = "Collection name required"

        except Exception as e:
            logger.error(f"Database operation error: {e}")
            results["error"] = str(e)

        return results

    async def _handle_optimization(
        self, action: str, command_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle optimization commands"""
        results: Dict[str, Any] = {}

        try:
            # Get cluster name - required for all optimization operations
            cluster_name = command_info.get("cluster_name")
            if not cluster_name:
                results["error"] = (
                    "Cluster name required for optimization operations. Please specify which cluster to use."
                )
                return results

            # Connect to the specified cluster first
            connection_params = {"cluster": cluster_name}
            await self.mcp_session.call_tool("connect", connection_params)
            results["cluster_connected"] = cluster_name

            if action == "missing_indexes":
                # Get all collections
                collections = await self.mcp_session.call_tool("list-collections", {})
                results["collections"] = collections

                # For each collection, analyze indexes
                if collections and hasattr(collections, "content"):
                    collection_data = json.loads(collections.content[0].text)
                    for collection in collection_data.get("collections", []):
                        indexes = await self.mcp_session.call_tool(
                            "collection-indexes", {"collection": collection}
                        )
                        results[f"{collection}_indexes"] = indexes

            elif action == "redundant_indexes":
                # Get all collections
                collections = await self.mcp_session.call_tool("list-collections", {})
                results["collections"] = collections

                redundant_indexes = {}

                # For each collection, analyze indexes for redundancy
                if collections and hasattr(collections, "content"):
                    collection_data = json.loads(collections.content[0].text)
                    for collection in collection_data.get("collections", []):
                        indexes = await self.mcp_session.call_tool(
                            "collection-indexes", {"collection": collection}
                        )

                        if indexes and hasattr(indexes, "content"):
                            index_data = json.loads(indexes.content[0].text)
                            redundant = await self._analyze_redundant_indexes(
                                collection, index_data
                            )
                            if redundant:
                                redundant_indexes[collection] = redundant

                results["redundant_indexes"] = redundant_indexes
                results["analysis_complete"] = True

        except Exception as e:
            logger.error(f"Optimization operation error: {e}")
            results["error"] = str(e)

        return results

    async def _handle_security(self, action: str, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security commands"""
        results: Dict[str, Any] = {}

        if action == "add_ip_whitelist":
            try:
                # First, get current access lists
                access_lists = await self.mcp_session.call_tool("atlas-inspect-access-list", {})
                results["current_access_lists"] = access_lists

                # Add IP if provided
                if command_info.get("ip_address"):
                    new_access = await self.mcp_session.call_tool(
                        "atlas-create-access-list",
                        {"ipAddress": command_info["ip_address"], "comment": "Added via Slack bot"},
                    )
                    results["new_access_entry"] = new_access

            except Exception as e:
                logger.error(f"IP whitelist error: {e}")
                results["error"] = str(e)

        elif action == "reset_password":
            try:
                # List users first
                users = await self.mcp_session.call_tool("atlas-list-db-users", {})
                results["users"] = users

            except Exception as e:
                logger.error(f"Password reset error: {e}")
                results["error"] = str(e)

        return results

    async def _handle_rbac_commands(
        self, action: str, command_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle RBAC-related commands"""
        results: Dict[str, Any] = {}

        if action == "rbac_report":
            # This will be handled by the main bot with RBAC manager
            results["rbac_report"] = {"note": "RBAC report requested"}

        elif action == "list_admins":
            # This will be handled by the main bot with RBAC manager
            results["list_admins"] = {"note": "Admin list requested"}

        elif action == "check_permissions":
            # This will be handled by the main bot with RBAC manager
            results["check_permissions"] = {"note": "Permission check requested"}

        return results

    async def _analyze_redundant_indexes(
        self, collection_name: str, index_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze indexes for redundancy"""
        redundant_indexes: List[Dict[str, Any]] = []

        try:
            indexes = index_data.get("indexes", [])

            if not indexes:
                return redundant_indexes

            # Parse indexes into a more analyzable format
            parsed_indexes = []
            for idx in indexes:
                if isinstance(idx, dict):
                    name = idx.get("name", "")
                    key = idx.get("key", {})

                    # Skip the default _id index
                    if name == "_id_":
                        continue

                    # Extract field names and directions
                    fields = []
                    for field, direction in key.items():
                        fields.append({"field": field, "direction": direction})

                    parsed_indexes.append(
                        {
                            "name": name,
                            "fields": fields,
                            "field_names": [f["field"] for f in fields],
                            "key": key,
                            "original": idx,
                        }
                    )

            # Find redundant indexes
            for i, idx1 in enumerate(parsed_indexes):
                for j, idx2 in enumerate(parsed_indexes):
                    if i >= j:  # Skip self-comparison and duplicates
                        continue

                    redundancy = self._check_index_redundancy(idx1, idx2)
                    if redundancy:
                        redundant_indexes.append(
                            {
                                "collection": collection_name,
                                "redundant_index": redundancy["redundant"],
                                "covers_same_as": redundancy["covers"],
                                "redundancy_type": redundancy["type"],
                                "recommendation": redundancy["recommendation"],
                            }
                        )

            return redundant_indexes

        except Exception as e:
            logger.error(f"Error analyzing redundant indexes for {collection_name}: {e}")
            return []

    def _check_index_redundancy(
        self, idx1: Dict[str, Any], idx2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if two indexes are redundant"""

        # Type 1: Exact duplicate (same fields, same order, same direction)
        if idx1["field_names"] == idx2["field_names"]:
            if all(
                f1["direction"] == f2["direction"] for f1, f2 in zip(idx1["fields"], idx2["fields"])
            ):
                return {
                    "redundant": idx1["name"],
                    "covers": idx2["name"],
                    "type": "exact_duplicate",
                    "recommendation": f"Remove index '{idx1['name']}' as it's identical to '{idx2['name']}'",
                }

        # Type 2: Prefix redundancy (one index is a prefix of another)
        if self._is_prefix_redundant(idx1, idx2):
            return {
                "redundant": idx1["name"],
                "covers": idx2["name"],
                "type": "prefix_redundant",
                "recommendation": (
                    f"Consider removing index '{idx1['name']}' as it's covered by '{idx2['name']}'"
                ),
            }

        if self._is_prefix_redundant(idx2, idx1):
            return {
                "redundant": idx2["name"],
                "covers": idx1["name"],
                "type": "prefix_redundant",
                "recommendation": (
                    f"Consider removing index '{idx2['name']}' as it's covered by '{idx1['name']}'"
                ),
            }

        # Type 3: Reverse redundancy (same fields, opposite directions)
        if (
            idx1["field_names"] == idx2["field_names"]
            and len(idx1["fields"]) == 1
            and len(idx2["fields"]) == 1
        ):
            f1_dir = idx1["fields"][0]["direction"]
            f2_dir = idx2["fields"][0]["direction"]

            if (f1_dir == 1 and f2_dir == -1) or (f1_dir == -1 and f2_dir == 1):
                return {
                    "redundant": idx1["name"],
                    "covers": idx2["name"],
                    "type": "reverse_redundant",
                    "recommendation": (
                        f"Indexes '{idx1['name']}' and '{idx2['name']}' are reverse duplicates. "
                        f"Consider keeping only one unless both sort orders are frequently used."
                    ),
                }

        return None

    def _is_prefix_redundant(
        self, potential_redundant: Dict[str, Any], covering_index: Dict[str, Any]
    ) -> bool:
        """Check if potential_redundant is a prefix of covering_index"""
        redundant_fields = potential_redundant["field_names"]
        covering_fields = covering_index["field_names"]

        if len(redundant_fields) >= len(covering_fields):
            return False

        # Check if redundant fields are a prefix of covering fields
        for i, field in enumerate(redundant_fields):
            if i >= len(covering_fields) or covering_fields[i] != field:
                return False

            # Check if directions match
            if (
                potential_redundant["fields"][i]["direction"]
                != covering_index["fields"][i]["direction"]
            ):
                return False

        return True

    def _get_help_text(self) -> str:
        """Get help text for the bot"""
        return """
🤖 **MongoDB Atlas Assistant Help**

**Atlas Management:**
• List my clusters
• Create a new cluster called [name]
• Show cluster details for [cluster]

**Performance Analysis:**
• Analyze cluster [name] performance over last [time]
• Show slow queries on cluster [name]
• Performance summary for [cluster]

**Database Operations:**
• List all databases
• Show collections in database [name]
• Analyze schema for collection [name]

**Security:**
• Add IP [address] to whitelist
• Reset password for user [name]

**Optimization:**
• Find missing indexes in database [name]
• Find redundant indexes in database [name]
• Show duplicate indexes
• Storage usage analysis

Use natural language - I'll understand your intent!
        """
