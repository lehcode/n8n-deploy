---
layout: default
title: FAQ
nav_order: 7
description: "Frequently asked questions about n8n-deploy"
---

# Frequently Asked Questions

> "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% of the code accounts for the other 90% of the development time." — Tom Cargill

## General Questions

### What is n8n-deploy?

n8n-deploy is a Python CLI tool for managing n8n workflows using a database-first approach. It provides a SQLite metadata store for tracking workflows, especially useful for remote servers without web UI access.

### Why use n8n-deploy instead of the n8n web interface?

n8n-deploy is ideal when:
- You need to manage workflows on remote servers without web UI access
- You want version control and command-line workflow management
- You need to automate workflow deployment in CI/CD pipelines
- You prefer CLI tools for workflow operations

### What are the system requirements?

- Python 3.8 or higher
- n8n server (local or remote)
- SQLite3 (included with Python)
- Basic understanding of n8n workflows

## Installation & Setup

### How do I install n8n-deploy?

```bash
pip install n8n-deploy
```

Or install from source:
```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
pip install -e .
```

### How do I initialize the database?

```bash
n8n-deploy db init
```

{: .tip }
> Use the `--import` flag to accept an existing database without prompting.

### Where is the database stored?

By default, the database is stored in the directory specified by `N8N_DEPLOY_APP_DIR` environment variable, or you can specify it with the `--app-dir` CLI flag.

## Configuration

### How do I configure n8n-deploy?

Configuration follows this priority order:
1. CLI flags (highest priority)
2. Environment variables
3. .env files (development mode only)
4. Default values

See the [Configuration Guide](configuration.md) for details.

### How do I set up multiple n8n servers?

Add API keys for each server:
```bash
echo "production-key" | n8n-deploy apikey add prod_server
echo "staging-key" | n8n-deploy apikey add staging_server
```

Then specify the server URL when running commands:
```bash
n8n-deploy --server-url http://prod.example.com wf list-server
```

### Can I use n8n-deploy with self-signed certificates?

Yes, use the `--skip-ssl-verify` flag:
```bash
n8n-deploy --server-url https://n8n.local --skip-ssl-verify wf list-server
```

{: .warning }
> **Warning**: Only use `--skip-ssl-verify` for trusted servers. It disables SSL certificate validation.

## Workflow Management

### How do I pull workflows from my n8n server?

```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf pull "Workflow Name"
```

### How do I push workflows to my n8n server?

```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf push "Workflow Name"
```

### Where are workflow files stored?

Workflows are stored as JSON files in the directory specified by `N8N_FLOW_DIR` environment variable or `--flow-dir` CLI flag. Files are named by their n8n workflow ID.

### How do I backup my workflows?

```bash
# Backup all workflows
n8n-deploy wf backup

# Backup specific workflow
n8n-deploy wf backup "My Workflow"
```

Backups are stored as tar.gz archives with SHA256 checksums for integrity verification.

### Can I search for workflows?

Yes:
```bash
n8n-deploy wf search "customer"
```

## Troubleshooting

### I'm getting "database not found" errors

Initialize the database first:
```bash
n8n-deploy db init
```

Or specify the correct app directory:
```bash
n8n-deploy --app-dir /path/to/app db status
```

### API key authentication is failing

Test your API key:
```bash
n8n-deploy apikey test my_server --server-url http://n8n.example.com:5678
```

Ensure:
- The API key is valid and hasn't expired
- The server URL is correct (including port)
- The n8n server is accessible

### Workflows aren't syncing correctly

1. Check server connectivity:
   ```bash
   n8n-deploy --server-url http://n8n.example.com:5678 wf list-server
   ```

2. Verify workflow names match exactly (case-sensitive)

3. Check API key permissions

See the [Troubleshooting Guide](troubleshooting.md) for more solutions.

## Development

### How do I contribute to n8n-deploy?

See our [Contributing Guidelines](developers/contributing.md) for:
- Development environment setup
- Code style requirements
- Testing procedures
- Pull request process

### How do I run tests?

```bash
# Run all tests
python run_tests.py --all

# Run unit tests only
python run_tests.py --unit

# Run integration tests
python run_tests.py --integration
```

### Where can I report bugs or request features?

Create an issue on [GitHub](https://github.com/lehcode/n8n-deploy/issues) with:
- Detailed description
- Steps to reproduce
- System information
- Expected vs actual behavior

## Performance & Optimization

### How many workflows can n8n-deploy handle?

n8n-deploy is designed to handle thousands of workflows efficiently. SQLite can manage databases up to 281 terabytes, so workflow count is rarely a limitation.

### Can I use n8n-deploy in production?

Yes! n8n-deploy is production-ready and includes:
- Database integrity checks
- Backup and restore functionality
- API key lifecycle management
- Comprehensive error handling

{: .note }
> Always test in a staging environment first and keep regular backups.

### How do I optimize performance?

- Use `--no-emoji` flag for faster output in scripts
- Keep workflow JSON files in a dedicated directory
- Regularly compact the database: `n8n-deploy db compact`
- Use environment variables for persistent configuration

## Security

### How are API keys stored?

API keys are stored in plain text in the SQLite database. The database should be:
- Stored in a secure location with appropriate file permissions
- Not committed to version control
- Backed up securely

### Can I encrypt the database?

SQLite encryption is not built-in, but you can:
- Use filesystem-level encryption
- Store the database on an encrypted volume
- Use SQLCipher (requires custom build)

### What data does n8n-deploy collect?

n8n-deploy does not collect or transmit any telemetry data. All operations are local except when communicating with your specified n8n server.

## Related Resources

- [Getting Started Guide](getting-started.md)
- [Configuration Guide](configuration.md)
- [Workflow Management](workflows.md)
- [API Key Management](apikeys.md)
- [Developer Guide](developers/index.md)
- [Troubleshooting](troubleshooting.md)

---

**Didn't find your question?**
Check our [GitHub Discussions](https://github.com/lehcode/n8n-deploy/discussions) or open an [issue](https://github.com/lehcode/n8n-deploy/issues).
