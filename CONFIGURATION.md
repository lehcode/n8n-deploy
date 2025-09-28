# n8n-deploy Configuration Guide

> *"The more you know, the more you realize you don't know."* - Murphy's Law of Knowledge

This guide provides comprehensive information about configuring n8n-deploy for different environments and use cases.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Directory Configuration](#directory-configuration)
- [Environment Variables](#environment-variables)
- [CLI Options](#cli-options)
- [Configuration Precedence](#configuration-precedence)
- [Use Case Configurations](#use-case-configurations)
- [Advanced Configuration](#advanced-configuration)
- [Configuration Migration](#configuration-migration)
- [Troubleshooting Configuration](#troubleshooting-configuration)

## Configuration Overview

n8n-deploy uses a **flexible configuration system** with multiple layers of configuration sources. The system separates **application data** (database, backups) from **user workflow files** for maximum flexibility.

### Core Configuration Concepts

1. **Base Directory (App Directory)**: Contains n8n-deploy application data
   - SQLite database (`n8n-deploy.db`)
   - Backup archives (`backups/`)
   - Application metadata

2. **Flow Directory**: Contains user workflow files
   - User's workflow JSON files (`workflows/`)
   - Can be separate from base directory
   - Optional, defaults to base directory structure

3. **Configuration Priority**: CLI options override environment variables override defaults

## Directory Configuration

### Directory Structure Options

n8n-deploy supports multiple directory layouts:

#### Option 1: Single Directory (Simple)

```
/app/location/
├── n8n-deploy.db              # Application database
├── backups/                   # Backup archives
└── n8n/                      # Workflow files (legacy)
    └── workflows/
        └── my-workflow.json
```

**Usage:**
```bash
cd /app/location
n8n-deploy db init
n8n-deploy list
```

#### Option 2: Dual Directory (Recommended)

```
# Application Base Directory
/app/base/
├── n8n-deploy.db              # Application database
└── backups/                   # Backup archives
    └── backup_20240924.tar.gz

# Flow Directory (separate)
/workflow/files/
└── workflows/                 # User workflow files
    ├── main-workflow.json
    └── subflow.json
```

**Usage:**
```bash
export N8N_FLOW_DIR=/workflow/files
n8n-deploy --app-dir /app/base list
```

#### Option 3: Production Layout

```
# System Application Directory
/opt/n8n-deploy/
├── n8n-deploy.db
└── backups/

# Data Directory
/data/workflows/
└── workflows/
    └── production-workflows.json

# Configuration
/etc/n8n-deploy/
└── environment
```

### Directory Resolution

The configuration system resolves directories with clear precedence:

```python
# Base Directory Resolution (for app data)
1. CLI --app-dir parameter          # Highest priority
2. Current working directory        # Default fallback

# Flow Directory Resolution (for workflow files)
1. CLI --flow-dir parameter         # Highest priority
2. N8N_FLOW_DIR environment variable
3. Same as base directory           # Legacy compatibility
```

### Directory Validation

n8n-deploy automatically validates directory access:

```python
def validate_paths(self) -> None:
    """Validate that paths are accessible and writable"""
    # Checks performed:
    # 1. Directory exists or can be created
    # 2. Directory is actually a directory (not a file)
    # 3. Directory is writable by current user
    # 4. Parent directory exists for file operations
```

## Environment Variables

### Core Environment Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `N8N_FLOW_DIR` | Directory containing workflow files | `/data/workflows` | Same as app dir |
| `N8N_DEPLOY_TESTING` | Testing mode flag | `1` | Not set |

### Future Environment Variables

| Variable | Description | Example | Status |
|----------|-------------|---------|--------|
| `N8N_API_URL` | Default n8n server URL | `https://n8n.example.com` | Planned |
| `N8N_API_KEY` | Default API key | `n8n_api_key_...` | Planned |
| `N8N_DEPLOY_CONFIG` | Config file path | `/etc/n8n-deploy/config.yaml` | Planned |

### Environment Variable Usage

#### Basic Configuration

```bash
# Set workflow files location
export N8N_FLOW_DIR=/home/user/workflows

# Use n8n-deploy normally
n8n-deploy list
n8n-deploy add "wf-1" "My Workflow" "workflows/test.json"
```

#### Production Environment

```bash
# Production environment setup
export N8N_FLOW_DIR=/data/workflows
export N8N_API_URL=https://n8n.production.com
export N8N_API_KEY=n8n_api_production_key_123

# Add to system environment
cat >> /etc/environment << 'EOF'
N8N_FLOW_DIR=/data/workflows
EOF
```

#### Development Environment

```bash
# Development environment
export N8N_FLOW_DIR=$HOME/dev/workflows
export N8N_DEPLOY_TESTING=1

# Use with different app directory per project
n8n-deploy --app-dir ~/dev/project-a/n8n-deploy list
n8n-deploy --app-dir ~/dev/project-b/n8n-deploy list
```

#### Testing Environment

```bash
# Prevent default workflow initialization during tests
export N8N_DEPLOY_TESTING=1

# Run tests
python -m pytest tests/
python run_tests.py --unit
```

### Making Environment Variables Persistent

#### Bash/Zsh Configuration

```bash
# Add to ~/.bashrc or ~/.zshrc
cat >> ~/.bashrc << 'EOF'
# n8n-deploy configuration
export N8N_FLOW_DIR=$HOME/workflows

# Optional: Set default app directory
export N8N_DEPLOY_APP_DIR=$HOME/n8n-deploy

# Function to use custom app directory
n8n-deploy-custom() {
    n8n-deploy --app-dir "${N8N_DEPLOY_APP_DIR:-$(pwd)}" "$@"
}
EOF

# Reload configuration
source ~/.bashrc
```

#### Systemd Environment

```bash
# For systemd services
sudo mkdir -p /etc/systemd/system/n8n-deploy.service.d

cat > /etc/systemd/system/n8n-deploy.service.d/environment.conf << 'EOF'
[Service]
Environment="N8N_FLOW_DIR=/data/workflows"
Environment="N8N_API_URL=https://n8n.internal.com"
EOF

# Reload systemd
sudo systemctl daemon-reload
```

## CLI Options

### Global CLI Options

All n8n-deploy commands accept these global options:

| Option | Type | Description | Example |
|--------|------|-------------|---------|
| `--app-dir PATH` | Path | Application directory (database, backups) | `--app-dir /opt/n8n-deploy` |
| `--flow-dir PATH` | Path | Flow directory (workflow files) | `--flow-dir /data/workflows` |
| `--no-emoji` | Flag | Disable emoji output | `--no-emoji` |
| `--version` | Flag | Show version and exit | `--version` |
| `--help` | Flag | Show help and exit | `--help` |

### CLI Option Examples

#### Single Command Usage

```bash
# Use custom directories for single command
n8n-deploy --app-dir /custom/app --flow-dir /custom/flows list

# Script-friendly output
n8n-deploy --no-emoji list --format=json

# Check version
n8n-deploy --version
```

#### Persistent CLI Option Usage

```bash
# Create shell function for consistent options
n8n-prod() {
    n8n-deploy --app-dir /opt/n8n-deploy --flow-dir /data/workflows "$@"
}

# Use the function
n8n-prod list
n8n-prod db status
n8n-prod apikey list
```

#### Scripting with CLI Options

```bash
#!/bin/bash
# Production deployment script

APP_DIR="/opt/n8n-deploy"
FLOW_DIR="/data/workflows"
NO_EMOJI="--no-emoji"

# Function for consistent options
n8n_cmd() {
    n8n-deploy --app-dir "$APP_DIR" --flow-dir "$FLOW_DIR" $NO_EMOJI "$@"
}

# Use in script
n8n_cmd db status --format=json > status.json
n8n_cmd list --format=json > workflows.json
n8n_cmd backup-workflows --backup-dir /backups
```

## Configuration Precedence

The configuration system follows a clear precedence order:

### Precedence Hierarchy

```
1. CLI Options (--app-dir, --flow-dir)     # Highest priority
    ↓
2. Environment Variables (N8N_FLOW_DIR)    # Middle priority
    ↓
3. Default Values (current directory)      # Lowest priority
```

### Precedence Examples

```bash
# Example 1: CLI overrides environment
export N8N_FLOW_DIR=/env/workflows
n8n-deploy --flow-dir /cli/workflows list
# Uses: /cli/workflows

# Example 2: Environment overrides default
export N8N_FLOW_DIR=/env/workflows
n8n-deploy list
# Uses: /env/workflows

# Example 3: Default behavior
n8n-deploy list
# Uses: current directory
```

### Configuration Resolution Process

```python
def get_config(base_folder=None, flow_folder=None) -> n8n_deploy_Config:
    """Configuration resolution with precedence"""

    # Base folder: CLI > Current directory
    if base_folder is not None:
        base_path = Path(base_folder).resolve()  # CLI wins
    else:
        base_path = Path.cwd()  # Default

    # Flow folder: CLI > Environment > Base folder
    if flow_folder is not None:
        flow_path = Path(flow_folder).resolve()  # CLI wins
    elif "N8N_FLOW_DIR" in os.environ:
        flow_path = Path(os.environ["N8N_FLOW_DIR"]).resolve()  # ENV wins
    else:
        flow_path = None  # Use base folder (legacy)

    return n8n_deploy_Config(base_folder=base_path, flow_folder=flow_path)
```

## Use Case Configurations

### Development Configuration

**Scenario**: Local development with multiple projects

```bash
# Project structure
~/dev/
├── project-a/
│   ├── n8n-deploy/              # App data
│   └── workflows/               # Workflow files
└── project-b/
    ├── n8n-deploy/              # App data
    └── workflows/               # Workflow files

# Configuration per project
cd ~/dev/project-a
export N8N_FLOW_DIR=$(pwd)/workflows
n8n-deploy --app-dir $(pwd)/n8n-deploy db init

cd ~/dev/project-b
export N8N_FLOW_DIR=$(pwd)/workflows
n8n-deploy --app-dir $(pwd)/n8n-deploy db init

# Or use functions
dev-project-a() {
    n8n-deploy --app-dir ~/dev/project-a/n8n-deploy \
               --flow-dir ~/dev/project-a/workflows "$@"
}
```

### Production Configuration

**Scenario**: Production server with system-wide installation

```bash
# Directory structure
/opt/n8n-deploy/                 # Application data
├── n8n-deploy.db
└── backups/

/data/workflows/                 # Workflow files
└── workflows/
    └── production.json

# System configuration
cat > /etc/profile.d/n8n-deploy.sh << 'EOF'
export N8N_FLOW_DIR=/data/workflows
alias n8n-deploy='n8n-deploy --app-dir /opt/n8n-deploy'
EOF

# Service configuration
cat > /etc/systemd/system/n8n-deploy-backup.service << 'EOF'
[Unit]
Description=n8n-deploy Backup Service
After=network.target

[Service]
Type=oneshot
Environment=N8N_FLOW_DIR=/data/workflows
ExecStart=/usr/local/bin/n8n-deploy --app-dir /opt/n8n-deploy backup-workflows
User=n8n
Group=n8n

[Install]
WantedBy=multi-user.target
EOF

# Timer for regular backups
cat > /etc/systemd/system/n8n-deploy-backup.timer << 'EOF'
[Unit]
Description=Run n8n-deploy backup daily
Requires=n8n-deploy-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

### Multi-Environment Configuration

**Scenario**: Development, staging, and production environments

```bash
# Environment-specific configurations
# ~/.n8n-deploy-envs

# Development
n8n-dev() {
    export N8N_FLOW_DIR=$HOME/dev/workflows
    n8n-deploy --app-dir $HOME/dev/n8n-deploy "$@"
}

# Staging
n8n-staging() {
    export N8N_FLOW_DIR=/staging/workflows
    n8n-deploy --app-dir /staging/n8n-deploy "$@"
}

# Production
n8n-prod() {
    export N8N_FLOW_DIR=/data/workflows
    n8n-deploy --app-dir /opt/n8n-deploy "$@"
}

# Source the functions
source ~/.n8n-deploy-envs

# Usage
n8n-dev list
n8n-staging backup-workflows
n8n-prod db status
```

### Team Collaboration Configuration

**Scenario**: Shared workflow repository with individual databases

```bash
# Shared workflow repository
/shared/workflows/               # Git repository
├── .git/
└── workflows/
    ├── team-workflow-1.json
    └── team-workflow-2.json

# Individual configurations
# Team member A
export N8N_FLOW_DIR=/shared/workflows
n8n-deploy --app-dir $HOME/n8n-deploy-personal list

# Team member B
export N8N_FLOW_DIR=/shared/workflows
n8n-deploy --app-dir $HOME/n8n-deploy-personal list

# Shared backup location
n8n-deploy --app-dir $HOME/n8n-deploy-personal \
          backup-workflows --backup-dir /shared/backups
```

## Advanced Configuration

### Configuration File Support (Future)

Planned configuration file format:

```yaml
# ~/.n8n-deploy.yaml or /etc/n8n-deploy/config.yaml
app_directory: /opt/n8n-deploy
flow_directory: /data/workflows

n8n:
  api_url: https://n8n.example.com
  api_key: ${N8N_API_KEY}  # Environment variable substitution
  timeout: 30

backup:
  directory: /backups
  retention_days: 30
  compression: true

output:
  emoji: false  # For server environments
  format: table

logging:
  level: INFO
  file: /var/log/n8n-deploy.log
```

### Dynamic Configuration

**Environment Detection:**

```python
# Future: Automatic environment detection
def detect_environment():
    """Detect runtime environment and adjust configuration"""
    if os.path.exists('/.dockerenv'):
        return 'container'
    elif os.getenv('USER') == 'root':
        return 'system'
    elif os.getenv('CI'):
        return 'ci'
    else:
        return 'user'

# Adjust defaults based on environment
defaults = {
    'container': {
        'app_dir': '/app/data',
        'flow_dir': '/app/workflows',
        'emoji': False
    },
    'system': {
        'app_dir': '/opt/n8n-deploy',
        'flow_dir': '/data/workflows',
        'emoji': False
    },
    'user': {
        'emoji': True
    }
}
```

### Configuration Validation

Current validation features:

```python
def validate_configuration(config: n8n_deploy_Config) -> List[str]:
    """Validate configuration and return issues"""
    issues = []

    # Directory accessibility
    if not config.base_folder.exists():
        issues.append(f"Base folder does not exist: {config.base_folder}")

    if not os.access(config.base_folder, os.W_OK):
        issues.append(f"Base folder not writable: {config.base_folder}")

    # Flow directory validation
    if config.flow_folder and not config.flow_folder.exists():
        issues.append(f"Flow folder does not exist: {config.flow_folder}")

    # Database file validation
    if config.database_path.exists():
        if not os.access(config.database_path, os.R_OK | os.W_OK):
            issues.append(f"Database not accessible: {config.database_path}")

    return issues
```

## Configuration Migration

### Legacy Configuration Migration

From version 1.x to 2.x:

```bash
# Old (v1.x): Fixed project-relative structure
n8n-deploy/
├── n8n-deploy.db
├── n8n/
│   └── workflows/

# New (v2.x): Flexible directory structure
# No migration needed - legacy structure still works
n8n-deploy list  # Works with existing database
```

### Migration Script

```bash
#!/bin/bash
# migrate-config.sh - Migrate to new configuration system

OLD_DIR="$1"
NEW_APP_DIR="$2"
NEW_FLOW_DIR="$3"

if [[ -z "$OLD_DIR" || -z "$NEW_APP_DIR" || -z "$NEW_FLOW_DIR" ]]; then
    echo "Usage: $0 <old-dir> <new-app-dir> <new-flow-dir>"
    exit 1
fi

echo "Migrating n8n-deploy configuration..."

# Create new directories
mkdir -p "$NEW_APP_DIR"
mkdir -p "$NEW_FLOW_DIR/workflows"

# Copy database and backups
if [[ -f "$OLD_DIR/n8n-deploy.db" ]]; then
    cp "$OLD_DIR/n8n-deploy.db" "$NEW_APP_DIR/"
    echo "✅ Migrated database"
fi

if [[ -d "$OLD_DIR/backups" ]]; then
    cp -r "$OLD_DIR/backups" "$NEW_APP_DIR/"
    echo "✅ Migrated backups"
fi

# Copy workflow files
if [[ -d "$OLD_DIR/n8n/workflows" ]]; then
    cp -r "$OLD_DIR/n8n/workflows"/* "$NEW_FLOW_DIR/workflows/"
    echo "✅ Migrated workflows"
fi

# Set environment variable
echo "export N8N_FLOW_DIR='$NEW_FLOW_DIR'" >> ~/.bashrc

echo "✅ Migration complete!"
echo "New configuration:"
echo "  App directory: $NEW_APP_DIR"
echo "  Flow directory: $NEW_FLOW_DIR"
echo "  Environment: N8N_FLOW_DIR=$NEW_FLOW_DIR"
```

## Troubleshooting Configuration

### Common Configuration Issues

#### Issue 1: Directory Not Found

```bash
# Error
$ n8n-deploy list
Error: Base folder does not exist: /nonexistent/path

# Debug
echo "Current directory: $(pwd)"
echo "N8N_FLOW_DIR: $N8N_FLOW_DIR"
ls -la

# Solution
mkdir -p /correct/path
n8n-deploy --app-dir /correct/path db init
```

#### Issue 2: Permission Denied

```bash
# Error
$ n8n-deploy db init
Error: Permission denied: /readonly/path

# Debug
ls -la /readonly/
whoami
id

# Solution
# Option 1: Fix permissions
chmod 755 /readonly/path

# Option 2: Use accessible directory
n8n-deploy --app-dir ~/n8n-deploy db init
```

#### Issue 3: Environment Variable Not Recognized

```bash
# Error: Using wrong directory despite N8N_FLOW_DIR

# Debug
echo "N8N_FLOW_DIR: $N8N_FLOW_DIR"
env | grep N8N

# Check if variable is exported
declare -p N8N_FLOW_DIR

# Solution
export N8N_FLOW_DIR=/correct/path  # Must export, not just set
```

### Configuration Debugging

Enable debug output:

```bash
# Debug configuration resolution
python -c "
from api.config import get_config
import os

print('Environment N8N_FLOW_DIR:', os.getenv('N8N_FLOW_DIR', 'Not set'))
print('Current directory:', os.getcwd())

config = get_config()
print('Base folder:', config.base_folder)
print('Flow folder:', config.flow_folder)
print('Database path:', config.database_path)
print('Workflows path:', config.workflows_path)
"
```

### Configuration Verification

Verify your configuration setup:

```bash
#!/bin/bash
# verify-config.sh - Verify configuration

echo "=== n8n-deploy Configuration Verification ==="

# Check environment
echo "Environment variables:"
env | grep N8N_ || echo "  No N8N_* variables set"

# Check CLI help
echo -e "\nCLI version:"
n8n-deploy --version

# Check directory access
echo -e "\nDirectory access:"
if [[ -n "$N8N_FLOW_DIR" ]]; then
    if [[ -d "$N8N_FLOW_DIR" ]]; then
        echo "  N8N_FLOW_DIR accessible: $N8N_FLOW_DIR"
    else
        echo "  N8N_FLOW_DIR not found: $N8N_FLOW_DIR"
    fi
else
    echo "  N8N_FLOW_DIR not set"
fi

# Test database access
echo -e "\nDatabase status:"
n8n-deploy db status || echo "  Database not accessible"

echo -e "\n=== Verification complete ==="
```

---

This configuration guide provides comprehensive information for setting up n8n-deploy in any environment. For installation instructions, see [INSTALLATION.md](INSTALLATION.md). For command usage, see [CLI-REFERENCE.md](CLI-REFERENCE.md).