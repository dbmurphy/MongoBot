# Configuration example for MongoDB Slack Bot
# Copy this file to config.py and update with your credentials

# Slack Configuration
SLACK_BOT_TOKEN = "xoxb-your-bot-token-here"
SLACK_APP_TOKEN = "xapp-your-app-token-here"
SLACK_SIGNING_SECRET = "your-signing-secret-here"

# Anthropic Configuration
ANTHROPIC_API_KEY = "your-anthropic-api-key-here"

# MongoDB Atlas Configuration
MONGODB_ATLAS_CLIENT_ID = "your-atlas-service-account-client-id"
MONGODB_ATLAS_CLIENT_SECRET = "your-atlas-service-account-client-secret"

# Optional: Direct MongoDB connection string
MONGODB_CONNECTION_STRING = "mongodb+srv://username:password@cluster.mongodb.net/database"

# Optional: MCP Server Configuration
MCP_LOG_PATH = "/tmp/mcp-logs"
MCP_READ_ONLY = False
MCP_INDEX_CHECK = True
MCP_DISABLED_TOOLS: list[str] = []
MCP_TELEMETRY = "enabled"

# Role-Based Access Control (RBAC) Configuration
RBAC_ENABLED = True

# Admin Users - Full access to all operations
# Supports both Slack user IDs and friendly names
ADMIN_USERS = [
    "U1234567890",  # Slack user ID format
    "@david.murphy",  # Friendly name format
    "@jane.smith",  # Friendly name format
    "john.doe",  # Username without @ symbol
    # Add more admin users (mix of IDs and names)
]

# Admin Groups - Members of these groups have admin privileges
ADMIN_GROUPS = [
    "dba-team",
    "devops-team",
    "infrastructure-team",
    # Add more admin group names
]

# Admin Operations - Require admin privileges
ADMIN_OPERATIONS = [
    "create_cluster",
    "create_user",
    "create_index",
    "insert_document",
    "update_document",
    "delete_document",
    "drop_collection",
    "drop_database",
    "manage_indexes",
]

# User Operations - Available to all users
USER_OPERATIONS = [
    "list_clusters",
    "list_databases",
    "list_collections",
    "schema_analysis",
    "analyze_performance",
    "slow_queries",
    "missing_indexes",
    "redundant_indexes",
    "collection_stats",
    "database_stats",
    "help",
]

# Self-Service Operations - Users can perform these on their own resources
SELF_SERVICE_OPERATIONS = ["reset_own_password", "view_own_user_info", "add_ip_whitelist"]

# Notification Settings
RBAC_NOTIFY_ADMIN_ON_DENIED = True
RBAC_LOG_ACCESS_ATTEMPTS = True
