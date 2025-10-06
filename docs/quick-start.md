---
layout: default
title: Quick Start Guide
nav_order: 3
description: "Get started with n8n-deploy in 5 minutes"
---

# Quick Start Guide

> "If you can't explain it simply, you don't understand it well enough." — Albert Einstein

Get n8n-deploy running in 5 minutes with this fast-track guide.

## Prerequisites

- Python 3.8+ installed
- n8n server accessible (local or remote)
- n8n API key ([generate here](https://docs.n8n.io/api/authentication/))

---

## 🚀 5-Minute Setup

### Step 1: Install n8n-deploy

```bash
pip install n8n-deploy
```

### Step 2: Initialize Database

```bash
# Create application directory and database
n8n-deploy db init
```

### Step 3: Add API Key

```bash
# Add your n8n API key
echo "your_n8n_api_key_here" | n8n-deploy apikey add - --name my_server
```

### Step 4: Configure Server

```bash
# Add your n8n server
n8n-deploy server create "My Server" http://localhost:5678

# Link API key to server
n8n-deploy server keys "My Server"
```

### Step 5: Start Using

```bash
# Pull workflows from server
n8n-deploy --server-url http://localhost:5678 wf pull "Customer Onboarding"

# List local workflows
n8n-deploy wf list

# Push workflow back to server
n8n-deploy wf push "Customer Onboarding"
```

---

## ⚡ Common Tasks

### Pull All Workflows

```bash
n8n-deploy --server-url http://localhost:5678 wf pull --all
```

### Push Workflow to Production

```bash
# Set server URL
export N8N_SERVER_URL=https://n8n-prod.company.com

# Push workflow
n8n-deploy wf push "Production Deployment"
```

### Backup Database

```bash
n8n-deploy db backup
```

### Check Status

```bash
# Database status
n8n-deploy db status

# List servers
n8n-deploy server list

# List API keys
n8n-deploy apikey list
```

---

## 🔧 Configuration

### Environment Variables

Create `~/.env` file:

```bash
# Application data directory
N8N_DEPLOY_DATA_DIR=/path/to/app/data

# Workflow files directory
N8N_DEPLOY_FLOWS_DIR=/path/to/workflows

# Default server URL
N8N_SERVER_URL=http://localhost:5678
```

Enable `.env` loading:

```bash
export ENVIRONMENT=development
```

### CLI Overrides

```bash
# Override directories
n8n-deploy --data-dir /custom/path db status

# Override server URL
n8n-deploy --server-url https://n8n.example.com wf list-server
```

---

## 🎯 Next Steps

### Learn Core Features
- [Database Management](core-features/database/) - Metadata storage and backups
- [Server Management](core-features/servers/) - Multi-environment configuration
- [API Key Management](core-features/apikeys/) - Authentication setup
- [Workflow Management](core-features/workflows/) - Push/pull operations

### Advanced Topics
- [Configuration](configuration/) - Detailed environment setup
- [DevOps Guide](devops-guide/) - CI/CD integration
- [Quick Reference](quick-reference/) - Command cheat sheets

### Help & Support
- [Troubleshooting](troubleshooting/) - Common issues
- [FAQ](faq/) - Frequently asked questions
- [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues) - Report bugs

---

## 💡 Pro Tips

1. **Use Environment Variables**: Set `N8N_SERVER_URL` to avoid `--server-url` flags
2. **Script-Friendly Output**: Add `--no-emoji` for automation scripts
3. **JSON Output**: Use `--json` for parsing in scripts
4. **Backup Regularly**: Schedule `n8n-deploy db backup` via cron
5. **Version Control**: Store workflow JSON files in git repositories

---

**Ready to dive deeper?** Check out the [Getting Started Guide](getting-started/) for comprehensive setup instructions.
