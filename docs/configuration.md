---
layout: default
title: Configuration
nav_order: 3
---

## Configuration Guide

n8n-deploy uses a local SQLite database to store workflow paths, server links, and SSL settings. Configuration can come from CLI flags, the database, or environment variables.

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
- `--remote` / `N8N_SERVER_URL`
  - Specifies the n8n server for remote operations
  - Resolution priority:
    1. CLI explicit (`--remote staging`)
    2. Workflow's linked server (`server_id` in database)
    3. Environment variable (`N8N_SERVER_URL`)
  - Example: `n8n-deploy wf push my-workflow --remote production`

### SSL Verification
- `--skip-ssl-verify` (per-command)
  - Bypasses SSL certificate verification for current operation
  - Useful for servers with self-signed certificates

- `server ssl` command (persistent)
  - Stores SSL setting in database per server
  - `n8n-deploy server ssl production --skip-verify`
  - `n8n-deploy server ssl production --verify`
  - Resolution priority:
    1. CLI flag (`--skip-ssl-verify`)
    2. Server's stored setting (`skip_ssl_verify` column)
    3. Default: verify SSL certificates

### Directory Configuration
- `--data-dir` / `N8N_DEPLOY_DATA_DIR`
  - Application data directory (database, backups)
  - **Required**: Must be set via CLI or environment

- `--flow-dir` / `N8N_DEPLOY_FLOWS_DIR`
  - Directory containing workflow JSON files
  - Resolution priority:
    1. CLI explicit (`--flow-dir ./foo`)
    2. Workflow's stored `file_folder` from database
    3. Environment variable (`N8N_DEPLOY_FLOWS_DIR`)
    4. Current working directory (with warning)

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
2. Database-stored values (workflow `file_folder`, `server_id`, server `skip_ssl_verify`)
3. Environment Variables
4. .env Files (Development Mode Only)
5. Default Values (Lowest Priority)

## 🔗 Updating Stored Configuration

Use `wf link` to update workflow metadata without push/pull:

```bash
# Update stored flow directory
n8n-deploy wf link my-workflow --flow-dir ./new-location

# Link to different server
n8n-deploy wf link my-workflow --server production

# Combine options
n8n-deploy wf link my-workflow --flow-dir ./workflows --server staging
```

Use `server ssl` to configure per-server SSL settings:

```bash
# Skip SSL verification for server
n8n-deploy server ssl production --skip-verify

# Re-enable SSL verification
n8n-deploy server ssl production --verify
```

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