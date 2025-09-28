# n8n-deploy Installation Guide

> *"The most likely way for the world to be destroyed, most experts agree, is by accident. That's where we come in; we're computer professionals. We cause accidents."* - Nathaniel Borenstein's Computer Laws

This guide provides comprehensive installation instructions for n8n-deploy across different environments and use cases.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Quick Installation](#quick-installation)
- [Development Installation](#development-installation)
- [Production Installation](#production-installation)
- [Container Installation](#container-installation)
- [Global Shell Integration](#global-shell-integration)
- [Environment Configuration](#environment-configuration)
- [Verification](#verification)
- [Troubleshooting Installation Issues](#troubleshooting-installation-issues)
- [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or later
- **Operating System**: Linux, macOS, Windows
- **Memory**: 64 MB RAM
- **Storage**: 10 MB free space (plus space for workflows and database)
- **Network**: Internet access for installation (optional for operation)

### Recommended Requirements

- **Python**: 3.9 or later for optimal performance
- **Memory**: 256 MB RAM for larger workflow collections
- **Storage**: 100 MB+ for comprehensive usage
- **Environment**: Unix-like system for full shell integration

### Supported Python Versions

n8n-deploy is tested on:

- **Python 3.8** - Minimum supported version
- **Python 3.9** - Recommended version (CI default)
- **Python 3.10** - Full compatibility
- **Python 3.11** - Full compatibility
- **Python 3.12** - Latest supported version

## Installation Methods

n8n-deploy offers multiple installation approaches for different use cases:

| Method | Use Case | Complexity | Maintenance |
|--------|----------|------------|-------------|
| **PyPI Install** | Production, end users | Low | pip updates |
| **Development Install** | Contributors, customization | Medium | Git pulls |
| **Source Install** | Latest features, testing | Medium | Manual updates |
| **Container** | Isolated environments | Medium | Image updates |

## Quick Installation

### Method 1: PyPI Installation (Recommended)

Install the latest stable release from PyPI:

```bash
# Install n8n-deploy
pip install n8n-deploy

# Verify installation
n8n-deploy --version

# Initialize database
n8n-deploy db init

# Optional: Create global aliases
# (Download and run setup.sh from repository)
```

**Advantages:**
- ✅ Stable, tested releases
- ✅ Simple dependency management
- ✅ Automatic console script installation
- ✅ Standard Python package management

### Method 2: Direct Repository Installation

Install directly from the GitHub repository:

```bash
# Install latest from repository
pip install git+https://github.com/lehcode/n8n-deploy.git

# Or install specific version/branch
pip install git+https://github.com/lehcode/n8n-deploy.git@v2.0.0

# Verify installation
n8n-deploy --version
```

## Development Installation

For contributors and developers who need to modify the code:

### Using uv (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Create virtual environment with uv (faster)
uv venv .venv
source .venv/bin/activate

# Install in development mode with all dependencies
uv pip install -e .[test,dev]

# Install type stubs for external packages
uv pip install types-requests types-click

# Verify installation
n8n-deploy --version

# Run tests to ensure everything works
python run_tests.py --unit
```

### Using Traditional pip

```bash
# Clone repository
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .[test,dev]

# Install additional type stubs
pip install types-requests types-click

# Verify installation
n8n-deploy --version
```

### Development Dependencies

The `[test,dev]` extra includes:

**Testing Dependencies:**
- `pytest` - Test framework
- `pytest-cov` - Coverage testing
- `pytest-mock` - Mock object support
- `assertpy` - Fluent assertions

**Development Dependencies:**
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks

## Production Installation

### System-Wide Installation

For production servers or system-wide access:

```bash
# Install system-wide (requires admin privileges)
sudo pip install n8n-deploy

# Or using system package manager (if available)
# On Ubuntu/Debian (when packaged):
# sudo apt install n8n-deploy

# Create system service directory
sudo mkdir -p /opt/n8n-deploy
sudo chown $USER:$USER /opt/n8n-deploy

# Initialize production database
n8n-deploy --app-dir /opt/n8n-deploy db init
```

### Virtual Environment (Recommended)

For isolated production deployments:

```bash
# Create production environment
python -m venv /opt/n8n-deploy/venv
source /opt/n8n-deploy/venv/bin/activate

# Install n8n-deploy
pip install n8n-deploy

# Create startup script
cat << 'EOF' > /usr/local/bin/n8n-deploy
#!/bin/bash
source /opt/n8n-deploy/venv/bin/activate
exec python -m api.cli "$@"
EOF

chmod +x /usr/local/bin/n8n-deploy

# Test production installation
n8n-deploy --version
```

### Production Configuration

```bash
# Set up production directories
export N8N_FLOW_DIR=/data/workflows
mkdir -p /data/workflows/workflows

# Initialize production database
n8n-deploy --app-dir /opt/n8n-deploy db init

# Add production API keys
n8n-deploy --app-dir /opt/n8n-deploy apikey add production \
  --description "Production n8n server" \
  --expires-days 365
```

## Container Installation

### Docker Installation

Create a Dockerfile for containerized usage:

```dockerfile
FROM python:3.9-slim

# Install n8n-deploy
RUN pip install n8n-deploy

# Create app directory
WORKDIR /app

# Create volumes for persistence
VOLUME ["/app/data", "/app/workflows"]

# Set default environment
ENV N8N_FLOW_DIR=/app/workflows

# Default command
CMD ["n8n-deploy", "--app-dir", "/app/data", "--help"]
```

Build and run:

```bash
# Build container
docker build -t n8n-deploy .

# Run with persistent storage
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/workflows:/app/workflows \
  n8n-deploy n8n-deploy --app-dir /app/data list
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  n8n-deploy:
    build: .
    volumes:
      - ./data:/app/data
      - ./workflows:/app/workflows
    environment:
      - N8N_FLOW_DIR=/app/workflows
    command: tail -f /dev/null  # Keep container running
```

Usage:

```bash
# Start container
docker-compose up -d

# Run commands
docker-compose exec n8n-deploy n8n-deploy --app-dir /app/data db init
docker-compose exec n8n-deploy n8n-deploy --app-dir /app/data list
```

## Global Shell Integration

The global shell integration creates convenient aliases for system-wide access:

### Automatic Setup (Recommended)

```bash
# Clone repository temporarily
git clone https://github.com/lehcode/n8n-deploy.git /tmp/n8n-deploy

# Run setup script
/tmp/n8n-deploy/setup.sh

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc

# Test global aliases
n8n-deploy-list
n8n-deploy-init
```

### Manual Setup

If you prefer manual configuration:

```bash
# Add to your ~/.bashrc or ~/.zshrc
cat >> ~/.bashrc << 'EOF'
# n8n-deploy global aliases
alias n8n-deploy-init='n8n-deploy db init'
alias n8n-deploy-list='n8n-deploy list'
alias n8n-deploy-add='n8n-deploy add'
alias n8n-deploy-remove='n8n-deploy remove'
alias n8n-deploy-pull='n8n-deploy pull'
alias n8n-deploy-push='n8n-deploy push'
alias n8n-deploy-search='n8n-deploy search'
alias n8n-deploy-backup='n8n-deploy backup-workflows'
alias n8n-deploy-restore='n8n-deploy restore-workflows'
alias n8n-deploy-status='n8n-deploy db status'
alias n8n-deploy-apikey='n8n-deploy apikey'
EOF

# Reload configuration
source ~/.bashrc
```

### Global Aliases Reference

After setup, these aliases are available from any directory:

| Alias | Equivalent Command |
|-------|-------------------|
| `n8n-deploy-init` | `n8n-deploy db init` |
| `n8n-deploy-list` | `n8n-deploy list` |
| `n8n-deploy-add` | `n8n-deploy add` |
| `n8n-deploy-remove` | `n8n-deploy remove` |
| `n8n-deploy-pull` | `n8n-deploy pull` |
| `n8n-deploy-push` | `n8n-deploy push` |
| `n8n-deploy-search` | `n8n-deploy search` |
| `n8n-deploy-backup` | `n8n-deploy backup-workflows` |
| `n8n-deploy-restore` | `n8n-deploy restore-workflows` |
| `n8n-deploy-status` | `n8n-deploy db status` |
| `n8n-deploy-apikey` | `n8n-deploy apikey` |

## Environment Configuration

### Directory Structure Setup

Configure directories for optimal organization:

```bash
# Option 1: Single directory (simple)
mkdir ~/n8n-deploy
cd ~/n8n-deploy
n8n-deploy db init
# Database and workflows in same location

# Option 2: Separate directories (recommended)
mkdir -p ~/n8n-deploy-app     # App data (database, backups)
mkdir -p ~/workflows          # Workflow files
export N8N_FLOW_DIR=~/workflows
n8n-deploy --app-dir ~/n8n-deploy-app db init

# Option 3: Production layout
sudo mkdir -p /opt/n8n-deploy /data/workflows
export N8N_FLOW_DIR=/data/workflows
n8n-deploy --app-dir /opt/n8n-deploy db init
```

### Environment Variables

Set up persistent environment configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
cat >> ~/.bashrc << 'EOF'
# n8n-deploy configuration
export N8N_FLOW_DIR=$HOME/workflows
export N8N_DEPLOY_APP_DIR=$HOME/n8n-deploy-app

# Optional: Default n8n server (future feature)
export N8N_API_URL=https://n8n.example.com
EOF

# Reload configuration
source ~/.bashrc
```

### Configuration Verification

Verify your configuration:

```bash
# Check environment variables
echo "Flow directory: $N8N_FLOW_DIR"
echo "App directory: $N8N_DEPLOY_APP_DIR"

# Test directory access
ls -la "$N8N_FLOW_DIR"
ls -la "$N8N_DEPLOY_APP_DIR"

# Test n8n-deploy configuration
n8n-deploy --app-dir "$N8N_DEPLOY_APP_DIR" \
           --flow-dir "$N8N_FLOW_DIR" \
           db status
```

## Verification

### Installation Verification

Verify your installation with these tests:

```bash
# 1. Check version and basic functionality
n8n-deploy --version
n8n-deploy --help

# 2. Test database initialization
n8n-deploy db init
n8n-deploy db status

# 3. Test command groups
n8n-deploy db --help
n8n-deploy apikey --help

# 4. Test workflow operations
n8n-deploy list
n8n-deploy add test-wf "Test Workflow" "test.json" || true  # May fail, that's OK

# 5. Test backup operations
n8n-deploy list-backups
```

### Python API Verification

Test the Python API if using as a library:

```python
# Create test script: test_installation.py
import sys
try:
    from api.config import get_config
    from api.n8n_deploy_db import n8n_deploy_DB
    from api.manager import WorkflowManager
    from api.models import Workflow

    print("✅ All imports successful")

    # Test configuration
    config = get_config()
    print(f"✅ Configuration created: {config.database_path}")

    # Test database
    db = n8n_deploy_DB(config=config)
    stats = db.get_database_stats()
    print(f"✅ Database accessible: {stats.database_path}")

    print("✅ Installation verification complete")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
```

Run the test:

```bash
python test_installation.py
```

### Integration Test

Create a complete workflow test:

```bash
#!/bin/bash
set -e

echo "🧪 Running integration test..."

# Initialize clean environment
TEST_DIR=/tmp/n8n-deploy-test-$$
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize database
n8n-deploy db init
echo "✅ Database initialization"

# Add test API key
echo "test-api-key-123" | n8n-deploy apikey add test_server --description "Test server"
echo "✅ API key management"

# Test workflow operations
n8n-deploy list
echo "✅ Workflow listing"

# Test backup operations
n8n-deploy list-backups
echo "✅ Backup operations"

# Clean up
cd /
rm -rf "$TEST_DIR"
echo "✅ Integration test complete"
```

## Troubleshooting Installation Issues

### Common Installation Problems

**1. Python Version Issues**

```bash
# Check Python version
python --version

# If using old Python, try python3
python3 --version

# Install with specific Python version
python3.9 -m pip install n8n-deploy
```

**2. pip Installation Fails**

```bash
# Update pip first
python -m pip install --upgrade pip

# Install with user flag if permissions issue
pip install --user n8n-deploy

# Clear pip cache if corrupted
pip cache purge
pip install n8n-deploy
```

**3. Virtual Environment Issues**

```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install n8n-deploy
```

**4. Permission Errors**

```bash
# Use --user flag for user-local installation
pip install --user n8n-deploy

# Or fix pip permissions
sudo chown -R $USER ~/.local/lib/python*/site-packages/
```

**5. Module Not Found Errors**

```bash
# Check installation location
pip show n8n-deploy

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall in development mode
pip install -e .
```

### Platform-Specific Issues

**Windows:**

```powershell
# Use Python Launcher
py -m pip install n8n-deploy

# Check PATH for Scripts directory
echo $env:PATH

# Activate virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Run with python -m if PATH issues
python -m api.cli --version
```

**macOS:**

```bash
# Install with Homebrew Python
brew install python
/usr/local/bin/python3 -m pip install n8n-deploy

# Fix PATH if needed
export PATH="/usr/local/bin:$PATH"

# Use python3 explicitly
python3 -m pip install n8n-deploy
```

**Linux:**

```bash
# Install Python development headers if compilation fails
sudo apt-get install python3-dev python3-venv

# Or on CentOS/RHEL
sudo yum install python3-devel python3-venv

# Use system package manager if available
sudo apt-get install python3-pip
pip3 install n8n-deploy
```

### Development Installation Issues

**1. Type Checking Errors**

```bash
# Install missing type stubs
pip install types-requests types-click types-dateutil

# Clear mypy cache
rm -rf .mypy_cache/
mypy api/ --install-types
```

**2. Test Dependencies**

```bash
# Install test dependencies explicitly
pip install pytest pytest-cov pytest-mock assertpy

# Or install all extras
pip install -e .[test,dev]
```

**3. Pre-commit Issues**

```bash
# Install pre-commit hooks
pre-commit install

# Update hooks if they fail
pre-commit autoupdate

# Run manually to test
pre-commit run --all-files
```

## Uninstallation

### Complete Uninstallation

```bash
# 1. Remove Python package
pip uninstall n8n-deploy

# 2. Remove global aliases (if installed)
# Edit ~/.bashrc or ~/.zshrc to remove n8n-deploy aliases

# 3. Remove data directories (if desired)
rm -rf ~/n8n-deploy-app  # or your app directory
# Note: Workflow files in N8N_FLOW_DIR are kept

# 4. Remove virtual environment (if used)
rm -rf .venv
```

### Selective Cleanup

Keep data but remove installation:

```bash
# Remove only the Python package
pip uninstall n8n-deploy

# Keep database and workflow files for later reinstallation
# They will work with new installation
```

### Data Backup Before Uninstall

```bash
# Create final backup before uninstall
n8n-deploy backup-workflows --backup-dir ~/n8n-deploy-final-backup
n8n-deploy db backup ~/n8n-deploy-final-backup/database-backup.db

# Document your configuration
n8n-deploy db status > ~/n8n-deploy-final-backup/config-info.txt
echo "N8N_FLOW_DIR=$N8N_FLOW_DIR" >> ~/n8n-deploy-final-backup/config-info.txt
```

---

This installation guide covers all common scenarios and troubleshooting steps. For usage instructions, see [CLI-REFERENCE.md](CLI-REFERENCE.md). For configuration details, see [CONFIGURATION.md](CONFIGURATION.md).