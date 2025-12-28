---
layout: default
title: Troubleshooting
nav_order: 5
description: "Common issues and solutions for n8n-deploy"
---

This guide helps you resolve common issues when using n8n-deploy.

## Common Problems and Solutions

### 1. API Key Issues

**Symptom**: Unable to connect to n8n server

**Solutions**:

```bash
# Test API key
n8n-deploy apikey test my_key

# Verify with verbose output
n8n-deploy -v apikey test my_key

# List linked servers
n8n-deploy server list
```

{: .tip }
> If your workflow is linked to a server (`wf add --link-remote`), the API key is used automatically.

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

# Specify custom data directory
n8n-deploy db init --data-dir ~/.n8n-deploy
```

### 3. Workflow Pull/Push Failures

**Symptom**: Cannot pull or push workflows

{: .note }
> **Read-only fields**: n8n-deploy automatically strips read-only fields (`id`, `triggerCount`, `updatedAt`, `createdAt`, `versionId`, `staticData`, `tags`, `meta`) before push operations.

**Solutions**:

```bash
# If workflow is linked to server, just use the name
n8n-deploy wf push my-workflow

# Override server if needed
n8n-deploy wf push my-workflow --remote staging

# Check linked server
n8n-deploy wf list

# For self-signed certificates, configure SSL once
n8n-deploy server ssl production --skip-verify

# Or use per-command flag
n8n-deploy wf push my-workflow --skip-ssl-verify
```

### 4. SSL Certificate Issues

**Symptom**: SSL verification errors with self-signed certificates

**Solutions**:

```bash
# Configure SSL setting per server (persistent)
n8n-deploy server ssl production --skip-verify

# Or use per-command flag (one-time)
n8n-deploy wf push my-workflow --skip-ssl-verify

# Re-enable verification
n8n-deploy server ssl production --verify
```

{: .warning }
> Skipping SSL verification reduces security. Use only for trusted internal servers with self-signed certificates.

### 5. Configuration Verification

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
echo $N8N_DEPLOY_DATA_DIR
```

### 6. Folder Sync Issues

**Symptom**: Cannot sync folders or authentication fails

**Solutions**:

```bash
# Authenticate with n8n server first
n8n-deploy folder auth myserver --email user@example.com

# Or use browser cookie (DevTools → Application → Cookies → n8n-auth)
n8n-deploy folder auth myserver --cookie "n8n-auth=..."

# List folders to verify connection
n8n-deploy folder list --remote myserver

# Use dry-run to preview changes
n8n-deploy folder sync --dry-run
```

{: .note }
> Folder sync uses n8n's internal API (cookie-based auth), which is different from the public API (API key auth). You must authenticate separately for folder operations.

## Debugging Techniques

### Verbose Mode

n8n-deploy supports two levels of verbosity for debugging:

```bash
# Basic verbose - shows HTTP requests and operations
n8n-deploy -v wf push my-workflow

# Extended verbose - shows request/response details and timing
n8n-deploy -vv wf push my-workflow

# Verbose flag works at root or subcommand level
n8n-deploy -v wf push my-workflow    # Root level
n8n-deploy wf -v push my-workflow    # Subcommand level
n8n-deploy db -vv status             # Works on any subcommand
```

### Environment Debugging
```bash
# Set testing environment variable
N8N_DEPLOY_TESTING=1 n8n-deploy <command>
```

## System Requirements Check

### Verify Python Version
```bash
python --version  # Should be 3.9+
```

### Check Dependencies
```bash
pip list | grep -E "n8n-deploy|click|rich|pydantic|requests"
```

## Getting Help

### CLI Help
```bash
n8n-deploy --help
n8n-deploy wf --help
n8n-deploy wf push --help
n8n-deploy server ssl --help
```

### Online Resources

- [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues/)
- [Documentation](https://lehcode.github.io/n8n-deploy/)

{: .tip }
> Always use the latest version of n8n-deploy for bug fixes and new features.

## Known Limitations

- Requires API key for server operations
- Folder sync requires separate cookie-based authentication
- Supports SQLite backend only

## Related Guides

- [Configuration](configuration/)
- [Workflow Management](core-features/workflows/)
- [Server Management](core-features/servers/)
- [Folder Synchronization](core-features/folders/)
- [API Key Management](core-features/apikeys/)

## Reporting Issues

1. Check existing GitHub issues
2. Collect relevant logs and configuration details
3. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - Python and n8n-deploy versions
   - System information
