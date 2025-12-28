---
layout: default
title: Getting Started
nav_order: 2
description: "First steps with n8n-deploy CLI tool"
---

Welcome to n8n-deploy! This guide walks you through setup and your first workflow operations.

## Prerequisites

- **Python**: 3.9+
- **n8n Server**: Local or remote installation with API access
- **API Key**: Generated from n8n Settings → API

## Installation

### Option 1: Pip Install (Recommended)
```bash
pip install n8n-deploy
```

### Option 2: From Source
```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
pip install .
```

## One-Time Setup

### 1. Initialize Database
```bash
n8n-deploy db init --data-dir ~/.n8n-deploy
```

Creates a SQLite database to store workflow metadata, server configurations, and API keys.

### 2. Create Server Configuration
```bash
n8n-deploy server create production https://n8n.example.com
```

### 3. Add API Key Linked to Server
```bash
n8n-deploy apikey add "your-n8n-api-key" --name "prod-key" --server production
```

{: .tip }
> For security, use stdin to avoid the key in shell history: `echo "key" | n8n-deploy apikey add - --name "prod-key" --server production`

### 4. Configure SSL (Optional)
For servers with self-signed certificates:
```bash
n8n-deploy server ssl production --skip-verify
```

### 5. Verify Configuration
```bash
n8n-deploy env
```

## Workflow Operations

### Add a Workflow
```bash
# Add and link to server (stores path and server configuration)
n8n-deploy wf add workflow.json --flow-dir ./workflows --link-remote production
```

### Push and Pull
```bash
# By name or ID — database handles the rest
n8n-deploy wf push my-workflow
n8n-deploy wf pull my-workflow
```

### List Workflows
```bash
# Local database
n8n-deploy wf list

# Remote server
n8n-deploy wf list-server --remote production
```

### Update Stored Configuration
```bash
# Change flow directory
n8n-deploy wf link my-workflow --flow-dir ./new-location

# Switch to different server
n8n-deploy wf link my-workflow --server staging
```

{: .tip }
> Use `-v` or `-vv` flags for verbose output when debugging operations.

{: .note }
> Use `--no-emoji` flag for script-friendly output in automation pipelines.

## Troubleshooting

If you encounter issues:
- Check your Python version (`python --version`)
- Verify n8n server connectivity
- Review the [Troubleshooting Guide](troubleshooting/)

## Next Steps

- [Configuration Guide](configuration/) - Environment variables and precedence
- [Workflow Management](core-features/workflows/) - Advanced workflow operations
- [API Key Management](core-features/apikeys/) - Key lifecycle management
- [Troubleshooting](troubleshooting/) - Common issues and solutions
