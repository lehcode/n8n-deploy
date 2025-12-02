---
layout: default
title: Workflow Management
parent: Core Features
nav_order: 3
has_children: false
description: "Managing n8n workflows with n8n-deploy"
---

# Workflow Management

n8n-deploy provides comprehensive workflow management capabilities, allowing you to interact with n8n workflows seamlessly.

## 🆕 Adding New Workflows

n8n-deploy supports adding workflows that don't have a server-assigned ID yet. This is common when:

- Creating new workflows from scratch
- Exporting workflows from the n8n UI (which may not include the server ID)

### How It Works

1. **Add workflow without ID** - Tool generates a temporary `draft_{uuid}` ID
2. **Push to server** - Server assigns a permanent ID
3. **Automatic update** - Draft ID replaced with server ID, file renamed

```bash
# Add workflow without ID (generates draft_xxx temporary ID)
n8n-deploy wf add my-workflow.json --link-remote production
# Output: WARNING: No ID found. Generated draft ID: draft_abc123...

# Push to server (replaces draft ID with server-assigned ID)
n8n-deploy wf push draft_abc123 --remote production
# Output: Updating draft ID to server ID xYz789...
# Filename preserved: my-workflow.json (not renamed)
```

{: .note }
> The draft ID is temporary. After your first push, the database entry is updated with the permanent server-assigned ID. Your custom filename is preserved.

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

# Pull with custom filename (for new workflows)
n8n-deploy wf pull "Customer Onboarding" --filename customer-onboarding.json

# Pull with custom flow directory
n8n-deploy --flow-dir /path/to/workflows wf pull "Customer Onboarding"
```

{: .note }
> When pulling a new workflow, you'll be prompted to enter a filename. Use `--filename` to specify it directly.

### Push Workflow to Remote Server

```bash
# Push by workflow name
n8n-deploy wf push "Deployment Pipeline" --remote production

# Push by workflow ID
n8n-deploy wf push deAVBp391wvomsWY --remote production

# Push by filename
n8n-deploy wf push my-workflow.json --remote production
```

{: .tip }
> **Workflow Resolution**: The push command accepts workflow ID, name, or filename. Resolution priority: ID → Name → Filename.

{: .note }
> Workflow files should be managed with version control (git). Use `db backup` for database metadata, API keys, and server configurations.

### Delete Workflow

Remove a workflow from both the n8n server and the local database:

```bash
# Delete by workflow name
n8n-deploy wf delete "Customer Onboarding"

# Delete by workflow ID
n8n-deploy wf delete deAVBp391wvomsWY

# Delete by filename
n8n-deploy wf delete my-workflow.json

# Skip confirmation prompt
n8n-deploy wf delete "Customer Onboarding" --yes

# Override server
n8n-deploy wf delete workflow-name --remote staging

# Self-signed certificates
n8n-deploy wf delete workflow-name --skip-ssl-verify
```

{: .warning }
> The `wf delete` command removes the workflow from the n8n server first, then from the local database. The JSON file is NOT deleted - you manage files yourself (via git).

{: .note }
> **Draft workflows**: Workflows with draft IDs (`draft_*`) are only removed from the database since they don't exist on any server yet.

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

### Custom Filenames

Workflows can use any filename you choose:

```bash
# Add workflow with custom filename (preserved)
n8n-deploy wf add my-descriptive-name.json

# Push using the filename
n8n-deploy wf push my-descriptive-name.json --remote production
```

{: .note }
> Filenames are preserved - `my-workflow.json` stays `my-workflow.json`, not renamed to `{id}.json`.

### Workflow Status Tracking

- Workflows tracked in SQLite database
- Metadata includes:
  - Workflow name
  - Custom filename (`file` column)
  - File folder location
  - Timestamps
  - Server linkage

## 🆘 Troubleshooting

- Verify server URL and API key
- Check file permissions
- Ensure workflow names are exact
- Use `--skip-ssl-verify` for self-signed certificates

{: .note }
> **Push operations**: Read-only fields are automatically stripped before sending to n8n server. See [Troubleshooting](/n8n-deploy/troubleshooting/) for details.

## 📖 Related Guides

- [Configuration](/n8n-deploy/configuration/)
- [API Key Management](/n8n-deploy/core-features/apikeys/)
- [Troubleshooting](/n8n-deploy/troubleshooting/)

## 💻 Example Workflow Management Scenario

```bash
# Add API key for server
echo "your-api-key" | n8n-deploy apikey add my_server

# List remote workflows
n8n-deploy --server-url http://n8n.example.com:5678 wf list-server

# Pull a specific workflow
n8n-deploy wf pull "Customer Onboarding"

# Search workflows
n8n-deploy wf search "customer"
```
