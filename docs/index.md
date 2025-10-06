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
   - Full details in the [Installation Guide](user-guide/installation/)
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

### User Guides
- [Installation Guide](user-guide/installation/)
- [Getting Started](getting-started/)
- [Configuration](configuration/)

### Core Features
- [Database Management](database/) - SQLite operations and backups
- [Workflow Management](workflows/) - Push/pull workflow operations
- [API Key Management](apikeys/) - Secure key handling
- [Server Management](servers/) - Multi-server configuration

### Advanced Topics
- [DevOps Integration](user-guide/devops-integration/) - CI/CD pipelines and automation
- [Troubleshooting](troubleshooting/) - Common issues and solutions

### Quick Reference
- [Database Commands](quick-reference/database-commands/) - CLI cheat sheet

## 🤝 Contributing

Interested in contributing? Check out our [Contributing Guide](developers/contributing/).

## 📝 License

MIT License. See [LICENSE](https://github.com/lehcode/n8n-deploy/blob/master/LICENSE) for details.