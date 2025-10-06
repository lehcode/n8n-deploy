---
layout: default
title: Core Features
nav_order: 4
has_children: true
description: "Essential n8n-deploy features for workflow management"
---

# Core Features

> "The purpose of software engineering is to control complexity, not to create it." — Pamela Zave

n8n-deploy provides four core features for managing n8n workflows across environments.

## 🎯 Overview

### Database Management
SQLite-based metadata storage for workflows, API keys, and server configurations.

**Key operations:**
- Initialize and manage workflow databases
- Create backups with integrity verification
- Compact databases for optimal performance
- Monitor database health and statistics

[Learn more →](database/)

### Server Management
Multi-server configuration for development, staging, and production environments.

**Key operations:**
- Register n8n server instances
- Link servers with API keys
- Manage server active/inactive states
- UTF-8 and emoji support for server names

[Learn more →](servers/)

### API Key Management
Secure storage and lifecycle management of n8n authentication tokens.

**Key operations:**
- Store API keys with descriptions
- Link keys to multiple servers
- Test key validity
- Deactivate or delete unused keys

[Learn more →](apikeys/)

### Workflow Management
Push and pull workflows between local storage and remote n8n servers.

**Key operations:**
- Add workflows to database
- Push workflows to servers
- Pull workflows from servers
- Search and list workflows

[Learn more →](workflows/)

---

## 🚀 Quick Links

| Feature | Common Task | Quick Command |
|---------|-------------|---------------|
| Database | Initialize | `n8n-deploy db init` |
| Server | Add server | `n8n-deploy server create "Name" URL` |
| API Key | Add key | `echo "$KEY" \| n8n-deploy apikey add - --name key_name` |
| Workflow | Push workflow | `n8n-deploy wf push "Workflow Name"` |

---

## 📖 Related Documentation

- [Getting Started](../getting-started/) - Initial setup guide
- [Quick Start Guide](../quick-start/) - 5-minute getting started
- [Configuration](../configuration/) - Environment variables
- [Quick Reference](../quick-reference/) - Command cheat sheets
- [DevOps Guide](../devops-guide/) - Advanced automation
