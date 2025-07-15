# Contributing to MongoDB Atlas Slack Bot

Thank you for your interest in contributing! We welcome all improvements, bug fixes, and new features.

## 🛠️ How to Contribute

### 1. Fork the Repository
- Click the **Fork** button on GitHub to create your own copy.

### 2. Clone Your Fork
```bash
git clone https://github.com/your-username/MongoBot.git
cd MongoBot
```

### 3. Create a Branch
- Use a descriptive branch name:
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow the code style and linting rules (see below).
- Add or update tests as needed.

### 5. Run Quality Checks
- Run the full QA pipeline before pushing:
```bash
make qa
```
- Or use the quick pre-commit check:
```bash
make pre-commit
```
- Ensure all lint, test, and security checks pass.

### 6. Commit and Push
```bash
git add .
git commit -m "Describe your change"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request
- Go to your fork on GitHub and click **New Pull Request**.
- Fill in the PR template and describe your changes.
- Reference any related issues.

### 8. Code Review
- Your PR will be reviewed by maintainers.
- Please respond to feedback and make any requested changes.

### 9. Issue Reporting
- Use GitHub Issues to report bugs, request features, or ask questions.
- Please provide as much detail as possible (logs, steps to reproduce, etc).

## 🧑‍💻 Code Style & Quality
- Follow PEP8 and project linting rules.
- Use type annotations where possible.
- Run `make lint` and `make format` before committing.
- Pre-commit hooks will enforce code quality.

## 🧪 Tests
- Add or update tests for new features and bug fixes.
- Run `make test` to verify.

## 🪝 Pre-commit Hooks
- Install with `make pre-commit-setup`.
- Hooks will run automatically on commit.

## 🤝 Community
- Be respectful and constructive in all communications.
- See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) if available.

---

For build and environment setup, see [BUILD.md](./BUILD.md).
For user documentation and features, see [README.md](./README.md).
