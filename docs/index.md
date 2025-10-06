---
layout: default
title: Home
nav_order: 1
description: "Python CLI tool for managing n8n workflows with SQLite metadata"
permalink: /
---
# n8n-deploy: Database-First n8n Workflow Management CLI

> "Complexity is the enemy of reliability." — Arthur Bloch, Murphy's Laws

Welcome to n8n-deploy, a powerful Python CLI tool for managing n8n workflows with a SQLite metadata store.

## 🌟 Key Features

- **Database-First Management**
  - SQLite as the single source of truth for workflow metadata
  - Efficient workflow tracking, management, and versioning

- **Remote Server Integration**
  - Seamless push/pull operations with n8n servers
  - Flexible configuration for multiple server environments

- **API Key Management**
  - Simple, secure lifecycle management
  - Plain text storage with easy configuration

## 🚀 Quick Start

1. **Installation**
   - Full details in the [Installation Guide](user-guide/installation.md)
   ```bash
   pip install n8n-deploy
   ```

2. **Initialize Database**
   ```bash
   n8n-deploy db init
   ```

3. **Add API Key**
   ```bash
   echo "your_n8n_api_key" | n8n-deploy apikey add my_server
   ```

## 📖 Documentation

- [Installation Guide](user-guide/installation.md)
- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Workflow Management](workflows.md)
- [API Key Management](apikeys.md)
- [Troubleshooting](troubleshooting.md)

## 🤝 Contributing

Interested in contributing? Check out our [Contributing Guide](developers/contributing.md).

## 📝 License

MIT License. See [LICENSE](../LICENSE) for details.