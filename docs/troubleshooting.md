---
layout: default
title: Troubleshooting
nav_order: 5
description: "Common issues and solutions for n8n-deploy"
---

This guide helps you resolve common issues when using n8n-deploy.

## 🚨 Common Problems and Solutions

### 1. API Key Issues

**Symptom**: Unable to connect to n8n server

**Solutions**:

```bash
# Test API key
n8n-deploy apikey test my_server

# Verify server URL
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Use verbose flag for more details
n8n-deploy --verbose apikey test my_server
```

### 2. Database Initialization Problems

**Symptom**: Database not found or cannot be created

{: .note }
> Use the `--import` flag to accept an existing database without prompting.

**Solutions**:

```bash
# Reinitialize database with import flag
n8n-deploy db init --import

# Check database status
n8n-deploy db status

# Specify custom app directory
n8n-deploy --data-dir /custom/path db init
```

### 3. Workflow Pull/Push Failures

**Symptom**: Cannot pull or push workflows

{: .warning }
> **Warning**: SSL verification issues? Use `--skip-ssl-verify` flag for self-signed certificates, but be aware of security implications.

{: .note }
> **Read-only fields**: n8n-deploy automatically strips read-only fields (`id`, `triggerCount`, `updatedAt`, `createdAt`, `versionId`, `staticData`, `tags`, `meta`) before push operations. If you encounter 400 errors with manually edited workflow files, ensure you're using the latest version.

**Solutions**:

```bash
# Check server connectivity
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Skip SSL verification (for self-signed certs)
n8n-deploy --server-url https://n8n.example.com:5678 --skip-ssl-verify wf list-server

# Verify workflow name exactly
n8n-deploy wf pull "Exact Workflow Name"
```

### 4. Configuration Verification

**Symptom**: Unexpected configuration behavior

**Solutions**:

```bash
# Show current configuration
n8n-deploy env

# Show configuration in JSON
n8n-deploy env --json

# Check environment variables
echo $N8N_SERVER_URL
echo $N8N_DEPLOY_FLOWS_DIR
```

## 🔍 Debugging Techniques

### Verbose Mode
```bash
# Add verbose flag for detailed output
n8n-deploy --verbose <command>
```

### Environment Debugging
```bash
# Set testing environment variable
N8N_DEPLOY_TESTING=1 n8n-deploy <command>
```

## 📋 System Requirements Check

### Verify Python Version
```bash
python --version  # Should be 3.8+
```

### Check Dependencies
```bash
pip list | grep -E "n8n-deploy|click|rich|pydantic|requests"
```

## 🆘 Getting Help

### CLI Help
```bash
n8n-deploy --help
n8n-deploy wf --help
n8n-deploy apikey --help
```

### Online Resources

- [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues/)
- [Documentation](https://lehcode.github.io/n8n-deploy/)

{: .tip }
> **Tip**: Always use the latest version of n8n-deploy for bug fixes and new features.

{: .note }
> Use environment variables for consistent configuration across terminal sessions. Run `n8n-deploy env` to verify your settings.

## 🚧 Known Limitations

- Limited to n8n workflow management
- Requires API key for server operations
- No automatic workflow synchronization
- Supports SQLite backend only

## 📖 Related Guides

- [Configuration](configuration/)
- [Workflow Management](core-features/workflows/)
- [API Key Management](core-features/apikeys/)

## 🐛 Reporting Issues

1. Check existing GitHub issues
2. Collect relevant logs and configuration details
3. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - Python and n8n-deploy versions
   - System information
