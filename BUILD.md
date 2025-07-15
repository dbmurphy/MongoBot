# Build & Development Guide

This document covers all aspects of building, testing, linting, and developing the MongoDB Atlas Slack Bot.

## 🏗️ Environment Setup

- **Python**: 3.10.15 (managed via pyenv)
- **Node.js**: 20.10.0+
- **macOS**: Homebrew recommended
- **pyenv**: For Python version management

### Quick Start
```bash
make setup      # Complete project setup
make test       # Run tests
make lint       # Run linting checks
make format     # Format code
make run        # Run the bot
```

## 🛠️ Makefile Targets

| Target              | Description                                      |
|---------------------|--------------------------------------------------|
| `help`              | Show available commands                          |
| `setup`             | Complete project setup (install deps, dev tools, run tests) |
| `install`           | Install project dependencies                     |
| `dev-setup`         | Install development dependencies                 |
| `test`              | Run test suite                                   |
| `lint`              | Run linting checks (flake8, pylint, mypy)        |
| `format`            | Format code (black, isort)                       |
| `security`          | Run security checks (bandit, safety)             |
| `check`             | Run all checks (syntax, lint, security)          |
| `syntax-check`      | Check Python syntax                              |
| `run`               | Run the MongoDB Slack Bot                        |
| `build`             | Build project (run all checks and tests)         |
| `clean`             | Clean temporary files and cache                  |
| `docs`              | Show documentation info                          |
| `config-check`      | Check configuration setup                        |
| `validate`          | Validate entire project                          |
| `ci`                | Run CI/CD pipeline locally                       |
| `dev`               | Start development environment                    |
| `info`              | Show project information                         |
| `python-version`    | Show Python version and environment info         |
| `qa`                | Complete Quality Assurance pipeline              |
| `qc`                | Alias for qa (Quality Control)                   |
| `pre-commit`        | Quick pre-commit checks                          |
| `pre-commit-setup`  | Setup pre-commit hooks                           |
| `lint-stats`        | Show detailed linting statistics                 |

## 🧹 Cleaning
- `make clean` removes all temp, cache, build, and output files.

## 🧪 Testing
- `make test` runs the test suite.
- Test files should be named `test_*.py`.

## 🧑‍💻 Linting & Formatting
- `make lint` runs flake8, pylint, and mypy.
- `make format` runs black and isort.
- Config files: `.flake8`, `.pylintrc`.

## 🔒 Security
- `make security` runs bandit and safety.
- Security reports are output to `security-report.json`.

## 🪝 Pre-commit Hooks
- Install with `make pre-commit-setup`.
- Hooks run format, lint, test, and security checks before each commit.
- Configured in `.pre-commit-config.yaml`.

## 🏗️ CI/CD
- `make ci` runs the full pipeline locally.

## 📝 Configuration Files
- `.flake8` for flake8
- `.pylintrc` for pylint
- `.pre-commit-config.yaml` for pre-commit
- `.gitignore` for ignored files

## 🐍 Python Version
- `.python-version` specifies the required Python version.

## 🧑‍💻 Developer Workflow
- Use `make qa` or `make qc` for full quality checks before committing.
- Use `make pre-commit` for a quick check.
- Use `make clean` to reset your environment.

---

For user-facing features, usage, and bot commands, see [README.md](./README.md).
For contribution guidelines, see [CONTRIBUTE.md](./CONTRIBUTE.md).
