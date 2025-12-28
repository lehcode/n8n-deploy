# n8n-deploy: Database-First n8n Workflow Management CLI

[![GitHub](https://img.shields.io/badge/GitHub-lehcode%2Fn8n--deploy-blue?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy)
[![CI/CD Pipeline](https://github.com/lehcode/n8n-deploy/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/lehcode/n8n-deploy/actions)
[![GitHub stars](https://img.shields.io/github/stars/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/commits/master)
[![GitHub issues](https://img.shields.io/github/issues/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/issues)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue?style=flat-square&logo=python)](https://github.com/lehcode/n8n-deploy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://github.com/lehcode/n8n-deploy/blob/master/LICENSE)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

<!-- PyPI badges will be enabled after first release:
[![PyPI](https://img.shields.io/pypi/v/n8n-deploy?style=flat-square&logo=pypi)](https://pypi.org/project/n8n-deploy/)
[![Downloads](https://img.shields.io/pypi/dm/n8n-deploy?style=flat-square)](https://pypi.org/project/n8n-deploy/)
-->

## Overview

`n8n-deploy` is a Python CLI that **remembers your workflow configuration**. Built on SQLite, it stores paths, servers, and settings - so deployment commands stay simple.

```bash
n8n-deploy wf push my-workflow
```

The database knows where your workflow lives and which server it belongs to.

### Key Features

- 🧠 **Smart Configuration**
  - Stores workflow paths, server links, and SSL settings
  - Push/pull by workflow name or ID
  - Override anytime with explicit flags

- 🚀 **Multi-Server Support**
  - Push and pull workflows to any n8n server
  - Per-server SSL verification settings
  - API key management with server linking

- 📁 **Folder Synchronization** (NEW in v0.2.0)
  - Bidirectional folder sync between local and n8n server
  - `folder` CLI command group for folder operations
  - Automatic folder mapping and tracking

- 💻 **Versatile CLI Interface**
  - Emoji-rich output for interactive use
  - Script-friendly mode with `--no-emoji` flag
  - Verbose logging with `-v` and `-vv` flags at any command level
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
n8n-deploy apikey add "your-n8n-api-key" --name "prod-key" --server production
# Or via stdin (key not saved in shell history)
# echo "your-n8n-api-key" | n8n-deploy apikey add - --name "prod-key" --server production

# Configure SSL for self-signed certificates (optional)
n8n-deploy server ssl production --skip-verify

# Link workflow to server with flow directory (automatic server resolution)
n8n-deploy wf add workflow.json --flow-dir ./workflows --link-remote production

# Push/pull uses linked server AND stored flow-dir automatically!
n8n-deploy wf push workflow-name  # No --flow-dir or --remote needed!
n8n-deploy wf pull workflow-name  # Uses stored paths automatically

# Update workflow metadata without push/pull
n8n-deploy wf link my-workflow --flow-dir ./new-location
n8n-deploy wf link my-workflow --server staging

# Override with --remote for ad-hoc operations
n8n-deploy wf push workflow-name --remote staging

# Delete workflow from local database
n8n-deploy wf delete workflow-name

# List workflows from server
n8n-deploy wf server --remote production

# Folder synchronization (NEW in v0.2.0)
n8n-deploy folder sync --remote production  # Sync folders with server

# Enable verbose logging for debugging
n8n-deploy -v wf push workflow-name   # Basic verbose
n8n-deploy -vv wf push workflow-name  # Extended verbose
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

- Python 3.9+
- n8n server (local or remote)
- Basic understanding of workflow management

### Performance Note

Designed for efficient workflow management with minimal overhead. Ideal for DevOps, automation engineers, and workflow enthusiasts.
