---
layout: default
title: Configuration
nav_order: 3
---

## Configuration Guide

n8n-deploy offers multiple configuration methods to suit different environments and use cases.

## 🔧 Configuration Methods

### 1. CLI Flags
Highest priority configuration method.

```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server
```

### 2. Environment Variables
Second-highest priority configuration method.

```bash
# Set n8n server URL
export N8N_SERVER_URL=http://n8n.example.com:5678

# Set workflow directory
export N8N_DEPLOY_FLOW_DIR=/path/to/workflows
```

### 3. .env Files (Development Mode)
Lowest priority configuration method, only active in development mode.

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file
ENVIRONMENT=development
N8N_SERVER_URL=http://n8n.example.com:5678
N8N_DEPLOY_FLOW_DIR=/path/to/workflows
```

## 📋 Available Configuration Options

### Server Configuration
- `--server-url` / `N8N_SERVER_URL`
  - Specifies the n8n server URL for remote operations
  - Example: `http://n8n.example.com:5678`

### Directory Configuration
- `--app-dir` / `N8N_DEPLOY_APP_DIR`
  - Application data directory (database, backups)
  - Default: Depends on system configuration

- `--flow-dir` / `N8N_DEPLOY_FLOW_DIR`
  - Directory containing workflow JSON files
  - Default: Current working directory

### Environment Configuration
- `ENVIRONMENT`
  - Set to `development` to enable .env file loading
  - Default: `production` (ignores .env files)

### Testing Configuration
- `N8N_DEPLOY_TESTING`
  - Set to `1` to prevent default workflow initialization during tests
  - Useful for test environments

## 🔍 Configuration Precedence

Configuration options are evaluated in this order:
1. CLI Flags (Highest Priority)
2. Environment Variables
3. .env Files (Development Mode Only)
4. Default Values (Lowest Priority)

## 💡 Pro Tips

- Use environment variables for persistent settings
- Use CLI flags for one-time overrides
- Keep sensitive information out of version control
- Use the `env` command to view current configuration

```bash
# Show current configuration
n8n-deploy env

# Show configuration in JSON format
n8n-deploy env --json
```

## 🆘 Troubleshooting

- If a configuration seems incorrect, use `n8n-deploy env` to verify
- Check file paths and permissions
- Ensure API keys are correctly configured

## 📖 Related Guides

- [Getting Started](getting-started.md)
- [Workflow Management](workflows.md)
- [API Key Management](apikeys.md)