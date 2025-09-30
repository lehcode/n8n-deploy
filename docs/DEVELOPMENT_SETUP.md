# Development Setup Guide

> *"The sooner you start to code, the longer the program will take."* - Carlson's Law

## Overview

This guide provides comprehensive setup instructions for n8n-deploy development, from basic environment setup to advanced development workflows. The project supports Python 3.8-3.12 with modern tooling for efficient development.

## Quick Start

### Prerequisites

- **Python 3.8+** (3.9+ recommended for development)
- **Git** for version control
- **Optional**: `uv` for faster package management

### 1-Minute Setup

```bash
# Clone repository
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Install with wrapper script (auto-creates venv)
./n8n-deploy --help

# Or traditional setup
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev,test]"
```

## Environment Setup Options

### Option 1: UV (Recommended for Development)

UV provides the fastest package installation and dependency resolution:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv --python /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install -e ".[dev,test]"

# Install type stubs for external libraries
uv pip install types-requests types-click
```

**Benefits**:
- 10-100x faster than pip for dependency resolution
- Better dependency conflict detection
- Excellent for CI/CD environments

### Option 2: Traditional pip

Standard Python package management:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install project
python -m pip install --upgrade pip
pip install -e ".[dev,test]"

# Install type checking dependencies
pip install types-requests types-click
```

### Option 3: Development Wrapper Script

The project includes a wrapper script that handles environment setup automatically:

```bash
# No installation required - auto-creates .venv if needed
./n8n-deploy --help
./n8n-deploy db status
./n8n-deploy list

# For development work
export N8N_DEPLOY_APP_DIR=/path/to/dev/data
./n8n-deploy db init
```

**Features**:
- Automatic virtual environment creation
- Dependency installation on first run
- No system-wide installation required
- Perfect for testing and development

## Development Dependencies

### Core Dependencies

```toml
# Runtime dependencies
dependencies = [
    "click>=8.0.0",      # CLI framework
    "requests>=2.28.0",  # HTTP client for n8n API
    "pydantic>=2.0.0",   # Data validation and serialization
    "rich>=13.0.0",      # Rich terminal output
    "python-dateutil>=2.8.0",  # Date handling
    "tabulate>=0.9.0",   # Table formatting
    "colorama>=0.4.0",   # Cross-platform colored output
]
```

### Development Dependencies

```toml
# Development tools
dev = [
    "pytest>=7.0.0",     # Testing framework
    "black>=22.0.0",     # Code formatting
    "flake8>=4.0.0",     # Linting
    "mypy>=1.0.0",       # Type checking
    "pre-commit>=2.20.0", # Git hooks
]

# Testing dependencies
test = [
    "pytest>=7.0.0",      # Test runner
    "pytest-cov>=4.0.0",  # Coverage reporting
    "pytest-mock>=3.10.0", # Mocking utilities
    "assertpy>=1.1",      # Fluent assertions
]
```

### Type Checking Dependencies

```bash
# External type stubs for strict type checking
pip install types-requests types-click

# Development type stubs (if using additional libraries)
pip install types-tabulate types-colorama
```

## Development Tools Configuration

### 1. Code Formatting with Black

```bash
# Check formatting
black --check api/

# Auto-format code
black api/

# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'
```

**Integration**:
- Pre-commit hook automatically formats code
- CI pipeline validates formatting
- VSCode extension available for real-time formatting

### 2. Type Checking with MyPy

```bash
# Basic type checking
mypy api/

# Strict mode (CI requirement)
mypy api/ --strict

# Configuration ensures zero errors in strict mode
[tool.mypy]
python_version = "3.9"
warn_return_any = true
disallow_untyped_defs = true
strict_equality = true
```

**Development Tips**:
- Install type stubs: `pip install types-requests`
- Use `reveal_type()` for debugging type inference
- Clear cache: `rm -rf .mypy_cache/` if issues persist

### 3. Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Configuration (.pre-commit-config.yaml)
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

## Project Structure for Development

```
n8n-deploy/
├── api/                          # Core application code
│   ├── __init__.py              # Package exports
│   ├── cli.py                   # CLI interface (40k+ lines)
│   ├── manager.py               # Workflow orchestration
│   ├── n8n_deploy_db.py        # Database layer
│   ├── config.py               # Configuration management
│   ├── api_keys.py             # API key management
│   └── models.py               # Pydantic data models
├── tests/                       # Test suite
│   ├── conftest.py             # Pytest configuration
│   ├── helpers.py              # Test utilities
│   ├── fixtures/               # Test data
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── docs/                       # Documentation
├── .venv/                      # Virtual environment
├── pyproject.toml             # Project configuration
├── run_tests.py               # Custom test runner
└── ./n8n-deploy              # Development wrapper script
```

### Key Development Files

- **`pyproject.toml`**: All project configuration in one place
- **`run_tests.py`**: Custom test runner with verbose output
- **`./n8n-deploy`**: Wrapper script for development workflow
- **`tests/conftest.py`**: Comprehensive test fixtures and configuration

## Environment Variables for Development

### Core Configuration

```bash
# Required for database location
export N8N_DEPLOY_APP_DIR="/path/to/dev/data"

# Optional workflow directory
export N8N_FLOW_DIR="/path/to/your/workflows"

# Optional n8n server for integration testing
export N8N_SERVER_URL="http://localhost:5678"

# Test environment (prevents default workflow initialization)
export N8N_DEPLOY_TESTING=1
```

### Development Environment Setup

```bash
# Create development configuration script
cat > dev_env.sh << 'EOF'
#!/bin/bash
# Development environment setup

export N8N_DEPLOY_APP_DIR="$HOME/n8n-deploy-dev"
export N8N_FLOW_DIR="$HOME/n8n-workflows"
export N8N_SERVER_URL="http://localhost:5678"

# Create directories
mkdir -p "$N8N_DEPLOY_APP_DIR"
mkdir -p "$N8N_FLOW_DIR"

echo "✅ Development environment configured"
echo "   App dir: $N8N_DEPLOY_APP_DIR"
echo "   Flow dir: $N8N_FLOW_DIR"
echo "   Server: $N8N_SERVER_URL"
EOF

chmod +x dev_env.sh
source dev_env.sh
```

## Development Workflow

### 1. Initial Setup

```bash
# Clone and setup
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Setup environment
source dev_env.sh

# Install dependencies
uv pip install -e ".[dev,test]"
uv pip install types-requests types-click

# Initialize development database
./n8n-deploy db init
```

### 2. Code Development Cycle

```bash
# 1. Create feature branch
git checkout -b feature/new-functionality

# 2. Develop with live testing
./n8n-deploy --help  # Test CLI changes
python run_tests.py --unit  # Run unit tests

# 3. Type checking and formatting
mypy api/ --strict
black api/

# 4. Run comprehensive tests
python run_tests.py --all

# 5. Commit changes
git add .
git commit -m "feat: add new functionality"
```

### 3. Testing During Development

```bash
# Quick unit tests
python run_tests.py --unit

# Specific test file
python run_tests.py --specific tests/unit/test_models.py

# Integration tests
python run_tests.py --integration

# All tests with coverage
python run_tests.py --all --coverage

# Generate comprehensive report
python run_tests.py --report
```

### 4. Live Development Testing

```bash
# Test CLI directly
python api/cli.py --help

# Test specific commands
./n8n-deploy db status
./n8n-deploy list --no-emoji

# Test with different configurations
N8N_DEPLOY_APP_DIR=/tmp/test ./n8n-deploy db init
./n8n-deploy --app-dir /tmp/test list
```

## IDE Configuration

### Visual Studio Code

**Recommended Extensions**:
```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.mypy-type-checker",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-vscode.test-adapter-converter"
    ]
}
```

**Settings** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.mypyEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ]
}
```

### PyCharm

**Configuration**:
1. **Interpreter**: Set to `.venv/bin/python`
2. **Code Style**: Import Black configuration
3. **Type Checker**: Enable MyPy plugin
4. **Test Runner**: Configure pytest as default

## Performance Optimization for Development

### 1. Fast Dependency Installation

```bash
# Use uv for speed
uv pip install -e ".[dev,test]"

# Or use pip with cache
export PIP_CACHE_DIR=~/.cache/pip
pip install -e ".[dev,test]"
```

### 2. Fast Test Execution

```bash
# Run only fast tests
python run_tests.py --unit

# Parallel test execution
python -m pytest tests/unit/ -n auto

# Skip slow integration tests during development
python -m pytest tests/ -m "not slow"
```

### 3. Development Database

```bash
# Use in-memory database for unit tests
export N8N_DEPLOY_TESTING=1

# Separate development database
export N8N_DEPLOY_APP_DIR=/tmp/n8n-deploy-dev
```

## Multi-Version Python Testing

### Local Testing

```bash
# Test with pyenv (multiple Python versions)
pyenv install 3.8.18 3.9.18 3.10.13 3.11.7 3.12.1

# Create virtual environments for each version
for version in 3.8.18 3.9.18 3.10.13 3.11.7 3.12.1; do
    pyenv virtualenv $version n8n-deploy-$version
    pyenv activate n8n-deploy-$version
    pip install -e ".[dev,test]"
    python run_tests.py --unit --quiet
    pyenv deactivate
done
```

### Docker Testing (CI Simulation)

```bash
# Test in clean container environment
docker run --rm -v $(pwd):/app -w /app python:3.9-slim bash -c "
    apt-get update && apt-get install -y git
    pip install -e .[dev,test]
    pip install types-requests types-click
    python run_tests.py --all
"
```

## Common Development Tasks

### 1. Adding New CLI Commands

```bash
# 1. Add command to api/cli.py
@cli.command()
@click.argument("workflow_id")
@click.option("--app-dir", type=click.Path())
def new_command(workflow_id, app_dir):
    """New command implementation"""
    try:
        config = get_config(base_folder=app_dir)
        # Implementation
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

# 2. Test the command
./n8n-deploy new-command --help
./n8n-deploy new-command test_workflow

# 3. Add tests
# Create test in tests/unit/test_cli.py or tests/integration/
```

### 2. Database Schema Changes

```bash
# 1. Update schema version in api/n8n_deploy_db.py
SCHEMA_VERSION = 2

# 2. Add migration logic in _initialize_database()
def _migrate_to_version_2(self):
    """Migration logic"""
    pass

# 3. Test with existing database
python run_tests.py --specific tests/unit/test_n8n_deploy_db.py
```

### 3. Adding New Dependencies

```bash
# 1. Add to pyproject.toml
dependencies = [
    "new-package>=1.0.0",
]

# 2. Install and test
uv pip install -e ".[dev,test]"
python run_tests.py --unit

# 3. Update type stubs if needed
uv pip install types-new-package
```

## Troubleshooting Development Issues

### Common Issues

**1. Import Errors**
```bash
# Ensure project is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

**2. Type Checking Failures**
```bash
# Clear MyPy cache
rm -rf .mypy_cache/

# Install missing type stubs
pip install types-requests types-click
```

**3. Test Failures**
```bash
# Run tests with debugging
python run_tests.py --unit --quiet

# Run specific failing test
python -m pytest tests/unit/test_specific.py::test_function -v -s
```

**4. Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf .venv/
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

## Next Steps

1. **Read**: [Testing Guide](TESTING.md) for comprehensive testing strategies
2. **Study**: [API Reference](API_REFERENCE.md) for detailed component documentation
3. **Follow**: [Contributing Guide](CONTRIBUTING.md) for code standards and workflow
4. **Reference**: [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues

---

*Happy coding! The development environment is designed to get you productive quickly while maintaining high code quality standards.*