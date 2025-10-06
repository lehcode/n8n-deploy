---
layout: default
title: FAQ
nav_order: 6
description: "Frequently asked questions about n8n-deploy"
---

# Frequently Asked Questions

> "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% of the code accounts for the other 90% of the development time." — Tom Cargill

## General Questions

### What is n8n-deploy?

n8n-deploy is a Python CLI tool for managing n8n workflows using a database-first approach with a SQLite metadata store. It's particularly useful for remote servers without web UI access.

### Why use n8n-deploy?

Ideal scenarios include:
- Managing workflows on remote servers
- Version controlling workflows
- Automating workflow deployment in CI/CD
- Preferring CLI-based workflow management

## Installation and Setup

### How do I install n8n-deploy?

See our comprehensive [Installation Guide](user-guide/installation/) for all details and methods.

### What are the system requirements?

- Python 3.8+
- n8n server (local or remote)
- SQLite3 (included with Python)

## Configuration

### How are configuration settings managed?

Configuration follows this priority:
1. CLI flags (highest priority)
2. Environment variables
3. `.env` files (development mode only)
4. Default values

Full details in the [Configuration Guide](configuration/).

## Workflow Management

### How do I list, pull, or push workflows?

Workflow operations are covered in the [Workflow Management Guide](core-features/workflows/). Basic examples:

```bash
# List local workflows
n8n-deploy wf list

# List server workflows
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Pull a workflow
n8n-deploy wf pull "My Workflow"

# Push a workflow
n8n-deploy wf push "Deploy Workflow"
```

## Troubleshooting

### Common Issues

If you encounter problems, check:
- [Troubleshooting Guide](troubleshooting/)
- Verify Python version: `python --version`
- Check server connectivity
- Review error messages carefully

## Development and Contribution

### How can I contribute?

See our [Contributing Guide](developers/contributing/) for:
- Development setup
- Code style requirements
- Testing procedures
- Pull request process

## Security and Performance

### Is n8n-deploy production-ready?

Yes! Features include:
- Database integrity checks
- Backup and restore functionality
- API key lifecycle management
- Comprehensive error handling

### Does n8n-deploy collect telemetry?

No. n8n-deploy does not collect or transmit any telemetry data. All operations are local except when communicating with your specified n8n server.

## Resources

- [Official Documentation](index/)
- [GitHub Repository](https://github.com/lehcode/n8n-deploy/)
- [Changelog](https://github.com/lehcode/n8n-deploy/blob/master/CHANGELOG.md) - Version history
- [TODO](https://github.com/lehcode/n8n-deploy/blob/master/TODO.md) - Planned features
- [Contributing Guide](https://github.com/lehcode/n8n-deploy/blob/master/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/lehcode/n8n-deploy/blob/master/CODE_OF_CONDUCT.md)
- [Issue Tracker](https://github.com/lehcode/n8n-deploy/issues/)

---

**Didn't find your answer?**
- Check [GitHub Discussions](https://github.com/lehcode/n8n-deploy/discussions/)
- [Open an Issue](https://github.com/lehcode/n8n-deploy/issues/)