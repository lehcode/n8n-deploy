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
n8n-deploy wf list-server --remote http://n8n.example.com:5678
```

### Pull Workflow from Remote Server
```bash
# Pull specific workflow
n8n-deploy wf pull "Customer Onboarding" --remote http://n8n.example.com:5678

# Pull multiple workflows at once (NEW in v0.9.0)
n8n-deploy wf pull wf1 wf2 wf3 --remote http://n8n.example.com:5678

# Pull with custom flow directory
n8n-deploy wf pull "Customer Onboarding" --remote http://n8n.example.com:5678 --flow-dir /path/to/workflows

# Non-interactive mode (uses default filenames, no prompts)
n8n-deploy wf pull wf1 wf2 --remote production --non-interactive
```

### Push Workflow to Remote Server
```bash
# Push specific workflow
n8n-deploy wf push "Deployment Pipeline" --remote http://n8n.example.com:5678

# Push multiple workflows at once (NEW in v0.9.0)
n8n-deploy wf push wf1 wf2 wf3 --remote http://n8n.example.com:5678

# Push with custom flow directory
n8n-deploy wf push "Deployment Pipeline" --remote http://n8n.example.com:5678 --flow-dir /path/to/workflows
```

**Multi-workflow output example:**
```text
[1/3] Processing: wf1
Pushed workflow 'wf1' to server

[2/3] Processing: wf2
Pushed workflow 'wf2' to server

[3/3] Processing: wf3
Pushed workflow 'wf3' to server

=== Push Summary ===
  OK   wf1
  OK   wf2
  OK   wf3

All 3 workflow(s) pushed successfully
```

### Delete Workflow

Remove a workflow from the n8n server and/or local database. At least one flag is required.

```bash
# Remove from database only (untrack)
n8n-deploy wf delete "Customer Onboarding" --db

# Delete from server only (keep in database)
n8n-deploy wf delete "Customer Onboarding" --server

# Delete from both server and database
n8n-deploy wf delete "Customer Onboarding" --db --server

# Skip confirmation prompt
n8n-deploy wf delete "Customer Onboarding" --db --server --yes

# Override server
n8n-deploy wf delete workflow-name --server --remote staging

# Self-signed certificates
n8n-deploy wf delete workflow-name --server --skip-ssl-verify
```

**Important Notes:**
- The local JSON file is NEVER deleted
- Draft workflows (starting with `draft_*`) are only removed from database (they don't exist on server)
- At least one of `--db` or `--server` must be specified

### Smart Workflow Lookup

All workflow commands support flexible name matching (new in v0.9.0):

```bash
# All of these resolve to the same workflow "My Workflow"
n8n-deploy wf push "My Workflow"      # Exact name
n8n-deploy wf push "my workflow"      # Case-insensitive
n8n-deploy wf push my-workflow        # Slug-style (hyphens)
n8n-deploy wf push my_workflow        # Slug-style (underscores)
n8n-deploy wf push my-workflow.json   # Filename lookup
```

**Lookup Priority:**
1. Workflow ID (exact match)
2. Workflow name (exact match)
3. Case-insensitive name match
4. Slug-style match (converts spaces/dashes/underscores)
5. Filename match (auto-appends .json if missing)

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
# Create server and add API key
n8n-deploy server create my_server http://n8n.example.com:5678
echo "your-api-key" | n8n-deploy apikey add - --name my_key --server my_server

# List remote workflows
n8n-deploy wf list-server --remote my_server

# Pull a specific workflow
n8n-deploy wf pull "Customer Onboarding" --remote my_server

# Backup all workflows
n8n-deploy wf backup

# Search workflows
n8n-deploy wf search "customer"
```