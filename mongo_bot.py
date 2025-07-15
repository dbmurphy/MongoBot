#!/usr/bin/env python3
"""
MongoDB Atlas Slack Bot
A Slack bot that uses MongoDB MCP server with Claude 4 LLM for Atlas management
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime

import anthropic
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from command_handler import MongoCommandHandler
from rbac import RBACManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoSlackBot:
    def __init__(self):
        # Initialize Slack app
        self.app = AsyncApp(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )

        # Initialize Claude client
        self.claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # MCP session
        self.mcp_session = None

        # Command handler
        self.command_handler = None

        # RBAC manager
        self.rbac_manager = None

        # Bot user ID
        self.bot_user_id = None

        # Setup event handlers
        self.setup_handlers()

    async def setup_mcp_connection(self):
        """Setup connection to MongoDB MCP server"""
        try:
            # MCP server parameters
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "mongodb-mcp-server",
                    "--apiClientId",
                    os.environ.get("MONGODB_ATLAS_CLIENT_ID"),
                    "--apiClientSecret",
                    os.environ.get("MONGODB_ATLAS_CLIENT_SECRET"),
                    "--connectionString",
                    os.environ.get("MONGODB_CONNECTION_STRING", ""),
                    "--logPath",
                    "/tmp/mcp-logs",
                ],
                env={
                    "MDB_MCP_API_CLIENT_ID": os.environ.get("MONGODB_ATLAS_CLIENT_ID"),
                    "MDB_MCP_API_CLIENT_SECRET": os.environ.get("MONGODB_ATLAS_CLIENT_SECRET"),
                    "MDB_MCP_CONNECTION_STRING": os.environ.get("MONGODB_CONNECTION_STRING", ""),
                    "MDB_MCP_LOG_PATH": "/tmp/mcp-logs",
                },
            )

            # Create MCP client session
            self.mcp_session = await stdio_client(server_params)

            # Initialize command handler
            self.command_handler = MongoCommandHandler(self.mcp_session)
            await self.command_handler.refresh_tools()

            # List available tools
            tools_response = await self.mcp_session.list_tools()
            logger.info(f"Available MCP tools: {[tool.name for tool in tools_response.tools]}")

            return True

        except Exception as e:
            logger.error(f"Failed to setup MCP connection: {e}")
            return False

    def setup_handlers(self):
        """Setup Slack event handlers"""

        @self.app.event("app_mention")
        async def handle_app_mention(event, say, client):
            """Handle app mentions in channels"""
            await self.process_message(event, say, client)

        @self.app.event("message")
        async def handle_direct_message(event, say, client):
            """Handle direct messages to the bot"""
            # Only respond to direct messages (not channel messages)
            if event.get("channel_type") == "im":
                await self.process_message(event, say, client)

        @self.app.command("/mongo")
        async def handle_mongo_command(ack, respond, command, client):
            """Handle /mongo slash command"""
            await ack()

            # Create a mock event for processing
            mock_event = {
                "text": command["text"],
                "user": command["user_id"],
                "channel": command["channel_id"],
                "ts": command.get("trigger_id", str(datetime.now().timestamp())),
            }

            async def mock_say(text=None, blocks=None, **kwargs):
                await respond(text=text, blocks=blocks, **kwargs)

            await self.process_message(mock_event, mock_say, client)

    async def process_message(self, event, say, client):
        """Process incoming messages and route to appropriate handlers"""
        try:
            # Get bot user ID if not cached
            if not self.bot_user_id:
                auth_response = await client.auth_test()
                self.bot_user_id = auth_response["user_id"]

            # Initialize RBAC manager if not already done
            if not self.rbac_manager:
                self.rbac_manager = RBACManager(client)

            # Extract message text
            text = event.get("text", "").strip()
            user_id = event.get("user")

            # Remove bot mention if present
            if f"<@{self.bot_user_id}>" in text:
                text = re.sub(f"<@{self.bot_user_id}>", "", text).strip()

            if not text:
                # Show available commands based on user permissions
                help_message = await self.get_personalized_help(user_id)
                await say(help_message)
                return

            # Show typing indicator
            await say("🔍 Analyzing your request...")

            # Setup MCP connection if not already done
            if not self.mcp_session:
                await self.setup_mcp_connection()

            # Process the command using Claude + MCP with RBAC
            response = await self.process_with_claude_and_mcp(text, user_id)

            # Send response back to Slack
            await say(response)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await say(f"❌ Sorry, I encountered an error: {str(e)}")

    async def process_with_claude_and_mcp(self, user_message: str, user_id: str) -> str:
        """Process user message using Claude LLM and MCP tools with RBAC"""
        try:
            # Use command handler to analyze and categorize the request
            command_info = self.command_handler.categorize_command(user_message)
            logger.info(f"Command categorized as: {command_info}")

            # If it's a help request, return personalized help
            if command_info["action"] == "help":
                return await self.get_personalized_help(user_id)

            # Check user permissions for this operation
            operation = command_info["action"]
            permission_check = await self.rbac_manager.check_user_permission(user_id, operation)

            if not permission_check["allowed"]:
                return await self.handle_permission_denied(
                    user_id, operation, permission_check["reason"]
                )

            # Handle RBAC commands specially
            if command_info["category"] == "rbac":
                return await self.handle_rbac_command(user_id, operation)

            # Execute the command using MCP tools
            mcp_results = await self.command_handler.execute_command(command_info)

            # Get available tools for context
            available_tools = self.command_handler.available_tools

            # Create system prompt for Claude to format results
            system_prompt = f"""You are a MongoDB Atlas assistant formatting results for Slack.

Original command: {user_message}
Command category: {command_info['category']}
Command action: {command_info['action']}
User permission level: {permission_check['reason']}

Available MCP tools: {', '.join(available_tools)}

Format the results clearly for Slack with:
- Use emojis for visual appeal (🚀 for clusters, 🔍 for analysis, 📊 for data, ⚠️ for warnings, ❌ for errors)
- Use code blocks for technical data
- Use bullet points for lists
- Keep it concise but informative
- If there are errors, explain them clearly and suggest solutions
- For performance analysis, provide actionable insights
- For database operations, summarize key findings

Present the data in a way that's easy to understand for technical teams."""

            # Use Claude to format the results for Slack
            claude_response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Format these MCP results for Slack:\n\n{json.dumps(mcp_results, indent=2)}",
                    }
                ],
            )

            return claude_response.content[0].text

        except Exception as e:
            logger.error(f"Error in Claude/MCP processing: {e}")
            return f"❌ Error processing request: {str(e)}\n\nTry asking for help to see available commands."

    async def get_personalized_help(self, user_id: str) -> str:
        """Get personalized help based on user permissions"""
        try:
            is_admin = await self.rbac_manager.is_user_admin(user_id)

            if is_admin:
                return """🤖 **MongoDB Atlas Assistant - Admin Access**

**📋 Available Commands:**

**🚀 Atlas Management (Admin):**
• `List my clusters` - View all clusters
• `Create a new cluster called [name]` - Create new cluster
• `Show cluster details for [cluster]` - Cluster information

**🔒 Security Management (Admin):**
• `Add IP [address] to whitelist` - Manage IP access
• `Reset password for user [name]` - Reset user passwords
• `Create database user [name]` - Create new users

**🔧 Database Operations (Admin):**
• `Create index on [collection] for [field]` - Index management
• `Insert document into [collection]` - Add documents
• `Update documents in [collection]` - Modify documents
• `Delete documents from [collection]` - Remove documents

**📊 Analysis & Monitoring (All Users):**
• `Analyze cluster [name] performance` - Performance analysis
• `Show slow queries on cluster [name]` - Query analysis
• `Find missing indexes in [database]` - Optimization
• `List databases` - View databases
• `Show collections in [database]` - View collections

**🔐 Admin Privileges Active** - You have full access to all operations."""
            else:
                return """🤖 **MongoDB Atlas Assistant - User Access**

**📋 Available Commands:**

**📊 Analysis & Monitoring:**
• `List my clusters` - View cluster information
• `Analyze cluster [name] performance` - Performance analysis
• `Show slow queries on cluster [name]` - Query analysis
• `Find missing indexes in [database]` - Index optimization

**🔍 Database Information:**
• `List databases` - View available databases
• `Show collections in [database]` - View collections
• `Analyze schema for collection [name]` - Schema analysis
• `Show database statistics` - Database metrics

**📈 Performance Analysis:**
• `Performance issues on [cluster]` - Cluster analysis
• `Storage usage analysis` - Storage metrics
• `Query patterns analysis` - Query optimization

**ℹ️ User Access** - For admin operations (create/update/delete), please contact an administrator."""

        except Exception as e:
            logger.error(f"Error generating personalized help: {e}")
            return self.command_handler._get_help_text()

    async def handle_permission_denied(self, user_id: str, operation: str, reason: str) -> str:
        """Handle permission denied scenarios"""
        try:
            # Get user info for better messaging
            user_info = await self.app.client.users_info(user=user_id)
            username = user_info["user"]["name"] if user_info["ok"] else user_id

            # Get list of admins
            admin_info = await self.rbac_manager.get_admin_users_info()
            admin_mentions = []

            for admin in admin_info:
                if admin["type"] == "direct":
                    admin_mentions.append(f"<@{admin['user_id']}>")
                else:
                    admin_mentions.append(f"@{admin['username']}")

            message = f"""🚫 **Access Denied**

**User:** @{username}
**Operation:** `{operation}`
**Reason:** {reason}

**What you can do:**
• Use `help` to see available commands for your role
• Contact an administrator for elevated access
• Try read-only operations like `list clusters` or `analyze performance`

**Administrators:** {', '.join(admin_mentions[:5])}{'...' if len(admin_mentions) > 5 else ''}
"""

            return message

        except Exception as e:
            logger.error(f"Error handling permission denied: {e}")
            return f"❌ Access denied: {reason}. Contact an administrator for help."

    async def handle_rbac_command(self, user_id: str, operation: str) -> str:
        """Handle RBAC-specific commands"""
        try:
            if operation == "rbac_report":
                # Only admins can see full RBAC report
                if not await self.rbac_manager.is_user_admin(user_id):
                    return "❌ Admin privileges required to view RBAC report"

                return self.rbac_manager.generate_rbac_report()

            elif operation == "list_admins":
                # Only admins can see admin list
                if not await self.rbac_manager.is_user_admin(user_id):
                    return "❌ Admin privileges required to view admin list"

                admin_info = await self.rbac_manager.get_admin_users_info()

                message = "👥 **Administrator List**\n\n"

                direct_admins = [admin for admin in admin_info if admin["type"] == "direct"]
                group_admins = [admin for admin in admin_info if admin["type"] == "group"]

                if direct_admins:
                    message += "**Direct Admin Users:**\n"
                    for admin in direct_admins:
                        message += f"• <@{admin['user_id']}> ({admin['real_name']})\n"
                    message += "\n"

                if group_admins:
                    message += "**Admin Groups:**\n"
                    for admin in group_admins:
                        message += f"• @{admin['username']}\n"
                    message += "\n"

                if not direct_admins and not group_admins:
                    message += "No administrators configured.\n"

                return message

            elif operation == "check_permissions":
                # Users can check their own permissions
                permissions = self.rbac_manager.get_user_permissions(user_id)
                is_admin = await self.rbac_manager.is_user_admin(user_id)

                message = "🔐 **Your Permissions**\n\n"
                message += f"**Access Level:** {'Admin' if is_admin else 'User'}\n\n"

                if is_admin:
                    message += "**Admin Operations Available:**\n"
                    for op in sorted(permissions["admin_operations"]):
                        message += f"• {op}\n"
                    message += "\n"

                message += "**User Operations Available:**\n"
                for op in sorted(permissions["allowed_operations"]):
                    message += f"• {op}\n"

                if permissions["self_service_operations"]:
                    message += "\n**Self-Service Operations:**\n"
                    for op in sorted(permissions["self_service_operations"]):
                        message += f"• {op}\n"

                return message

            else:
                return "❌ Unknown RBAC command"

        except Exception as e:
            logger.error(f"Error handling RBAC command: {e}")
            return f"❌ Error processing RBAC command: {str(e)}"

    async def start(self):
        """Start the Slack bot"""
        try:
            # Setup MCP connection
            await self.setup_mcp_connection()

            # Start socket mode handler
            handler = AsyncSocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
            await handler.start_async()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise


# Main execution
async def main():
    """Main function to run the bot"""
    bot = MongoSlackBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
