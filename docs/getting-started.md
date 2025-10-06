---
layout: default
title: Getting Started
nav_order: 2
description: "Quick start guide for n8n-deploy CLI installation and setup"
---


Welcome to n8n-deploy! This guide will help you get up and running quickly with our workflow management CLI.

## 🎯 Prerequisites

- **Python Version**: 3.8+
- **n8n Server**: Local or remote installation
- **Basic Understanding**: Familiarity with n8n workflows and API concepts

## 🔧 Installation Methods

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

## 🚀 First-Time Setup

### 1. Initialize Database
```bash
n8n-deploy db init
```
This creates a new SQLite database to track your workflows.

### 2. Configure n8n Server API Key
```bash
# Interactive key entry
echo "your_n8n_api_key" | n8n-deploy apikey add my_server
```

### 3. Verify Configuration
```bash
# Check environment configuration
n8n-deploy env
```

## 🌈 Basic Workflow Operations

### List Local Workflows
```bash
n8n-deploy wf list
```

### List Remote Server Workflows
```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server
```

### Pull a Workflow from Remote Server
```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf pull "My Workflow"
```

### Push a Workflow to Remote Server
```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf push "Deploy Workflow"
```

{: .tip }
> **Tip**: Use the `--no-emoji` flag for script-friendly output when integrating with automation scripts.

{: .note }
> Configure environment variables for persistent settings across terminal sessions.

## 🆘 Troubleshooting

If you encounter any issues:
- Check your Python version (`python --version`)
- Verify n8n server connectivity
- Review the [Troubleshooting Guide](troubleshooting.md)

## 📖 Next Steps

- [Configuration Guide](configuration.md)
- [Workflow Management](workflows.md)
- [API Key Management](apikeys.md)