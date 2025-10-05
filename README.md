# n8n-deploy: Database-First n8n Workflow Management CLI

> "If builders built buildings the way programmers wrote programs, then the first woodpecker that came along would destroy civilization." - Arthur Bloch, Murphy's Laws

## Overview

`n8n-deploy` is a powerful Python CLI tool designed to simplify n8n workflow management through a database-first approach. It provides a flexible, efficient solution for managing n8n workflows, especially in environments without direct web UI access.

### Key Features

- 🗂️ **Database-Driven Workflow Management**
  - SQLite metadata store for tracking workflows
  - Flexible base folder configuration
  - Plain text API key storage

- 🚀 **Seamless n8n Server Integration**
  - Push and pull workflows directly from remote n8n servers
  - Support for multiple server configurations
  - Secure API key handling

- 💻 **Versatile CLI Interface**
  - Emoji-rich output for interactive use
  - Script-friendly mode with `--no-emoji` flag
  - Comprehensive workflow operations

### Installation

```bash
# Recommended: Use uv for faster setup
uv venv --python /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install n8n-deploy

# Alternative: Pip install
pip install n8n-deploy
```

### Quick Start

```bash
# Initialize database
n8n-deploy db init

# Add an API key for your n8n server
echo "your-n8n-api-key" | n8n-deploy apikey add my_server_key

# List workflows from a remote n8n server
n8n-deploy --server-url http://n8n.example.com wf list-server

# Pull a specific workflow
n8n-deploy --server-url http://n8n.example.com wf pull "My Workflow"
```

### Configuration

`n8n-deploy` supports multiple configuration methods:

1. CLI Flags
2. Environment Variables
3. `.env` Files (in development mode)

#### Environment Variables

- `N8N_DEPLOY_FLOW_DIR`: Workflow files directory
- `N8N_DEPLOY_APP_DIR`: Application data directory
- `N8N_SERVER_URL`: n8n server URL for remote operations

### Documentation

- [User Guide](/docs/user-guide/README.md)
- [Configuration Guide](/docs/configuration.md)
- [Workflow Management](/docs/workflows.md)
- [Troubleshooting](/docs/troubleshooting.md)

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](/docs/CONTRIBUTING.md) for details.

### License

This project is licensed under the terms specified in the [LICENSE](/LICENSE) file.

### Requirements

- Python 3.8+
- n8n server (local or remote)
- Basic understanding of workflow management

### Support and Community

- GitHub Issues: Report bugs or request features
- Discord/Slack: Community support channels (links to be added)

### Performance Note

Designed for efficient workflow management with minimal overhead. Ideal for DevOps, automation engineers, and workflow enthusiasts.