---
layout: default
title: Home
nav_order: 1
description: "Python CLI tool for managing n8n workflows with SQLite metadata"
permalink: /
---
# n8n-deploy: Database-First n8n Workflow Management CLI

Welcome to the official documentation for n8n-deploy, a powerful Python CLI tool for managing n8n workflows with a SQLite metadata store.

## 🚀 Quick Overview

n8n-deploy provides a database-first approach to workflow management, designed to simplify and streamline your n8n automation workflows, especially for remote servers without web UI access.

> "Automation is not about replacing humans, but about empowering them to focus on what truly matters." - Adapted from Arthur Bloch's Murphy's Laws

### 🌟 Key Features

- **Database-First Management**
  - SQLite as the single source of truth for workflow metadata
  - Track, manage, and version your workflows efficiently

- **Remote Server Integration**
  - Seamless push/pull operations with n8n servers
  - Flexible configuration for multiple server environments

- **API Key Management**
  - Simple, secure lifecycle management for n8n API keys
  - Plain text storage with easy configuration

## 📦 Installation

### Using Pip (Recommended)
```bash
pip install n8n-deploy
```

### From Source
```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
pip install .
```

## 🖥️ Quick Start

### Initialize Database
```bash
n8n-deploy db init
```

### Add API Key
```bash
# Interactive key entry
echo "your_n8n_api_key" | n8n-deploy apikey add my_server
```

### Workflow Operations
```bash
# List local workflows
n8n-deploy wf list

# List remote server workflows
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Pull a workflow from remote server
n8n-deploy wf pull "My Workflow"

# Push a workflow to remote server
n8n-deploy wf push "Deploy Workflow"
```

## 📚 Table of Contents

1. [Getting Started](getting-started.md)
2. [Installation](installation.md)
3. [Configuration](configuration.md)
4. [Workflow Management](workflows.md)
5. [API Key Management](apikeys.md)
6. [Troubleshooting](troubleshooting.md)
7. [FAQ](faq.md)
8. [Developer Guide](developers/index.md)

## 🤝 Contributing

Interested in contributing? Check out our [Contributing Guide](CONTRIBUTING.md).

## 📝 License

MIT License. See [LICENSE](../LICENSE) for details.
