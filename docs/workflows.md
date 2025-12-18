---
layout: default
title: Workflow Management
nav_order: 4
---

## Workflow Management

n8n-deploy provides comprehensive workflow management capabilities, allowing you to interact with n8n workflows seamlessly.

## 🌟 Workflow Operations

### List Workflows

#### Local Workflows
```bash
n8n-deploy wf list
```

#### Remote Server Workflows
```bash
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server
```

### Pull Workflow from Remote Server
```bash
# Pull specific workflow
n8n-deploy --server-url http://n8n.example.com:5678 wf pull "Customer Onboarding"

# Pull with custom flow directory
n8n-deploy --flow-dir /path/to/workflows wf pull "Customer Onboarding"
```

### Push Workflow to Remote Server
```bash
# Push specific workflow
n8n-deploy --server-url http://n8n.example.com:5678 wf push "Deployment Pipeline"

# Push with custom flow directory
n8n-deploy --flow-dir /path/to/workflows wf push "Deployment Pipeline"
```

### Script Synchronization

Sync external scripts (.js, .cjs, .py) referenced by Execute Command nodes alongside workflow push.

**Remote path formula:** `<scripts-base-path>/<workflow-name>/`

Example: With `--scripts-base-path=/opt/n8n/scripts` and workflow "My Workflow", scripts upload to `/opt/n8n/scripts/My_Workflow/`

```bash
# Push workflow with script sync
n8n-deploy wf push "My Workflow" \
  --scripts ./scripts \
  --scripts-host n8n.example.com \
  --scripts-user deploy \
  --scripts-key ~/.ssh/id_rsa

# Custom base path (default: /opt/n8n/scripts)
n8n-deploy wf push "My Workflow" \
  --scripts ./scripts \
  --scripts-base-path /mnt/n8n/local-files \
  --scripts-host n8n.example.com \
  --scripts-user deploy \
  --scripts-key ~/.ssh/id_rsa

# Dry run to preview without uploading
n8n-deploy wf push "My Workflow" --scripts ./scripts --dry-run

# Sync all scripts (ignore git change detection)
n8n-deploy wf push "My Workflow" --scripts ./scripts --scripts-all
```

**Environment variables:**
- `N8N_SCRIPTS_HOST`: Remote host
- `N8N_SCRIPTS_USER`: SSH username
- `N8N_SCRIPTS_PORT`: SSH port (default: 22)
- `N8N_SCRIPTS_KEY`: SSH key file path
- `N8N_SCRIPTS_BASE_PATH`: Base path on remote (default: /opt/n8n/scripts)

### Workflow Backup
```bash
# Backup all workflows
n8n-deploy wf backup

# Backup specific workflow
n8n-deploy wf backup "My Workflow"
```

### Workflow Restore
```bash
# Restore from backup
n8n-deploy wf restore backup_file.tar.gz
```

## 🔍 Advanced Workflow Management

### Search Workflows
```bash
# Search workflows by name or tag
n8n-deploy wf search "customer"
```

### Workflow Statistics
```bash
# Show workflow statistics
n8n-deploy wf stats
```

## 💡 Pro Tips

- Use quotes for workflow names with spaces
- Leverage `--no-emoji` flag for scripting
- Keep workflow files organized in a consistent directory

## 🧩 Workflow File Management

### Workflow File Location
- Stored as JSON files
- Named by n8n workflow ID
- Can be stored in custom directories

### Workflow Status Tracking
- Workflows tracked in SQLite database
- Metadata includes:
  - Workflow name
  - File path
  - Timestamps
  - Tags

## 🆘 Troubleshooting

- Verify server URL and API key
- Check file permissions
- Ensure workflow names are exact
- Use `--skip-ssl-verify` for self-signed certificates

## 📖 Related Guides

- [Configuration](configuration.md)
- [API Key Management](apikeys.md)
- [Troubleshooting](troubleshooting.md)

## 💻 Example Workflow Management Scenario

```bash
# Add API key for server
echo "your-api-key" | n8n-deploy apikey add my_server

# List remote workflows
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Pull a specific workflow
n8n-deploy wf pull "Customer Onboarding"

# Backup all workflows
n8n-deploy wf backup

# Search workflows
n8n-deploy wf search "customer"
```