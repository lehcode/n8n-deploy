# n8n-deploy: Database-First n8n Workflow Management CLI

[![GitHub](https://img.shields.io/badge/GitHub-lehcode%2Fn8n--deploy-blue?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy)
[![CI/CD Pipeline](https://github.com/lehcode/n8n-deploy/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/lehcode/n8n-deploy/actions)
[![GitHub stars](https://img.shields.io/github/stars/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/commits/master)
[![GitHub issues](https://img.shields.io/github/issues/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/issues)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue?style=flat-square&logo=python)](https://github.com/lehcode/n8n-deploy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://github.com/lehcode/n8n-deploy/blob/master/LICENSE)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

<!-- PyPI badges will be enabled after first release:
[![PyPI](https://img.shields.io/pypi/v/n8n-deploy?style=flat-square&logo=pypi)](https://pypi.org/project/n8n-deploy/)
[![Downloads](https://img.shields.io/pypi/dm/n8n-deploy?style=flat-square)](https://pypi.org/project/n8n-deploy/)
-->

## Overview

`n8n-deploy` is a powerful Python CLI tool designed to simplify n8n workflow management through a database-first approach. It provides a flexible, efficient solution for managing n8n workflows, especially in environments without direct web UI access.

### Key Features

- 🗂️ **Database-Driven Workflow Management**
  - SQLite metadata store for tracking workflows
  - Support for new workflows without server ID (auto-generates draft ID)
  - Flexible base folder configuration
  - Plain text API key storage

- 🚀 **Seamless n8n Server Integration**
  - Push and pull workflows directly from remote n8n servers
  - Workflow-server linking for automatic server resolution
  - Priority-based server configuration (linked server → ENV → --remote)
  - Support for multiple server configurations with API key management

- 💻 **Versatile CLI Interface**
  - Emoji-rich output for interactive use
  - Script-friendly mode with `--no-emoji` flag
  - Comprehensive workflow operations

### Installation

```bash
# Pip install
pip install n8n-deploy

# Use uv for faster setup and virtual environment
uv venv --python /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install n8n-deploy
```

### Quick Start

```bash
# Initialize database
n8n-deploy db init --data-dir ~/.n8n-deploy

# Create server and add API key
n8n-deploy server create production https://n8n.example.com
echo "your-n8n-api-key" | n8n-deploy apikey add - --name "prod-key"

# Link workflow to server (automatic server resolution)
n8n-deploy wf add workflow.json --link-remote production

# Push/pull uses linked server automatically (no --remote needed!)
n8n-deploy wf push workflow-name  # Uses production server
n8n-deploy wf pull workflow-name  # Uses production server

# Override with --remote for ad-hoc operations
n8n-deploy wf push workflow-name --remote staging

# List workflows from server
n8n-deploy wf server --remote production
```

### Community & Support

💬 **Get Help & Connect**:
- **[Discussions](https://github.com/lehcode/n8n-deploy/discussions)** - Ask questions, share ideas, showcase workflows
- **[Issues](https://github.com/lehcode/n8n-deploy/issues)** - Report bugs or request features
- **[Documentation](https://lehcode.github.io/n8n-deploy)** - Complete guides and API reference

**Discussion Categories**:
- 📣 **Announcements** - Project updates and releases
- 🙏 **Q&A** - Get help from the community
- 💡 **Ideas** - Suggest new features
- 🎯 **Show and Tell** - Share your workflows
- #️⃣ **General** - Everything else

### Configuration

`n8n-deploy` supports multiple configuration methods:

1. CLI Flags
2. Environment Variables
3. `.env` Files (in development mode)

#### Environment Variables

- `N8N_DEPLOY_FLOWS_DIR`: Workflow files directory
- `N8N_DEPLOY_DATA_DIR`: Application data directory
- `N8N_SERVER_URL`: n8n server URL for remote operations

### Documentation

📚 **[Read the full documentation](https://lehcode.github.io/n8n-deploy/)**

Quick Links:
- [Getting Started](https://lehcode.github.io/n8n-deploy/getting-started.html)
- [Configuration Guide](https://lehcode.github.io/n8n-deploy/configuration.html)
- [Workflow Management](https://lehcode.github.io/n8n-deploy/workflows.html)
- [API Key Management](https://lehcode.github.io/n8n-deploy/apikeys.html)
- [Troubleshooting](https://lehcode.github.io/n8n-deploy/troubleshooting.html)

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

**Quick Links**:
- [Developer Guide](https://lehcode.github.io/n8n-deploy/developers/)
- [Architecture Overview](https://lehcode.github.io/n8n-deploy/developers/architecture.html)
- [Testing Framework](https://lehcode.github.io/n8n-deploy/developers/testing.html)

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Requirements

- Python 3.8+
- n8n server (local or remote)
- Basic understanding of workflow management

### Performance Note

Designed for efficient workflow management with minimal overhead. Ideal for DevOps, automation engineers, and workflow enthusiasts.
