---
layout: default
title: Configuration
nav_order: 4
description: "Configuration options for n8n-deploy"
---

## Configuration Guide

n8n-deploy offers multiple configuration methods to suit different environments and use cases.

## 🔧 Configuration Methods

### 1. CLI Flags
Highest priority configuration method.

```bash
n8n-deploy server create "Production n8n Server 🚀" http://n8n.example.com:5678
```

### 2. Environment Variables
Second-highest priority configuration method.

```bash
# Set n8n server URL
export N8N_SERVER_URL=http://n8n.example.com:5678

# Set workflow directory
export N8N_DEPLOY_FLOWS_DIR=/path/to/workflows
```

### 3. .env Files (Development Mode)
Lowest priority configuration method, only active in development mode.

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file
ENVIRONMENT=development
N8N_SERVER_URL=http://n8n.example.com:5678
N8N_DEPLOY_FLOWS_DIR=/path/to/workflows
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

- `--flow-dir` / `N8N_DEPLOY_FLOWS_DIR`
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

{: .tip }
> **Tip**: Use environment variables for persistent settings and CLI flags for one-time overrides.

{: .warning }
> **Warning**: Keep sensitive information like API keys out of version control. Never commit `.env` files.

```bash
# Show current configuration
n8n-deploy env

# Show configuration in JSON format
n8n-deploy env --format json
```

## 🆘 Troubleshooting

- If a configuration seems incorrect, use `n8n-deploy env` to verify
- Check file paths and permissions
- Ensure API keys are correctly configured

## 📖 Related Guides

- [Getting Started](getting-started/)
- [Workflow Management](workflows/)
- [API Key Management](apikeys/)
