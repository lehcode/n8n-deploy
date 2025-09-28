# n8n-deploy - N8N Workflow Manager

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://gitlab.pirouter.dev:8443/n8n/n8n-deploy)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checking: MyPy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy-lang.org/)

> *"If builders built buildings the way programmers wrote programs, then the first woodpecker that came along would destroy civilization."* - Arthur Bloch's Law

**Essential tool for remote n8n deployments** - manage workflows from your local machine without slow export/import through web UI. Database-first workflow management with plain text API keys and flexible directory configuration.

## Overview

n8n-deploy is a Python CLI tool that provides database-first workflow management for n8n automation platform. It excels in scenarios where n8n runs on remote servers and web UI access is limited or slow.

**Key Use Cases:**

- **Remote Server Management**: Deploy workflows to headless n8n servers via SSH
- **Local Development Workflow**: Edit workflows locally, deploy remotely
- **Backup and Restore**: Create versioned backups with integrity verification
- **Team Collaboration**: Share workflow metadata through SQLite database

## Features

### Database-First Architecture

- **SQLite Metadata Store**: Complete workflow tracking with simple table schema
- **File System Integration**: Flexible base folder and flow folder configuration
- **Backup System**: `tar.gz` archives with SHA256 integrity verification
- **Full-Text Search**: Built-in FTS5 search across workflow content

### CLI Management

- **Rich Interface**: Emoji-enabled tables with `--no-emoji` for script compatibility
- **Global Access**: Install once, use from anywhere with shell aliases
- **Comprehensive Commands**: 13 main commands covering all workflow operations
- **API Key Storage**: Plain text keys for simplicity (local-only storage)

### Configuration Flexibility

- **Dual Directory System**: Separate app data (database, backups) and workflow files
- **Environment Variables**: N8N_FLOW_DIR environment variable to specify workflow files location
- **CLI Options**: `--app-dir` and `--flow-dir` for runtime configuration
- **Legacy Compatibility**: Seamless migration from older configurations

## Quick Start

### 1. Installation

```bash
# Option 1: Direct installation (recommended for production)
pip install n8n-deploy

# Option 2: Development installation from source
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
pip install -e .

# Option 3: Using uv (faster dependency resolution)
uv venv .venv && source .venv/bin/activate
uv pip install -e .
```

### 2. Global Shell Integration (Optional but Recommended)

```bash
# Create global aliases for convenient access
./setup.sh

# Now use from anywhere:
n8n-deploy list         # List all workflows
n8n-deploy init        # Initialize database
```

### 3. Basic Configuration

```bash
# Initialize database (creates n8n-deploy.db in current directory)
n8n-deploy db init

# Add API key for n8n server
n8n-deploy apikey add n8n_main --key YOUR_N8N_API_KEY

# Set workflow files location (optional)
export N8N_FLOW_DIR=/path/to/your/workflow/files
```

### 4. Workflow Management

```bash
# List all workflows
n8n-deploy list

# Add workflow to management
n8n-deploy add "workflow-id" "My Workflow" "workflows/my-workflow.json"

# Pull from n8n server
n8n-deploy pull workflow-id

# Push to n8n server
n8n-deploy push workflow-id

# Create backup
n8n-deploy backup-workflows

# Search workflows
n8n-deploy search "email"
```

## Directory Structure

n8n-deploy uses a dual-directory system for maximum flexibility:

```
# App Base Directory (--app-dir or current directory)
/app/base/
├── n8n-deploy.db           # SQLite metadata database
└── backups/                # Workflow backup archives
    └── backup_20240924_123456.tar.gz

# Flow Directory (N8N_FLOW_DIR or --flow-dir or same as base)
/flow/directory/
└── workflows/              # Your workflow JSON files
    ├── main-workflow.json
    └── subflow.json
```

## Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list` | Show all workflows with status | `n8n-deploy list --format=table` |
| `add` | Add workflow to management | `n8n-deploy add ID "Name" "file.json"` |
| `pull` | Download from n8n server | `n8n-deploy pull workflow-id` |
| `push` | Upload to n8n server | `n8n-deploy push workflow-id` |
| `search` | Find workflows by content | `n8n-deploy search "webhook"` |
| `backup-workflows` | Create tar.gz backup | `n8n-deploy backup-workflows` |
| `restore-workflows` | Restore from backup | `n8n-deploy restore-workflows backup.tar.gz` |
| `apikey add` | Store API key | `n8n-deploy apikey add server1 --key KEY` |
| `db status` | Database statistics | `n8n-deploy db status` |

### Command Groups

**Workflow Management:**
- `add`, `remove`, `list`, `search`, `stats`, `sync`

**n8n Integration:**
- `pull`, `push` (requires API key configuration)

**Backup Operations:**
- `backup-workflows`, `restore-workflows`, `verify-backup`, `list-backups`

**Database Management:**
- `db init`, `db status`, `db backup`, `db vacuum`, `db compact`

**API Key Management:**
- `apikey add`, `apikey list`, `apikey get`, `apikey delete`, `apikey test`

## Database Schema

n8n-deploy uses a 6-table SQLite schema for comprehensive workflow management:

### Core Tables

1. **workflows** - Main workflow metadata
   - `id` (TEXT PRIMARY KEY), `name`, `type`, `description`
   - `file_path`, `node_count`, `status`, `tags`
   - `created_at`, `updated_at`, `last_synced`, `n8n_version_id`

2. **api_keys** - Plain text API key storage
   - `id`, `name`, `api_key`, `created_at`, `last_used`
   - `expires_at`, `is_active`, `description`

3. **configurations** - Workflow configuration snapshots
   - `workflow_id`, `config_type`, `config_data`
   - `created_at`, `is_active`

### Schema Tables (Future Features)
4. **versions** - Version tracking preparation
5. **dependencies** - Workflow dependency mapping
6. **schema_info** - Database versioning

### Full-Text Search
- **workflows_fts** - FTS5 virtual table for content search
- Automatic triggers maintain search index consistency

## Configuration Options

### Environment Variables

```bash
# Workflow files directory (user's JSON files)
N8N_FLOW_DIR=/path/to/workflow/files

# Testing mode (prevents default workflow initialization)
N8N_DEPLOY_TESTING=1

# Future n8n server configuration
N8N_API_URL=https://n8n.example.com
N8N_API_KEY=default_api_key
```

### CLI Options

```bash
# Directory for app data (database, backups) - defaults to current directory
--app-dir /custom/app/location

# Directory for workflow files - overrides N8N_FLOW_DIR
--flow-dir /custom/workflow/location

# Disable emoji output for script parsing
--no-emoji

# Show version information
--version
```

## Python API Usage

n8n-deploy can be used as a Python library:

```python
from api.config import get_config
from api.manager import WorkflowManager
from api.n8n_deploy_db import n8n_deploy_DB

# Initialize with custom configuration
config = get_config(
    base_folder="/app/data",
    flow_folder="/workflow/files"
)

# Create manager instance
manager = WorkflowManager(config=config)

# List workflows
workflows = manager.list_workflows()

# Add workflow
manager.add_workflow("wf-123", "My Workflow", "workflows/my.json")

# Direct database access
db = n8n_deploy_DB(config=config)
workflow = db.get_workflow("wf-123")
```

## Development

### Environment Setup

```bash
# Using uv (recommended - faster dependency resolution)
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Traditional pip
python -m venv .venv && source .venv/bin/activate
pip install -e .[test,dev]
```

### Testing

```bash
# Comprehensive test runner with verbose output
python run_tests.py --unit                    # Unit tests only
python run_tests.py --integration             # Integration tests only
python run_tests.py --unit --coverage         # With coverage report
python run_tests.py --quality                 # Code quality checks
python run_tests.py --report                  # Full test report
python run_tests.py --specific tests/unit/test_models.py  # Specific tests

# Direct pytest usage
pytest tests/unit/ -v                         # Verbose unit tests
pytest tests/integration/ -v                  # Verbose integration tests
```

### Code Quality

```bash
# Code formatting
black api/

# Type checking (zero errors in strict mode)
mypy api/ --strict

# Install type stubs for external dependencies
pip install types-requests types-click
```

### Building Packages

```bash
# Build wheel and source distribution
python -m build

# Install built package
pip install dist/*.whl

# Verify installation
n8n-deploy --version
```

## GitLab CI/CD Pipeline

The project uses an efficient merge request pipeline with comprehensive validation:

### Pipeline Stages

**Quality Stage:**
- `quality:mypy` - Strict type checking
- `quality:black` - Code formatting validation
- `quality:coverage` - Comprehensive test coverage report

**Security Stage:**
- `secret_detection` - Secret scanning
- `sast` - Static Application Security Testing

**Test Stage:**
- `test:unit` - Unit tests with coverage
- `test:integration` - Integration tests

**Build Matrix Stage:**
- `build:python-matrix` - Multi-version testing (Python 3.9-3.11)
- `build:validation` - Package build validation

**Build Stage:**
- `build:production` - Final production validation

### Developer Workflow

```bash
# Feature development - no CI triggered
git push origin feature-branch

# Create merge request - full pipeline runs
# All quality, security, and test gates must pass

# Post-merge to master - deployment builds
# Automatic package creation and validation
```

## Advanced Usage

### Backup Strategy

```bash
# Create workflow backup with metadata
n8n-deploy backup-workflows --backup-dir /backups

# List available backups with integrity status
n8n-deploy list-backups

# Verify backup integrity
n8n-deploy verify-backup backup_20240924_123456.tar.gz

# Restore from backup with confirmation
n8n-deploy restore-workflows backup.tar.gz --force
```

### Multi-Environment Management

```bash
# Development environment
n8n-deploy --app-dir ~/dev/n8n-deploy list

# Production environment
n8n-deploy --app-dir /opt/n8n-deploy --flow-dir /data/workflows list

# Staging with environment variable
export N8N_FLOW_DIR=/staging/workflows
n8n-deploy list
```

### API Key Management

```bash
# Add API key with expiration
n8n-deploy apikey add prod_server --expires-days 90 --description "Production server key"

# List all keys with status
n8n-deploy apikey list

# Test key connectivity
n8n-deploy apikey test prod_server

# Deactivate expired key
n8n-deploy apikey delete old_key --confirm
```

### Database Management

```bash
# View database statistics
n8n-deploy db status --format=json

# Create database backup
n8n-deploy db backup /backups/db_backup.db

# Optimize database performance
n8n-deploy db vacuum
n8n-deploy db compact
```

## Troubleshooting

### Common Issues

**Database Initialization Fails:**
```bash
# Check directory permissions
ls -la $(pwd)
# Initialize with specific app directory
n8n-deploy --app-dir /writable/path db init
```

**Workflow Files Not Found:**
```bash
# Verify flow directory configuration
echo $N8N_FLOW_DIR
# Use explicit flow directory
n8n-deploy --flow-dir /actual/workflow/path list
```

**API Key Connection Issues:**
```bash
# Test stored API key
n8n-deploy apikey test your_key_name
# Verify key format and server accessibility
```

### Performance Optimization

```bash
# Regular database maintenance
n8n-deploy db vacuum      # Reclaim space
n8n-deploy db compact     # Optimize structure

# FTS index rebuild (if search is slow)
# Handled automatically by triggers
```

## Migration Guide

### From Version 1.x to 2.x

n8n-deploy 2.0 introduces configuration system improvements:

```bash
# Old: Fixed project-relative paths
# New: Flexible base and flow directories

# Update workflow (no breaking changes to CLI interface)
# Database schema automatically migrates
# API keys remain in plain text format
```

### Environment Variable Changes

```bash
# New in 2.0: Flow directory configuration
export N8N_FLOW_DIR=/your/workflow/files

# Testing mode (existing)
export N8N_DEPLOY_TESTING=1
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Setup development environment
uv venv .venv && source .venv/bin/activate
uv pip install -e .[test,dev]

# Install pre-commit hooks
pre-commit install

# Run full test suite
python run_tests.py --report
```

### Testing Guidelines

- Use `N8N_DEPLOY_TESTING=1` environment variable in tests
- Design tests for both user and CI environments
- Use `/dev/null/invalid_path` patterns for reliable failure testing
- Run tests with `--quiet` flag for automated environments

### Code Standards

- **Black formatting**: 88 character line length
- **MyPy type checking**: Strict mode, zero errors
- **Pydantic models**: Comprehensive data validation
- **Click CLI**: Rich interface with --no-emoji compatibility

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/lehcode/n8n-deploy
- **Issues**: https://github.com/lehcode/n8n-deploy/issues
- **Documentation**: [ARCHITECTURE.md](ARCHITECTURE.md), [CLI-REFERENCE.md](CLI-REFERENCE.md)
- **GitLab CI**: https://gitlab.pirouter.dev:8443/n8n/n8n-deploy

---

*n8n-deploy: Making remote workflow management simple and reliable.*