---
layout: default
title: Contributing
parent: Developer Guide
nav_order: 4
description: "Details about Contributing in n8n-deploy"
---

# Contributing to n8n-deploy

{: .note }
> For the complete contributing guide, see [CONTRIBUTING.md](https://github.com/lehcode/n8n-deploy/blob/master/CONTRIBUTING.md)

{: .warning }
> **Important**: By contributing, you agree to follow our [Code of Conduct](https://github.com/lehcode/n8n-deploy/blob/master/CODE_OF_CONDUCT.md) and development practices.

## Getting Started

### Prerequisites

- Python 3.8+
- `pip` or `uv`
- Git
- Basic understanding of CLI tools and workflows

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
```

## Contribution Workflow

### 1. Find an Issue

- Check [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues/)
- Look for "good first issue" or "help wanted" labels
- Discuss potential changes in the issue comments

### 2. Fork and Branch

```bash
# Fork on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/n8n-deploy.git
cd n8n-deploy

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 3. Development Guidelines

{: .tip }
> Follow these practices to ensure code quality and consistency.

#### Code Style
- Use `black` for formatting
- Use `mypy --strict` for type checking
- Write comprehensive type annotations
- Keep functions small and focused

#### Commit Messages
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Use imperative mood ("Add feature" not "Added feature")

### 4. Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests
python run_tests.py --all
```

{: .warning }
> All tests must pass before submitting a pull request.

### 5. Documentation

- Update relevant documentation
- Add/update tests for new functionality
- Ensure documentation is clear and concise

### 6. Pull Request

```bash
# Push your changes
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

## Code of Conduct

1. Be respectful and inclusive
2. Provide constructive feedback
3. Focus on the code, not the person
4. Ask questions, don't make assumptions

{: .note }
> "In open source, we feel strongly that to really do something well, you have to get a lot of people involved." — Linus Torvalds

## Reporting Bugs

- Use GitHub Issues
- Provide a clear, minimal reproduction
- Include your environment details
- Be patient and responsive

## Feature Requests

- Open an issue first to discuss
- Explain the use case
- Provide potential implementation ideas
- Be open to feedback

{: .warning }
> Not all features will be accepted. Maintainers prioritize project goals and simplicity.