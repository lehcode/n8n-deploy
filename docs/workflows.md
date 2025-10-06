---
layout: default
title: Workflow Management
nav_order: 5
description: "Managing n8n workflows with n8n-deploy"
---

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

{: .tip }
> **Tip**: Always use quotes for workflow names with spaces. Example: `n8n-deploy wf pull "Customer Onboarding"`

{: .note }
> Leverage the `--no-emoji` flag for scripting to get clean, parseable output.

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

- [Configuration](configuration/)
- [API Key Management](apikeys/)
- [Troubleshooting](troubleshooting/)

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
