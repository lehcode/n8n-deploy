---
layout: default
title: Home
nav_order: 1
description: "Python CLI tool for managing n8n workflows with SQLite metadata"
permalink: /
---
# n8n-deploy: Database-First n8n Workflow Management CLI

> "Complexity is the enemy of reliability." — Arthur Bloch, Murphy's Laws

A Python CLI that remembers your workflow configuration. Set up once, deploy anytime.

## Key Features

- **Smart Configuration Storage**
  - SQLite database stores workflow paths, server links, and SSL settings
  - Push and pull by workflow name or ID (copy from n8n UI URL)
  - Override stored settings anytime with explicit flags

- **Multi-Server Support**
  - Manage workflows across multiple n8n servers
  - Per-server SSL verification settings
  - API keys linked to specific servers

## Quick Start

### Installation

```bash
pip install n8n-deploy
```

Full details in the [Installation Guide](user-guide/installation/)

### One-Time Setup

```bash
# Initialize database
n8n-deploy db init --data-dir ~/.n8n-deploy

# Create server configuration
n8n-deploy server create production https://n8n.example.com

# Add API key linked to server
n8n-deploy apikey add "your-api-key" --name "prod-key" --server production

# Optional: Skip SSL verification for self-signed certificates
n8n-deploy server ssl production --skip-verify
```

### Daily Workflow Operations

```bash
# Add workflow with server link (stores configuration)
n8n-deploy wf add workflow.json --flow-dir ./workflows --link-remote production

# Push and pull by name or ID
n8n-deploy wf push my-workflow
n8n-deploy wf pull my-workflow

# Update stored configuration without syncing
n8n-deploy wf link my-workflow --flow-dir ./new-location
n8n-deploy wf link my-workflow --server staging
```

{: .tip }
> After initial setup, most workflow management commands need only the workflow name or ID. The database handles paths and server selection automatically.

## Documentation

### User Guides
- [Installation Guide](user-guide/installation/)
- [Getting Started](getting-started/)
- [Configuration](configuration/)

### Core Features
- [Database Management](core-features/database/) - SQLite operations and backups
- [Workflow Management](core-features/workflows/) - Push/pull workflow operations
- [API Key Management](core-features/apikeys/) - Secure key handling
- [Server Management](core-features/servers/) - Multi-server configuration

### Advanced Topics
- [DevOps Integration](user-guide/devops-integration/) - CI/CD pipelines and automation
- [Troubleshooting](troubleshooting/) - Common issues and solutions

### Quick Reference
- [Database Commands](quick-reference/database-commands/) - CLI cheat sheet

## Contributing

Interested in contributing? Check out our:

- [Contributing Guide](https://github.com/lehcode/n8n-deploy/blob/master/CONTRIBUTING.md) - How to contribute
- [Code of Conduct](https://github.com/lehcode/n8n-deploy/blob/master/CODE_OF_CONDUCT.md) - Community guidelines
- [Changelog](https://github.com/lehcode/n8n-deploy/blob/master/CHANGELOG.md) - Project history
- [TODO](https://github.com/lehcode/n8n-deploy/blob/master/TODO.md) - Planned features

## License

MIT License. See [LICENSE](https://github.com/lehcode/n8n-deploy/blob/master/LICENSE) for details.
