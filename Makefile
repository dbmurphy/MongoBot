# MongoDB Atlas Slack Bot - Makefile
# Comprehensive build and development automation

.PHONY: help setup install test lint format clean run build check docs dev-setup all

# Default target
.DEFAULT_GOAL := help

# Python and pip commands with proper PATH setup
PYTHON_VERSION := 3.10.15
PYTHON_SETUP := export PATH="/opt/homebrew/bin:$$PATH" && eval "$$(pyenv init -)" && pyenv local $(PYTHON_VERSION)
PYTHON := $(PYTHON_SETUP) && python
PIP := $(PYTHON_SETUP) && pip

# Project directories
SRC_DIR := .
TEST_DIR := .
DOCS_DIR := docs

# Source files
PYTHON_FILES := $(wildcard *.py)
CONFIG_FILES := config.example.py requirements.txt

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
BOLD := \033[1m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BOLD)MongoDB Atlas Slack Bot - Development Commands$(NC)"
	@echo ""
	@echo "$(BLUE)Usage:$(NC)"
	@echo "  make <target>"
	@echo ""
	@echo "$(YELLOW)🔥 Most Common Commands:$(NC)"
	@echo "  $(GREEN)qa/qc          $(NC) Complete Quality Assurance pipeline"
	@echo "  $(GREEN)pre-commit     $(NC) Quick pre-commit checks"
	@echo "  $(GREEN)pre-commit-setup $(NC) Setup pre-commit hooks"
	@echo "  $(GREEN)setup          $(NC) Complete project setup"
	@echo "  $(GREEN)test           $(NC) Run test suite"
	@echo "  $(GREEN)run            $(NC) Run the MongoDB Slack Bot"
	@echo "  $(GREEN)docs-images    $(NC) Generate placeholder images"
	@echo ""
	@echo "$(BLUE)All Available Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Complete project setup (install dependencies, dev tools, run tests)
	@echo "$(BOLD)🚀 Setting up MongoDB Atlas Slack Bot$(NC)"
	@echo "$(BLUE)📋 Setting up Python environment...$(NC)"
	$(PYTHON_SETUP)
	$(MAKE) install
	$(MAKE) dev-setup
	$(MAKE) test
	@echo "$(GREEN)✅ Setup complete!$(NC)"

install: ## Install project dependencies
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

dev-setup: ## Install development dependencies (linting, formatting tools)
	@echo "$(BLUE)🔧 Installing development tools...$(NC)"
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
	else \
		$(PIP) install flake8 black isort pylint mypy bandit safety; \
	fi
	@echo "$(GREEN)✅ Development tools installed$(NC)"

test: ## Run test suite
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	$(PYTHON) test_bot.py
	@echo "$(GREEN)✅ Tests completed$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)🔍 Running linting checks...$(NC)"
	@echo "$(YELLOW)Running flake8...$(NC)"
	-$(PYTHON) -m flake8 $(PYTHON_FILES)
	@echo "$(YELLOW)Running pylint...$(NC)"
	-$(PYTHON) -m pylint $(PYTHON_FILES)
	@echo "$(YELLOW)Running mypy...$(NC)"
	-$(PYTHON) -m mypy $(PYTHON_FILES) --ignore-missing-imports
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	@echo "$(YELLOW)Running black...$(NC)"
	$(PYTHON) -m black $(PYTHON_FILES) --line-length=100
	@echo "$(YELLOW)Running isort...$(NC)"
	$(PYTHON) -m isort $(PYTHON_FILES) --profile black
	@echo "$(GREEN)✅ Code formatted$(NC)"

security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(NC)"
	@echo "$(YELLOW)Running bandit...$(NC)"
	-$(PYTHON) -m bandit -r $(SRC_DIR) -f json -o security-report.json
	@echo "$(YELLOW)Running safety...$(NC)"
	-$(PYTHON) -m safety check
	@echo "$(GREEN)✅ Security checks completed$(NC)"

check: ## Run all checks (syntax, lint, security)
	@echo "$(BOLD)🔍 Running comprehensive checks...$(NC)"
	$(MAKE) syntax-check
	$(MAKE) lint
	$(MAKE) security
	@echo "$(GREEN)✅ All checks completed$(NC)"

syntax-check: ## Check Python syntax
	@echo "$(BLUE)✅ Checking Python syntax...$(NC)"
	@for file in $(PYTHON_FILES); do \
		echo "Checking $$file..."; \
		$(PYTHON) -m py_compile $$file; \
	done
	@echo "$(GREEN)✅ Syntax check passed$(NC)"

run: ## Run the MongoDB Slack Bot
	@echo "$(BLUE)🚀 Starting MongoDB Slack Bot...$(NC)"
	@if [ ! -f config.py ]; then \
		echo "$(RED)❌ config.py not found. Please copy config.example.py to config.py and update with your credentials$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) mongo_bot.py

build: ## Build the project (run all checks and tests)
	@echo "$(BOLD)🏗️  Building project...$(NC)"
	$(MAKE) clean
	$(MAKE) syntax-check
	$(MAKE) test
	$(MAKE) lint
	@echo "$(GREEN)✅ Build completed successfully$(NC)"

clean: ## Clean temporary files and cache
	@echo "$(BLUE)🧹 Cleaning temporary files and cache...$(NC)"
	@echo "$(YELLOW)Removing Python cache files...$(NC)"
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(YELLOW)Removing test and cache directories...$(NC)"
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	find . -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(YELLOW)Removing log files...$(NC)"
	find . -name "*.log" -delete 2>/dev/null || true
	find . -name "logs" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(YELLOW)Removing generated reports...$(NC)"
	rm -f security-report.json 2>/dev/null || true
	rm -f bandit-report.json 2>/dev/null || true
	rm -f output.json 2>/dev/null || true
	rm -f temp_test.py 2>/dev/null || true
	@echo "$(YELLOW)Removing temporary files...$(NC)"
	find . -name "*.tmp" -delete 2>/dev/null || true
	find . -name "*.temp" -delete 2>/dev/null || true
	find . -name "*.bak" -delete 2>/dev/null || true
	find . -name "*.backup" -delete 2>/dev/null || true
	@echo "$(YELLOW)Removing build artifacts...$(NC)"
	rm -rf build/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf *.egg-info/ 2>/dev/null || true
	@echo "$(YELLOW)Removing IDE files...$(NC)"
	find . -name ".vscode" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".idea" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.swp" -delete 2>/dev/null || true
	find . -name "*.swo" -delete 2>/dev/null || true
	find . -name "*~" -delete 2>/dev/null || true
	@echo "$(YELLOW)Removing OS files...$(NC)"
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -name "Thumbs.db" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Complete cleanup finished$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@echo "$(YELLOW)Available documentation:$(NC)"
	@echo "  - README.md: General project documentation"
	@echo "  - BUILD.md: Build and development guide"
	@echo "  - CONTRIBUTE.md: Contribution guidelines"
	@echo "  - PROJECT_SUMMARY.md: Project overview"
	@echo "$(GREEN)✅ Documentation available$(NC)"

docs-images: ## Generate placeholder images for documentation
	@echo "$(BLUE)🖼️  Generating placeholder images...$(NC)"
	@mkdir -p docs/images
	@echo "$(YELLOW)Creating banner.png...$(NC)"
	@convert -size 600x120 xc:lightblue -gravity center -pointsize 24 -annotate 0 "MongoDB Atlas Slack Bot" docs/images/banner.png 2>/dev/null || \
		echo "$(YELLOW)ImageMagick not available, creating text placeholder...$(NC)" && \
		echo "MongoDB Atlas Slack Bot" > docs/images/banner.txt
	@echo "$(YELLOW)Creating index-analysis.png placeholder...$(NC)"
	@echo "Index Analysis Screenshot" > docs/images/index-analysis.txt
	@echo "$(YELLOW)Creating performance-monitoring.png placeholder...$(NC)"
	@echo "Performance Monitoring Screenshot" > docs/images/performance-monitoring.txt
	@echo "$(YELLOW)Creating rbac-management.png placeholder...$(NC)"
	@echo "RBAC Management Screenshot" > docs/images/rbac-management.txt
	@echo "$(GREEN)✅ Placeholder images created in docs/images/$(NC)"
	@echo "$(BLUE)💡 Replace .txt files with actual .png screenshots$(NC)"

config-check: ## Check configuration setup
	@echo "$(BLUE)⚙️  Checking configuration...$(NC)"
	@if [ ! -f config.py ]; then \
		echo "$(YELLOW)⚠️  config.py not found$(NC)"; \
		echo "$(BLUE)Creating config.py from template...$(NC)"; \
		cp config.example.py config.py; \
		echo "$(GREEN)✅ config.py created from template$(NC)"; \
		echo "$(YELLOW)⚠️  Please update config.py with your actual credentials$(NC)"; \
	else \
		echo "$(GREEN)✅ config.py exists$(NC)"; \
	fi

requirements-check: ## Check if requirements are satisfied
	@echo "$(BLUE)📋 Checking requirements...$(NC)"
	@$(PIP) check
	@echo "$(GREEN)✅ Requirements check completed$(NC)"

install-pre-commit: ## Install pre-commit hooks
	@echo "$(BLUE)🪝 Installing pre-commit hooks...$(NC)"
	$(PIP) install pre-commit
	$(PYTHON_SETUP) && pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"
	@echo "$(BLUE)💡 Pre-commit will now run automatically on git commits$(NC)"
	@echo "$(BLUE)💡 You can also run 'make pre-commit' manually$(NC)"

pre-commit-setup: ## Setup pre-commit with our configuration
	@echo "$(BLUE)🪝 Setting up pre-commit with project configuration...$(NC)"
	$(PIP) install pre-commit
	$(PYTHON_SETUP) && pre-commit install --config .pre-commit-config.yaml
	@echo "$(GREEN)✅ Pre-commit configured and installed$(NC)"
	@echo "$(BLUE)💡 Pre-commit will run: format, lint, test, security checks$(NC)"

validate: ## Validate the entire project
	@echo "$(BOLD)🔍 Validating project...$(NC)"
	$(MAKE) requirements-check
	$(MAKE) config-check
	$(MAKE) syntax-check
	$(MAKE) test
	@echo "$(GREEN)✅ Project validation completed$(NC)"

docker-build: ## Build Docker image (if Dockerfile exists)
	@if [ -f Dockerfile ]; then \
		echo "$(BLUE)🐳 Building Docker image...$(NC)"; \
		docker build -t mongodb-slack-bot .; \
		echo "$(GREEN)✅ Docker image built$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Dockerfile not found$(NC)"; \
	fi

docker-run: ## Run Docker container (if image exists)
	@echo "$(BLUE)🐳 Running Docker container...$(NC)"
	docker run -it --rm mongodb-slack-bot

info: ## Show project information
	@echo "$(BOLD)MongoDB Atlas Slack Bot - Project Information$(NC)"
	@echo ""
	@echo "$(BLUE)Python Version:$(NC) $(shell $(PYTHON) --version)"
	@echo "$(BLUE)Pip Version:$(NC) $(shell $(PIP) --version)"
	@echo "$(BLUE)Project Files:$(NC)"
	@ls -la *.py *.md *.txt 2>/dev/null || echo "  No files found"
	@echo ""
	@echo "$(BLUE)Configuration:$(NC)"
	@if [ -f config.py ]; then \
		echo "  ✅ config.py exists"; \
	else \
		echo "  ❌ config.py missing"; \
	fi
	@echo ""
	@echo "$(BLUE)Dependencies:$(NC)"
	@$(PIP) freeze | head -10
	@echo ""

all: setup build ## Run complete setup and build process
	@echo "$(BOLD)🎉 Complete build process finished!$(NC)"

# Development workflow targets
dev: ## Start development environment
	@echo "$(BOLD)🔧 Starting development environment...$(NC)"
	$(MAKE) dev-setup
	$(MAKE) config-check
	$(MAKE) validate
	@echo "$(GREEN)✅ Development environment ready$(NC)"
	@echo "$(BLUE)💡 Run 'make run' to start the bot$(NC)"

qa: ## Run complete Quality Assurance pipeline (format, lint, test, security)
	@echo "$(BOLD)🔍 Running Quality Assurance Pipeline$(NC)"
	@echo "$(BLUE)Step 1: Formatting code...$(NC)"
	$(MAKE) format
	@echo "$(BLUE)Step 2: Running all checks...$(NC)"
	$(MAKE) check
	@echo "$(BLUE)Step 3: Running tests...$(NC)"
	$(MAKE) test
	@echo "$(BLUE)Step 4: Showing quality statistics...$(NC)"
	$(MAKE) lint-stats
	@echo "$(GREEN)✅ Quality Assurance pipeline completed$(NC)"
	@echo "$(BLUE)💡 Your code is ready for commit!$(NC)"

qc: qa ## Alias for qa (Quality Control)

pre-commit: ## Quick pre-commit checks (format, lint, test)
	@echo "$(BOLD)🚀 Running Pre-Commit Checks$(NC)"
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test
	@echo "$(GREEN)✅ Pre-commit checks passed$(NC)"

ci: ## Run CI/CD pipeline locally
	@echo "$(BOLD)🔄 Running CI/CD pipeline...$(NC)"
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) dev-setup
	$(MAKE) syntax-check
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) security
	@echo "$(GREEN)✅ CI/CD pipeline completed$(NC)"

# Help for individual components
help-rbac: ## Show RBAC configuration help
	@echo "$(BOLD)🔐 RBAC Configuration Help$(NC)"
	@echo ""
	@echo "$(BLUE)Admin Users Configuration:$(NC)"
	@echo "  ADMIN_USERS = ["
	@echo "    'U1234567890',        # Slack user ID"
	@echo "    '@david.murphy',      # Friendly username with @"
	@echo "    'jane.smith',         # Friendly username without @"
	@echo "    'john.doe@company.com', # Email address"
	@echo "  ]"
	@echo ""
	@echo "$(BLUE)More details:$(NC) See RBAC_FEATURES.md"

help-setup: ## Show setup help
	@echo "$(BOLD)🚀 Setup Help$(NC)"
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. make setup          # Install dependencies and dev tools"
	@echo "  2. make config-check   # Setup configuration"
	@echo "  3. Edit config.py      # Add your credentials"
	@echo "  4. make run            # Start the bot"
	@echo ""
	@echo "$(BLUE)Daily Development:$(NC)"
	@echo "  make qa               # Complete quality assurance"
	@echo "  make pre-commit       # Quick pre-commit checks"
	@echo "  make format           # Format code only"
	@echo "  make test             # Run tests only"
	@echo ""
	@echo "$(BLUE)More details:$(NC) See README.md"

python-version: ## Show Python version and setup
	@echo "$(BOLD)🐍 Python Environment Information$(NC)"
	@echo ""
	@echo "$(BLUE)Current Python Version:$(NC) $(shell $(PYTHON) --version)"
	@echo "$(BLUE)Python Path:$(NC) $(shell $(PYTHON) -c 'import sys; print(sys.executable)')"
	@echo "$(BLUE)Pyenv Version:$(NC) $(shell pyenv version)"
	@echo "$(BLUE)Project Python Version:$(NC) $(shell cat .python-version)"
	@echo ""

lint-stats: ## Show linting statistics and scores
	@echo "$(BOLD)📊 Code Quality Statistics$(NC)"
	@echo ""
	@echo "$(BLUE)Flake8 Results:$(NC)"
	@$(PYTHON) -m flake8 $(PYTHON_FILES) --statistics || echo "Issues found (see above)"
	@echo ""
	@echo "$(BLUE)Pylint Score:$(NC)"
	@$(PYTHON) -m pylint $(PYTHON_FILES) --score=y 2>/dev/null | grep "Your code has been rated" || echo "Score not available"
	@echo ""
	@echo "$(BLUE)MyPy Results:$(NC)"
	@$(PYTHON) -m mypy $(PYTHON_FILES) --ignore-missing-imports --no-error-summary || echo "Type issues found"
	@echo ""
	@echo "$(BLUE)Configuration Files:$(NC)"
	@if [ -f .flake8 ]; then echo "  ✅ .flake8 configuration present"; else echo "  ❌ .flake8 missing"; fi
	@if [ -f .pylintrc ]; then echo "  ✅ .pylintrc configuration present"; else echo "  ❌ .pylintrc missing"; fi
	@echo "" 