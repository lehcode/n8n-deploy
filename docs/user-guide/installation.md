---
layout: default
title: Installation
parent: User Guide
nav_order: 1
description: "Comprehensive guide for installing and setting up n8n-deploy"
---

# Installation & Setup for n8n-deploy

> "Automation is about augmenting human capabilities, not replacing them." — Adapted from Arthur Bloch's Murphy's Laws on Complexity

Get n8n-deploy running on your system quickly and efficiently.

## Prerequisites

- **Python 3.8+**: Verified on versions 3.8 through 3.12
- **Basic Understanding**: Familiarity with n8n workflows and CLI tools

## Installation Methods

### Option 1: PyPI (Recommended)

The simplest way to install n8n-deploy:

```bash
pip install n8n-deploy
```

Verify installation:
```bash
n8n-deploy --version
```

### Option 2: Direct from GitHub

For the latest development version:

```bash
pip install git+https://github.com/lehcode/n8n-deploy.git
```

### Option 3: Local Development

Clone and run directly:

```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
./n8n-deploy --help  # Immediate usage
```

The wrapper script creates a virtual environment automatically.

## System Requirements

### Supported Platforms

- Linux (Ubuntu, Debian, Fedora, Arch)
- macOS (10.14+)
- Windows (via WSL2)

### Python and Dependencies

- **Python Version**: 3.8+
- **Core Dependencies** (auto-installed):
  - click: CLI framework
  - rich: Terminal formatting
  - pydantic: Data validation
  - requests: HTTP client
  - python-dotenv: Environment file support (dev only)

## Initial Configuration

### Set Up Directories

Configure where to store application data and workflow files:

```bash
# Application data directory
export N8N_DEPLOY_DATA_DIR=~/n8n-data

# Workflow JSON files directory
export N8N_DEPLOY_FLOWS_DIR=~/workflows
```

Add these to your shell profile for persistence.

### Initialize Database

Create the SQLite metadata store:

```bash
n8n-deploy db init
```

For existing databases:
```bash
n8n-deploy db init --import  # Accept existing database
```

### Verify Setup

Confirm your installation:

```bash
n8n-deploy db status
n8n-deploy env  # Show configuration
```

## Optional: n8n Server Integration

To sync with a remote n8n server:

```bash
# Set server URL
export N8N_SERVER_URL=https://n8n.example.com

# Add API key
echo "your-api-key-here" | n8n-deploy apikey add production

# Test connection
n8n-deploy wf list-server
```

## Development Environment

For development, create a `.env` file:

```bash
cp .env.example .env
```

Edit with your settings:
```bash
ENVIRONMENT=development
N8N_DEPLOY_DATA_DIR=/home/user/n8n-data
N8N_DEPLOY_FLOWS_DIR=/home/user/workflows
N8N_SERVER_URL=http://localhost:5678
```

**Note**: `.env` files only work in development mode.

## Troubleshooting

### Common Installation Issues

- **Command Not Found**:
  ```bash
  pip show n8n-deploy
  python -m n8n_deploy --help
  ```

- **Permission Errors**:
  ```bash
  pip install --user n8n-deploy
  ```

- **Version Conflicts**:
  ```bash
  python -m venv n8n-env
  source n8n-env/bin/activate
  pip install n8n-deploy
  ```

## Next Steps

- [Configuration Guide](../configuration/)
- [Workflow Management Guide](../core-features/workflows/)
- [Troubleshooting](../troubleshooting/)

---

Installation complete! Proceed to the [Getting Started Guide](getting-started/) to manage your first workflows.