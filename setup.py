#!/usr/bin/env python3
"""
Setup script for MongoDB Slack Bot
Helps users install dependencies and configure the bot
"""

import os
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print setup banner"""
    print(
        """
🚀 MongoDB Atlas Slack Bot Setup
================================

This script will help you set up the MongoDB Slack Bot with all necessary dependencies
and configuration.
"""
    )


def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")

    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def check_node_version():
    """Check if Node.js is installed for MCP server"""
    print("\n🔍 Checking Node.js version...")

    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js {version} is installed")

            # Check if version is >= 20.10.0
            version_parts = version.lstrip("v").split(".")
            major, minor = int(version_parts[0]), int(version_parts[1])

            if major >= 20 and minor >= 10:
                return True
            else:
                print("⚠️  Node.js 20.10.0 or higher is recommended for MCP server")
                return True
        else:
            print("❌ Node.js not found")
            return False

    except FileNotFoundError:
        print("❌ Node.js not found")
        print("   Please install Node.js 20.10.0 or higher from https://nodejs.org/")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")

    try:
        # Install dependencies
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True
        )
        print("✅ Python dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def test_mcp_server():
    """Test MongoDB MCP server installation"""
    print("\n🔍 Testing MongoDB MCP server...")

    try:
        result = subprocess.run(
            ["npx", "-y", "mongodb-mcp-server", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ MongoDB MCP server is available")
            return True
        else:
            print("❌ MongoDB MCP server test failed")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️  MongoDB MCP server test timed out (this is normal)")
        return True
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False


def create_config_file():
    """Create configuration file from example"""
    print("\n⚙️  Setting up configuration...")

    config_example = Path("config.example.py")
    config_file = Path("config.py")

    if not config_example.exists():
        print("❌ config.example.py not found")
        return False

    if config_file.exists():
        response = input("Config file already exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            print("⚠️  Skipping config file creation")
            return True

    # Copy example to config
    with open(config_example, "r") as src:
        content = src.read()

    with open(config_file, "w") as dst:
        dst.write(content)

    print("✅ Configuration file created (config.py)")
    print("   Please edit config.py with your actual credentials")
    return True


def check_configuration():
    """Check if configuration is set up"""
    print("\n🔍 Checking configuration...")

    try:
        # Check environment variables
        required_vars = [
            "SLACK_BOT_TOKEN",
            "SLACK_APP_TOKEN",
            "SLACK_SIGNING_SECRET",
            "ANTHROPIC_API_KEY",
            "MONGODB_ATLAS_CLIENT_ID",
            "MONGODB_ATLAS_CLIENT_SECRET",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            print("⚠️  Missing environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("   Please set these environment variables or update config.py")
            return False
        else:
            print("✅ All environment variables are set")
            return True

    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False


def run_tests():
    """Run the test suite"""
    print("\n🧪 Running test suite...")

    try:
        result = subprocess.run([sys.executable, "test_bot.py"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ All tests passed")
            print(result.stdout)
            return True
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            return False

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print(
        """
🎉 Setup Complete!

Next steps:
1. Configure your credentials in config.py or environment variables
2. Set up your Slack app (see README.md for instructions)
3. Create MongoDB Atlas service account credentials
4. Configure RBAC settings (admin users/groups in config.py)
5. Run the bot: python3 mongo_bot.py

🔐 RBAC Security Features:
- Admin users can create/modify/delete resources
- Regular users can view and analyze data
- Self-service operations for password resets
- Automatic admin notifications for denied access

For help:
- Check README.md for detailed setup instructions
- Run: python3 test_bot.py to test functionality
- Use: python3 mongo_bot.py --help for runtime options

Happy bot building! 🤖
"""
    )


def main():
    """Main setup function"""
    print_banner()

    # Check prerequisites
    if not check_python_version():
        return False

    if not check_node_version():
        return False

    # Install dependencies
    if not install_dependencies():
        return False

    # Test MCP server
    if not test_mcp_server():
        print("⚠️  MCP server test failed, but continuing...")

    # Create config file
    if not create_config_file():
        return False

    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but setup is complete")

    # Print next steps
    print_next_steps()

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
