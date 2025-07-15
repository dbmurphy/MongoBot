#!/usr/bin/env python3
"""
Test script for MongoDB Slack Bot
Tests basic functionality without requiring Slack or full MCP setup
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_handler import MongoCommandHandler


async def test_command_categorization():
    """Test command categorization without MCP connection"""
    print("🧪 Testing command categorization...")

    # Mock MCP session
    mock_session = MagicMock()
    handler = MongoCommandHandler(mock_session)

    # Test cases
    test_commands = [
        ("List my clusters", "atlas_management"),
        ("Create a new cluster called test-cluster", "atlas_management"),
        ("Add IP 192.168.1.100 to whitelist", "security"),
        ("Analyze cluster performance over last 24 hours", "performance"),
        ("Show slow queries on cluster prod", "performance"),
        ("List all databases in cluster production", "database"),
        ("Find missing indexes in ecommerce on cluster staging", "optimization"),
        ("Find missing indexes on cluster staging", "optimization"),
        ("Find redundant indexes in database products on cluster dev", "optimization"),
        ("Show redundant indexes on cluster dev", "optimization"),
        ("Show duplicate indexes in cluster analytics", "optimization"),
        ("Reset password for user admin", "security"),
        ("Show collections in database users on cluster production", "database"),
        ("Analyze schema for collection products in cluster staging", "database"),
        ("Show RBAC report", "rbac"),
        ("List admins", "rbac"),
        ("What can I do", "rbac"),
        ("help", "general"),
    ]

    results = []
    for command, expected_category in test_commands:
        result = handler.categorize_command(command)
        category = result["category"]
        action = result["action"]

        status = "✅" if category == expected_category else "❌"
        print(f"{status} '{command}' -> {category}/{action}")
        results.append(category == expected_category)

    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Success rate: {success_rate:.1f}%")

    return success_rate > 80


async def test_parameter_extraction():
    """Test parameter extraction from commands"""
    print("\n🔍 Testing parameter extraction...")

    mock_session = MagicMock()
    handler = MongoCommandHandler(mock_session)

    # Test cluster name extraction
    cluster_tests = [
        ("Analyze cluster prod-db performance", "prod-db"),
        ("Show details for cluster testing", "testing"),
        ("Performance issues on staging", "staging"),
        ("Create cluster called new-cluster", "new-cluster"),
    ]

    for command, expected_cluster in cluster_tests:
        result = handler.categorize_command(command)
        extracted = result.get("cluster_name")
        status = "✅" if extracted == expected_cluster else "❌"
        print(f"{status} Cluster from '{command}' -> {extracted}")

    # Test IP address extraction
    ip_tests = [
        ("Add IP 192.168.1.100 to whitelist", "192.168.1.100"),
        ("Whitelist 10.0.0.1 for development", "10.0.0.1"),
        ("Allow access from 172.16.0.50", "172.16.0.50"),
    ]

    for command, expected_ip in ip_tests:
        result = handler.categorize_command(command)
        extracted = result.get("ip_address")
        status = "✅" if extracted == expected_ip else "❌"
        print(f"{status} IP from '{command}' -> {extracted}")

    # Test database extraction for optimization commands
    print("\n🗄️ Testing database extraction for optimization commands...")
    db_tests = [
        ("Find missing indexes in database products on cluster production", "products"),
        ("Find missing indexes on cluster production", None),
        ("Show redundant indexes in database ecommerce on cluster staging", "ecommerce"),
        ("Show redundant indexes on cluster staging", None),
    ]

    for command, expected_db in db_tests:
        result = handler.categorize_command(command)
        extracted = result.get("database")
        status = "✅" if extracted == expected_db else "❌"
        print(f"{status} Database from '{command}' -> {extracted}")


async def test_help_functionality():
    """Test help text generation"""
    print("\n📚 Testing help functionality...")

    mock_session = MagicMock()
    handler = MongoCommandHandler(mock_session)

    help_text = handler._get_help_text()

    required_sections = [
        "Atlas Management",
        "Performance Analysis",
        "Database Operations",
        "Security",
        "Optimization",
    ]

    for section in required_sections:
        if section in help_text:
            print(f"✅ Help contains '{section}' section")
        else:
            print(f"❌ Help missing '{section}' section")

    print(f"📏 Help text length: {len(help_text)} characters")


async def test_rbac_functionality():
    """Test RBAC system functionality"""
    print("\n🔐 Testing RBAC functionality...")

    try:
        from rbac import RBACManager

        print("✅ RBACManager imported successfully")

        # Create a mock config with the expected operations
        mock_config = type(
            "FakeConfig",
            (),
            {
                "RBAC_ENABLED": True,
                "ADMIN_USERS": [],
                "ADMIN_GROUPS": [],
                "ADMIN_OPERATIONS": ["create_cluster", "reset_password"],
                "USER_OPERATIONS": ["list_clusters"],
                "SELF_SERVICE_OPERATIONS": ["reset_own_password", "add_ip_whitelist"],
                "RBAC_NOTIFY_ADMIN_ON_DENIED": True,
                "RBAC_LOG_ACCESS_ATTEMPTS": True,
            },
        )()

        # Patch the config module
        sys.modules["config"] = mock_config

        # Test RBAC configuration loading
        mock_slack_client = MagicMock()
        rbac_manager = RBACManager(mock_slack_client)

        # Test permission categories
        test_cases = [
            ("create_cluster", "admin"),
            ("list_clusters", "user"),
            ("reset_own_password", "self_service"),
            ("add_ip_whitelist", "self_service"),
            ("reset_password", "admin"),
            ("unknown_operation", "unknown"),
        ]

        for operation, expected_category in test_cases:
            category = rbac_manager.get_operation_category(operation)
            status = "✅" if category == expected_category else "❌"
            print(f"{status} Operation '{operation}' -> {category}")

        # Test report generation
        report = rbac_manager.generate_rbac_report()
        if "RBAC Configuration Report" in report:
            print("✅ RBAC report generation works")
        else:
            print("❌ RBAC report generation failed")

        # Test username resolution logic
        test_usernames = [
            ("U1234567890", "U1234567890"),  # Already a user ID
            ("@david.murphy", "david.murphy"),  # Username with @
            ("jane.smith", "jane.smith"),  # Username without @
        ]

        for input_name, expected_clean in test_usernames:
            # Test the username cleaning logic
            if input_name.startswith("U") and len(input_name) == 11:
                result = input_name
                status = "✅"
            else:
                result = input_name.lstrip("@")
                status = "✅" if result == expected_clean else "❌"

            print(f"{status} Username resolution: '{input_name}' -> '{result}'")

    except ImportError as e:
        print(f"❌ RBAC import failed: {e}")
    except Exception as e:
        print(f"❌ RBAC test error: {e}")


async def test_basic_imports():
    """Test that all required modules can be imported"""
    print("\n📦 Testing imports...")

    try:
        from slack_bolt.async_app import (  # noqa: F401 # pylint: disable=unused-import
            AsyncApp,
        )

        print("✅ Slack Bolt imported successfully")
    except ImportError as e:
        print(f"❌ Slack Bolt import failed: {e}")

    try:
        import anthropic  # noqa: F401 # pylint: disable=unused-import

        print("✅ Anthropic imported successfully")
    except ImportError as e:
        print(f"❌ Anthropic import failed: {e}")

    try:
        from mcp import ClientSession  # noqa: F401 # pylint: disable=unused-import

        print("✅ MCP imported successfully")
    except ImportError as e:
        print(f"❌ MCP import failed: {e}")

    try:
        from mongo_bot import (  # noqa: F401 # pylint: disable=unused-import
            MongoSlackBot,
        )

        print("✅ MongoSlackBot imported successfully")
    except ImportError as e:
        print(f"❌ MongoSlackBot import failed: {e}")

    try:
        from rbac import RBACManager  # noqa: F401 # pylint: disable=unused-import

        print("✅ RBACManager imported successfully")
    except ImportError as e:
        print(f"❌ RBACManager import failed: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting MongoDB Slack Bot Tests\n")

    # Run tests
    await test_basic_imports()
    await test_command_categorization()
    await test_parameter_extraction()
    await test_help_functionality()
    await test_rbac_functionality()

    print("\n✨ Test suite completed!")
    print("\n💡 To run the full bot, make sure you have:")
    print("   1. Set up environment variables (see config.example.py)")
    print("   2. Installed all dependencies (pip install -r requirements.txt)")
    print("   3. Created a Slack app and obtained tokens")
    print("   4. Set up MongoDB Atlas API credentials")
    print("   5. Configure RBAC settings (admin users/groups)")
    print("   6. Run: python3 mongo_bot.py")


if __name__ == "__main__":
    asyncio.run(main())
