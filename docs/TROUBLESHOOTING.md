# Troubleshooting Guide

## Overview

This troubleshooting guide helps developers and users resolve common issues encountered while developing, testing, or using n8n-deploy. The guide is organized by symptom categories with step-by-step diagnostic and resolution procedures.

## Quick Diagnostic Commands

### System Health Check

```bash
# Environment verification
python --version                    # Python 3.8+ required
which python                       # Check Python location
echo $PATH                         # Verify PATH includes Python

# Project status
./n8n-deploy --version             # Version check
./n8n-deploy --help                # Basic functionality

# Environment variables
env | grep N8N_DEPLOY              # Configuration vars
echo "App dir: $N8N_DEPLOY_APP_DIR"
echo "Flow dir: $N8N_FLOW_DIR"
echo "Server: $N8N_SERVER_URL"

# Dependencies
pip list | grep -E "(click|requests|pydantic|rich)"
python -c "import api; print('API module imports successfully')"
```

### Test Environment Check

```bash
# Test runner status
python run_tests.py --unit --no-deps-check

# Database connectivity
python -c "from api.db import DatabaseManager; print('DB imports OK')"

# File permissions
ls -la ~/.config/                  # Check config directory access
touch /tmp/n8n-test && rm /tmp/n8n-test  # Write permission test
```

## Installation and Setup Issues

### 1. Python Version Conflicts

**Symptoms**:
- "Python 3.8+ required" error messages
- Import errors for modern Python features
- Type hint syntax errors

**Diagnosis**:
```bash
# Check Python version
python --version
python3 --version

# Check virtual environment Python
which python
.venv/bin/python --version

# Check installed Python versions
ls /usr/bin/python*
pyenv versions  # If using pyenv
```

**Solutions**:

**Option A: System Python**:
```bash
# Install Python 3.9+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev

# Create virtual environment with specific version
python3.9 -m venv .venv
source .venv/bin/activate
python --version  # Should show 3.9+
```

**Option B: pyenv (Recommended for Development)**:
```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python 3.9
pyenv install 3.9.18
pyenv local 3.9.18

# Verify and recreate environment
python --version
rm -rf .venv/
python -m venv .venv
source .venv/bin/activate
```

### 2. Virtual Environment Issues

**Symptoms**:
- "Module not found" errors for installed packages
- Wrong Python interpreter being used
- Package installation not taking effect

**Diagnosis**:
```bash
# Check if virtual environment is active
echo $VIRTUAL_ENV  # Should show .venv path
which python       # Should show .venv/bin/python
which pip          # Should show .venv/bin/pip

# Check installed packages
pip list
pip show n8n-deploy
```

**Solutions**:

**Recreate Virtual Environment**:
```bash
# Deactivate and remove
deactivate
rm -rf .venv/

# Create fresh environment
python -m venv .venv
source .venv/bin/activate

# Verify and install
which python
pip install --upgrade pip
pip install -e ".[dev,test]"
```

**Environment Activation Issues**:
```bash
# Fish shell
source .venv/bin/activate.fish

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# Verify activation
echo $VIRTUAL_ENV  # Should not be empty
```

### 3. Dependency Installation Failures

**Symptoms**:
- "Failed to build package" errors
- Compilation errors during pip install
- Network timeouts during installation

**Diagnosis**:
```bash
# Check pip version
pip --version

# Check network connectivity
ping pypi.org
curl -I https://pypi.org/simple/

# Check available disk space
df -h .
```

**Solutions**:

**Basic Dependency Issues**:
```bash
# Upgrade pip and tools
pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -e ".[dev,test]" -v

# Clear pip cache
pip cache purge
```

**Compilation Issues (Linux)**:
```bash
# Install build essentials
sudo apt update
sudo apt install build-essential python3-dev

# For CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

**Network Issues**:
```bash
# Use different index
pip install -e ".[dev,test]" -i https://pypi.org/simple/

# Use company proxy (if applicable)
pip install -e ".[dev,test]" --proxy http://proxy.company.com:8080

# Offline installation (with downloaded packages)
pip download -r requirements.txt -d packages/
pip install --find-links packages/ -e ".[dev,test]"
```

## Configuration and Path Issues

### 1. Database Path Problems

**Symptoms**:
- "Database file not found" errors
- "Permission denied" when accessing database
- Database operations fail silently

**Diagnosis**:
```bash
# Check current configuration
./n8n-deploy db status

# Check environment variables
echo $N8N_DEPLOY_APP_DIR

# Check file permissions
ls -la $N8N_DEPLOY_APP_DIR/
ls -la $N8N_DEPLOY_APP_DIR/n8n-deploy.db
```

**Solutions**:

**Missing App Directory**:
```bash
# Set required environment variable
export N8N_DEPLOY_APP_DIR="$HOME/.config/n8n-deploy"
mkdir -p "$N8N_DEPLOY_APP_DIR"

# Or use CLI option
./n8n-deploy --app-dir "$HOME/.config/n8n-deploy" db init
```

**Permission Issues**:
```bash
# Check directory permissions
ls -ld $N8N_DEPLOY_APP_DIR

# Fix permissions
chmod 755 $N8N_DEPLOY_APP_DIR
chmod 644 $N8N_DEPLOY_APP_DIR/n8n-deploy.db

# Change ownership if needed
sudo chown $USER:$USER $N8N_DEPLOY_APP_DIR -R
```

**Database Corruption**:
```bash
# Backup and reinitialize
cp $N8N_DEPLOY_APP_DIR/n8n-deploy.db $N8N_DEPLOY_APP_DIR/n8n-deploy.db.backup
rm $N8N_DEPLOY_APP_DIR/n8n-deploy.db
./n8n-deploy db init

# Check database integrity
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db "PRAGMA integrity_check;"
```

### 2. Workflow File Path Issues

**Symptoms**:
- "Workflow file not found" when adding workflows
- Relative path resolution errors
- File access permission denied

**Diagnosis**:
```bash
# Check flow directory configuration
echo $N8N_FLOW_DIR
./n8n-deploy list  # Shows current paths in verbose mode

# Check file existence and permissions
ls -la /path/to/workflow/file.json
file /path/to/workflow/file.json  # Check if it's valid JSON
```

**Solutions**:

**Path Configuration**:
```bash
# Set flow directory
export N8N_FLOW_DIR="/path/to/your/workflows"

# Or use CLI option
./n8n-deploy --flow-dir "/path/to/workflows" add workflow.json

# Use absolute paths
./n8n-deploy add /full/path/to/workflow.json
```

**File Permission Issues**:
```bash
# Check file accessibility
test -r /path/to/workflow.json && echo "Readable" || echo "Not readable"

# Fix permissions
chmod 644 /path/to/workflow.json
```

**JSON Validation**:
```bash
# Validate JSON syntax
python -m json.tool < workflow.json

# Check with jq (if available)
jq . workflow.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## Testing and Development Issues

### 1. Test Execution Failures

**Symptoms**:
- Tests fail with import errors
- "Database is locked" errors during testing
- Tests pass individually but fail in batch

**Diagnosis**:
```bash
# Check test environment
echo $N8N_DEPLOY_TESTING
python -c "import pytest; print(f'pytest version: {pytest.__version__}')"

# Run single test for debugging
python -m pytest tests/unit/test_models.py::test_workflow_creation -v -s

# Check test database isolation
python run_tests.py --unit --no-deps-check
```

**Solutions**:

**Environment Setup**:
```bash
# Ensure test environment variable is set
export N8N_DEPLOY_TESTING=1

# Clear test artifacts
rm -rf .pytest_cache/
rm -f .coverage
rm -rf htmlcov/

# Recreate test environment
python run_tests.py --unit --no-deps-check
```

**Database Lock Issues**:
```bash
# Kill any hanging processes
pkill -f "python.*pytest"
pkill -f "n8n-deploy"

# Clear temporary test files
find /tmp -name "*n8n-deploy*" -type f -delete 2>/dev/null || true

# Run tests with fresh environment
python run_tests.py --unit
```

**Dependency Issues**:
```bash
# Install test dependencies
pip install -e ".[test]"

# Install missing test tools
pip install pytest pytest-cov pytest-mock assertpy

# Verify test runner
python run_tests.py --help
```

### 2. Type Checking Failures

**Symptoms**:
- MyPy reports type errors
- "Module has no attribute" errors
- Inconsistent type checking results

**Diagnosis**:
```bash
# Check MyPy installation and version
mypy --version

# Check type stub installation
pip list | grep types-

# Run type checking with verbose output
mypy api/ --verbose
```

**Solutions**:

**Install Type Stubs**:
```bash
# Install external type stubs
pip install types-requests types-click types-tabulate

# Clear MyPy cache
rm -rf .mypy_cache/

# Run type checking
mypy api/ --strict
```

**Configuration Issues**:
```bash
# Verify MyPy configuration
cat pyproject.toml | grep -A 20 "\[tool.mypy\]"

# Test with minimal configuration
mypy api/models.py --strict

# Check for conflicting configurations
find . -name "mypy.ini" -o -name ".mypy.ini" -o -name "setup.cfg"
```

### 3. Code Formatting Issues

**Symptoms**:
- Black formatting fails
- Pre-commit hooks fail
- Inconsistent formatting across files

**Diagnosis**:
```bash
# Check Black installation
black --version

# Check configuration
cat pyproject.toml | grep -A 10 "\[tool.black\]"

# Test formatting on single file
black --check api/models.py
```

**Solutions**:

**Format Code**:
```bash
# Auto-format all code
black api/

# Check what would be formatted
black --check --diff api/

# Format specific files
black api/cli.py api/manager.py
```

**Pre-commit Issues**:
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify -m "message"
```

## Runtime and CLI Issues

### 1. CLI Command Failures

**Symptoms**:
- Commands hang or freeze
- "Click abort" errors without clear message
- Unexpected command behavior

**Diagnosis**:
```bash
# Test basic CLI functionality
./n8n-deploy --help
./n8n-deploy --version

# Run with debug environment
DEBUG=1 ./n8n-deploy db status

# Check for hung processes
ps aux | grep n8n-deploy
```

**Solutions**:

**Basic CLI Issues**:
```bash
# Ensure wrapper script is executable
chmod +x ./n8n-deploy

# Test direct Python execution
python api/cli.py --help

# Check entry point installation
pip show n8n-deploy
which n8n-deploy
```

**Configuration Issues**:
```bash
# Test with explicit configuration
./n8n-deploy --app-dir /tmp/test db init

# Clear configuration conflicts
unset N8N_DEPLOY_APP_DIR N8N_FLOW_DIR N8N_SERVER_URL
./n8n-deploy --app-dir /tmp/test db status
```

**Hanging Commands**:
```bash
# Kill hung processes
pkill -f n8n-deploy

# Check for file locks
lsof | grep n8n-deploy.db

# Test with timeout
timeout 30 ./n8n-deploy list
```

### 2. Database Connection Issues

**Symptoms**:
- "Database is locked" errors
- Connection timeout errors
- Inconsistent database state

**Diagnosis**:
```bash
# Check database file
ls -la $N8N_DEPLOY_APP_DIR/n8n-deploy.db
file $N8N_DEPLOY_APP_DIR/n8n-deploy.db

# Check for locks
lsof $N8N_DEPLOY_APP_DIR/n8n-deploy.db

# Test direct SQLite access
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db ".tables"
```

**Solutions**:

**Lock Issues**:
```bash
# Kill processes holding locks
lsof $N8N_DEPLOY_APP_DIR/n8n-deploy.db | awk 'NR>1 {print $2}' | xargs kill

# Remove lock files (if safe)
rm -f $N8N_DEPLOY_APP_DIR/n8n-deploy.db-wal
rm -f $N8N_DEPLOY_APP_DIR/n8n-deploy.db-shm

# Test database accessibility
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db "SELECT COUNT(*) FROM workflows;"
```

**Corruption Recovery**:
```bash
# Backup current database
cp $N8N_DEPLOY_APP_DIR/n8n-deploy.db $N8N_DEPLOY_APP_DIR/backup-$(date +%Y%m%d).db

# Check and repair
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db "PRAGMA integrity_check;"
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db "VACUUM;"

# Restore from backup if needed
./n8n-deploy db backup --output-path /tmp/emergency-backup.tar.gz
```

### 3. n8n Server Integration Issues

**Symptoms**:
- Connection refused to n8n server
- Authentication failures
- SSL/TLS certificate errors

**Diagnosis**:
```bash
# Test server connectivity
curl -I $N8N_SERVER_URL/healthz
ping n8n.example.com

# Check API key
./n8n-deploy apikey list

# Test API authentication
curl -H "Authorization: Bearer your-api-key" $N8N_SERVER_URL/api/v1/workflows
```

**Solutions**:

**Connection Issues**:
```bash
# Verify server URL format
echo $N8N_SERVER_URL  # Should include http:// or https://

# Test with different URL formats
./n8n-deploy --server-url http://localhost:5678 list-server
./n8n-deploy --server-url https://n8n.example.com list-server

# Skip SSL verification for development
./n8n-deploy --skip-ssl-verify list-server
```

**Authentication Issues**:
```bash
# Add valid API key
echo "your-api-key" | ./n8n-deploy apikey add production_key

# Test key validity
./n8n-deploy apikey list --show-keys

# Test with environment variable
export N8N_API_KEY="your-api-key"
./n8n-deploy list-server
```

**Network Configuration**:
```bash
# Check proxy settings
echo $HTTP_PROXY $HTTPS_PROXY

# Test without proxy
unset HTTP_PROXY HTTPS_PROXY
./n8n-deploy list-server

# Configure corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

## Performance and Resource Issues

### 1. Slow Command Execution

**Symptoms**:
- Commands take unusually long to complete
- High CPU or memory usage
- Disk I/O bottlenecks

**Diagnosis**:
```bash
# Monitor resource usage
top -p $(pgrep -f n8n-deploy)
iostat -x 1 5  # Monitor disk I/O

# Profile Python execution
python -m cProfile -o profile.out api/cli.py db status
python -c "import pstats; p=pstats.Stats('profile.out'); p.sort_stats('cumulative').print_stats(10)"

# Check database size
ls -lh $N8N_DEPLOY_APP_DIR/n8n-deploy.db
```

**Solutions**:

**Database Optimization**:
```bash
# Compact database to reclaim space
./n8n-deploy db compact

# Analyze database performance
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db "ANALYZE; PRAGMA optimize;"

# Check for large backup files
du -sh $N8N_DEPLOY_APP_DIR/backups/
```

**System Resource Optimization**:
```bash
# Increase system limits (if needed)
ulimit -n 4096  # File descriptors
ulimit -f unlimited  # File size

# Monitor and clean temporary files
du -sh /tmp/
find /tmp -name "*n8n-deploy*" -mtime +1 -delete
```

### 2. Memory Issues

**Symptoms**:
- "MemoryError" exceptions
- System becomes unresponsive
- Process killed by OOM killer

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Monitor process memory
while true; do ps -o pid,vsz,rss,comm -p $(pgrep -f n8n-deploy); sleep 1; done
```

**Solutions**:

**Large Workflow Handling**:
```bash
# Process workflows in batches
./n8n-deploy list --limit 100

# Use streaming for large operations
./n8n-deploy backup --workflow-id specific_id

# Split large backup files
tar -czf - workflows/ | split -b 100M - backup_part_
```

## CI/CD and Deployment Issues

### 1. GitLab CI Pipeline Failures

**Symptoms**:
- CI jobs fail inconsistently
- Permission errors in CI environment
- Docker build failures

**Diagnosis**:
```bash
# Simulate CI environment locally
docker run --rm -v $(pwd):/app -w /app python:3.9-slim bash -c "
    apt-get update && apt-get install -y git
    pip install -e .[dev,test]
    python run_tests.py --unit
"

# Check CI environment variables
echo $CI $GITLAB_CI $CI_COMMIT_REF_NAME

# Review failed job logs in GitLab UI
```

**Solutions**:

**Docker Environment Issues**:
```bash
# Update Docker base image
# In .gitlab-ci.yml:
image: python:3.9-slim  # Use specific version

# Install system dependencies
before_script:
  - apt-get update && apt-get install -y git build-essential
```

**Permission Issues in CI**:
```bash
# Use CI-safe test paths in tests
# Instead of: /nonexistent/path
# Use: /dev/null/invalid_path

# Ensure CI environment variable is set
export N8N_DEPLOY_TESTING=1
```

### 2. Package Building Issues

**Symptoms**:
- "python -m build" fails
- Missing files in built package
- Version conflicts in distribution

**Diagnosis**:
```bash
# Test local build
python -m build
pip install dist/*.whl

# Check package contents
unzip -l dist/n8n_deploy-*.whl
tar -tzf dist/n8n_deploy-*.tar.gz
```

**Solutions**:

**Build Configuration**:
```bash
# Update build tools
pip install --upgrade build setuptools wheel

# Clean build artifacts
rm -rf build/ dist/ *.egg-info/
python -m build

# Verify package installation
pip install dist/*.whl
n8n-deploy --version
```

**Package Metadata Issues**:
```bash
# Check pyproject.toml syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Validate package metadata
python -m twine check dist/*
```

## Advanced Debugging Techniques

### 1. Python Debugging

**Interactive Debugging**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use pytest debugging
import pytest; pytest.set_trace()

# Rich debug output
from rich import print as rprint
rprint(complex_data_structure)
```

**Logging Configuration**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Performance Profiling**:
```bash
# Profile specific command
python -m cProfile -s cumulative api/cli.py db status

# Memory profiling
pip install memory-profiler
python -m memory_profiler api/cli.py
```

### 2. Database Debugging

**SQLite Analysis**:
```bash
# Connect to database
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db

# Useful SQLite commands
.tables                  # List tables
.schema workflows        # Show table schema
.mode column            # Column display mode
.headers on             # Show column headers

# Query examples
SELECT COUNT(*) FROM workflows;
SELECT name, status FROM workflows WHERE created_at > date('now', '-7 days');
EXPLAIN QUERY PLAN SELECT * FROM workflows WHERE status = 'active';
```

**Transaction Debugging**:
```python
# Debug database transactions
with db.transaction() as conn:
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")  # Explicit transaction
    try:
        # Database operations
        cursor.execute("INSERT INTO workflows ...")
        print(f"Affected rows: {cursor.rowcount}")
    except Exception as e:
        print(f"Transaction failed: {e}")
        raise
```

### 3. Network Debugging

**HTTP Request Debugging**:
```python
# Enable requests debugging
import logging
import urllib3

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

**n8n API Debugging**:
```bash
# Test API endpoints directly
curl -v -H "Authorization: Bearer $API_KEY" $N8N_SERVER_URL/api/v1/workflows

# Check API response format
curl -H "Authorization: Bearer $API_KEY" $N8N_SERVER_URL/api/v1/workflows | jq .

# Test different API versions
curl -H "Authorization: Bearer $API_KEY" $N8N_SERVER_URL/rest/workflows
```

## Emergency Recovery Procedures

### 1. Complete System Reset

**When all else fails**:
```bash
# 1. Backup important data
cp -r $N8N_DEPLOY_APP_DIR $N8N_DEPLOY_APP_DIR.backup.$(date +%Y%m%d)

# 2. Clean installation
rm -rf .venv/ .pytest_cache/ .mypy_cache/ build/ dist/ *.egg-info/
git clean -fdx  # WARNING: Removes all untracked files

# 3. Fresh environment
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev,test]"

# 4. Verify installation
python run_tests.py --unit --no-deps-check
./n8n-deploy --version
```

### 2. Data Recovery

**Database Recovery**:
```bash
# Try SQLite recovery
sqlite3 $N8N_DEPLOY_APP_DIR/n8n-deploy.db ".recover" > recovered.sql
sqlite3 new_database.db < recovered.sql

# Restore from backup
tar -xzf latest_backup.tar.gz -C /tmp/
cp /tmp/workflows/* $N8N_FLOW_DIR/
./n8n-deploy db init  # Recreate database
# Re-add workflows from files
```

**Configuration Recovery**:
```bash
# Reset to defaults
unset N8N_DEPLOY_APP_DIR N8N_FLOW_DIR N8N_SERVER_URL
export N8N_DEPLOY_APP_DIR="$HOME/.config/n8n-deploy"
mkdir -p "$N8N_DEPLOY_APP_DIR"
./n8n-deploy db init
```

## Getting Additional Help

### 1. Documentation Resources

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System design and components
- **Development**: [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Setup and environment
- **Testing**: [TESTING.md](TESTING.md) - Test framework and strategies
- **API**: [API_REFERENCE.md](API_REFERENCE.md) - Detailed API documentation
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow

### 2. Diagnostic Information Collection

**For Bug Reports**:
```bash
# Collect system information
echo "=== System Information ===" > debug_info.txt
python --version >> debug_info.txt
uname -a >> debug_info.txt
echo >> debug_info.txt

echo "=== Environment ===" >> debug_info.txt
env | grep -E "(N8N_|PYTHON_|PATH)" >> debug_info.txt
echo >> debug_info.txt

echo "=== Package Information ===" >> debug_info.txt
pip list | grep -E "(n8n-deploy|click|requests|pydantic)" >> debug_info.txt
echo >> debug_info.txt

echo "=== Error Reproduction ===" >> debug_info.txt
./n8n-deploy --version 2>&1 >> debug_info.txt
python run_tests.py --unit --no-deps-check 2>&1 | tail -20 >> debug_info.txt
```

### 3. Community Resources

- **GitHub Issues**: Report bugs and request features
- **GitLab Issues**: Internal development tracking
- **Documentation PRs**: Contribute to troubleshooting guide improvements

---

*Remember: When troubleshooting, start with the simplest solution first. Most issues can be resolved by recreating the virtual environment and ensuring proper configuration.*
