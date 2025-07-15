#!/bin/bash

# MongoDB Atlas Slack Bot - Python Environment Setup
# This script sets up the correct Python environment using pyenv

echo "🐍 Setting up Python environment for MongoDB Atlas Slack Bot..."

# Add pyenv to PATH if not already present
if ! command -v pyenv &> /dev/null; then
    echo "📝 Adding pyenv to PATH..."
    export PATH="/opt/homebrew/bin:$PATH"
    eval "$(pyenv init -)"
fi

# Check if we're in the correct directory
if [ ! -f ".python-version" ]; then
    echo "⚠️  Warning: .python-version file not found. Make sure you're in the MongoBot directory."
    echo "Current directory: $(pwd)"
    exit 1
fi

# Set the Python version
PYTHON_VERSION=$(cat .python-version)
echo "🔧 Setting Python version to $PYTHON_VERSION..."
pyenv local $PYTHON_VERSION

# Verify Python version
CURRENT_VERSION=$(python --version)
echo "✅ Python version: $CURRENT_VERSION"

# Check if virtual environment should be created
if [ "$1" = "--create-venv" ]; then
    echo "🏗️  Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

echo "🎉 Python environment setup complete!"
echo ""
echo "💡 To use this environment in new terminal sessions:"
echo "   source setup-env.sh"
echo ""
echo "🚀 Next steps:"
echo "   make install     # Install dependencies"
echo "   make test        # Run tests"
echo "   make run         # Start the bot" 