---
layout: default
title: Workflow Patterns
parent: User Guide
nav_order: 2
description: "Common workflow management patterns in n8n-deploy"
---

# Workflow Management Patterns

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." — Martin Fowler

This guide demonstrates practical workflow management patterns using n8n-deploy.

## Basic Patterns

### Create New Workflow from Scratch

Create and deploy a brand new workflow that doesn't exist on any server yet:

```bash
# Create workflow JSON (no ID field needed)
cat > my-workflow.json << 'EOF'
{
  "name": "My New Workflow",
  "nodes": [
    {
      "parameters": {},
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [250, 300]
    }
  ],
  "connections": {},
  "active": false,
  "settings": {}
}
EOF

# Add to n8n-deploy (generates draft_xxx ID)
n8n-deploy wf add my-workflow.json --link-remote production
# Output: WARNING: No ID found. Generated draft ID: draft_abc123...

# Push to server (draft ID replaced with server-assigned ID)
n8n-deploy wf push draft_abc123
# Output: Updating draft ID draft_abc123 to server ID xYz789...
# Filename preserved (my-workflow.json stays my-workflow.json)

# Verify the new workflow
n8n-deploy wf list
```

{: .tip }
> After the first push, the database is updated with the permanent server-assigned ID. Your custom filename is preserved.

### Initialize New Project

Set up n8n-deploy for a new workflow project:

```bash
# Create project directory
mkdir ~/my-n8n-workflows
cd ~/my-n8n-workflows

# Set environment
export N8N_DEPLOY_FLOWS_DIR="$(pwd)"
export N8N_DEPLOY_DATA_DIR="$(pwd)/.n8n-deploy"

# Initialize database
n8n-deploy db init

# Verify setup
n8n-deploy db status
```

### Pull Workflows from Server

Fetch workflows from your n8n server:

```bash
# Add server API key
echo "your-api-key" | n8n-deploy apikey add production

# List available workflows on server
n8n-deploy --server-url https://n8n.example.com wf list-server

# Pull specific workflow (prompted for filename if new)
n8n-deploy --server-url https://n8n.example.com wf pull "Customer Onboarding"

# Pull with custom filename (skip prompt)
n8n-deploy wf pull "Customer Onboarding" --filename customer-onboarding.json

# Pull all workflows
for workflow in $(n8n-deploy wf list-server --no-emoji | grep -v "ID" | awk '{print $2}'); do
    n8n-deploy wf pull "$workflow"
done
```

### Push Workflows to Server

Deploy local workflows to n8n server:

```bash
# Push single workflow
n8n-deploy --server-url https://n8n.example.com wf push "Data Pipeline"

# Verify push success
n8n-deploy wf list --no-emoji | grep "Data Pipeline"

# Push with SSL verification disabled (self-signed certificates)
n8n-deploy --server-url https://n8n.local wf push "Internal Process" --skip-ssl-verify
```

## Advanced Patterns

### Multi-Environment Workflow Management

Manage workflows across development, staging, and production:

```bash
# Setup directory structure
mkdir -p ~/workflows/{dev,staging,prod}

# Configure environments
cat > ~/.env.dev << EOF
N8N_DEPLOY_FLOWS_DIR=~/workflows/dev
N8N_DEPLOY_DATA_DIR=~/workflows/dev/.n8n-deploy
N8N_SERVER_URL=https://dev.n8n.example.com
EOF

cat > ~/.env.staging << EOF
N8N_DEPLOY_FLOWS_DIR=~/workflows/staging
N8N_DEPLOY_DATA_DIR=~/workflows/staging/.n8n-deploy
N8N_SERVER_URL=https://staging.n8n.example.com
EOF

cat > ~/.env.prod << EOF
N8N_DEPLOY_FLOWS_DIR=~/workflows/prod
N8N_DEPLOY_DATA_DIR=~/workflows/prod/.n8n-deploy
N8N_SERVER_URL=https://n8n.example.com
EOF

# Use with environment switching
source ~/.env.dev
n8n-deploy wf list-server

source ~/.env.prod
n8n-deploy wf push "Stable Workflow"
```

### Version Control Strategy

Workflow files should be managed with git:

```bash
# Initialize git repository in workflow directory
cd /path/to/workflows
git init
git add *.json
git commit -m "Initial workflow commit"

# Regular workflow updates
git add updated_workflow.json
git commit -m "Updated customer onboarding workflow"
git push origin main

# Automated workflow backup with git
cat > ~/bin/n8n-git-backup.sh << 'EOF'
#!/bin/bash
cd /path/to/workflows
git add *.json
git commit -m "Auto-backup $(date +%Y%m%d-%H%M%S)" || true
git push origin main
EOF

chmod +x ~/bin/n8n-git-backup.sh

# Schedule with cron (daily at 2 AM)
echo "0 2 * * * ~/bin/n8n-git-backup.sh" | crontab -
```

> **Note**: Use `db backup` to backup database metadata, API keys, and server configurations separately.

### Workflow Search and Organization

Efficiently find and organize workflows:

```bash
# Search by name
n8n-deploy wf search "customer"

# List workflows with specific tags
n8n-deploy wf list --filter-tag production

# Show workflow statistics
n8n-deploy wf stats

# Export workflow list to CSV
n8n-deploy wf list --no-emoji --format csv > workflows.csv
```

### Batch Operations

Process multiple workflows efficiently:

```bash
# Add tags to multiple workflows
for workflow in "Order Processing" "Payment Gateway" "Email Notifications"; do
    n8n-deploy wf update "$workflow" --add-tag critical
done

# Update workflow status in batch
workflows=("Workflow A" "Workflow B" "Workflow C")
for wf in "${workflows[@]}"; do
    n8n-deploy wf update "$wf" --status active
done

# Pull workflows matching pattern
n8n-deploy wf list-server --no-emoji | \
    grep -i "api" | \
    awk '{print $2}' | \
    xargs -I {} n8n-deploy wf pull "{}"
```

## Integration Patterns

### Git Version Control

Track workflow changes in Git:

```bash
# Initialize Git in workflow directory
cd ~/my-n8n-workflows
git init

# Create .gitignore
cat > .gitignore << EOF
.n8n-deploy/
*.log
.env
EOF

# Commit workflows
git add *.json
git commit -m "feat: add initial workflows"

# Track workflow changes
git diff HEAD~1 HEAD -- "deAVBp391wvomsWY.json"
```

### CI/CD Integration

Automate workflow deployment in CI/CD pipelines:

```yaml
# .gitlab-ci.yml example
deploy:workflows:
  stage: deploy
  script:
    - pip install n8n-deploy
    - echo "$N8N_API_KEY" | n8n-deploy apikey add production
    - n8n-deploy --server-url "$N8N_SERVER_URL" wf push "Production Pipeline"
  only:
    - master
  tags:
    - python
```

### Script-Friendly Output

Use `--no-emoji` for automation:

```bash
# Parse workflow list in scripts
workflow_count=$(n8n-deploy wf list --no-emoji | grep -c "json")
echo "Total workflows: $workflow_count"

# Extract workflow IDs
n8n-deploy wf list --no-emoji | \
    awk '{print $1}' | \
    grep -E '^[a-zA-Z0-9]+$' > workflow_ids.txt

# JSON output for complex parsing
n8n-deploy wf list --format json | jq '.[] | select(.status == "active")'
```

## Troubleshooting Patterns

### Verify Server Connectivity

Test n8n server connection:

```bash
# Test API key
n8n-deploy apikey test production

# List server workflows (verifies connectivity)
n8n-deploy --server-url https://n8n.example.com wf list-server

# Debug with verbose output
n8n-deploy --server-url https://n8n.example.com wf list-server --debug
```

### Handle Workflow Conflicts

Resolve workflow synchronization issues:

```bash
# Check local vs server differences
n8n-deploy wf list --no-emoji > local.txt
n8n-deploy wf list-server --no-emoji > server.txt
diff local.txt server.txt

# Force pull (overwrite local)
n8n-deploy wf pull "Conflict Workflow" --force

# Force push (overwrite server)
n8n-deploy wf push "Conflict Workflow" --force
```

### Database Maintenance

Keep database healthy:

```bash
# Check database status
n8n-deploy db status

# Compact database (reclaim space)
n8n-deploy db compact

# Backup database before major changes
n8n-deploy db backup --name "pre-migration-$(date +%Y%m%d)"
```

## Best Practices

{: .tip }
> **Workflow Naming**: Use descriptive, consistent names with spaces and emojis supported

{: .tip }
> **Regular Backups**: Use git for workflow files, `db backup` for database metadata

{: .tip }
> **Environment Separation**: Maintain separate databases for dev/staging/prod

{: .warning }
> **API Key Security**: Never commit API keys to version control

## Performance Optimization

### Efficient Bulk Operations

```bash
# Parallel workflow pulls (requires GNU parallel)
n8n-deploy wf list-server --no-emoji | \
    awk '{print $2}' | \
    parallel -j 4 n8n-deploy wf pull {}

# Batch process with error handling
while IFS= read -r workflow; do
    n8n-deploy wf pull "$workflow" || echo "Failed: $workflow" >> failed.log
done < workflows.txt
```

### Reduce Database Size

```bash
# Delete inactive workflows from server and database
n8n-deploy wf list --filter-status inactive --no-emoji | \
    awk '{print $1}' | \
    xargs -I {} n8n-deploy wf delete {} --yes

# Compact after bulk deletions
n8n-deploy db compact
```

## Real-World Examples

### Daily Workflow Sync

```bash
#!/bin/bash
# sync-workflows.sh - Daily workflow synchronization

set -e

# Configuration
SERVER="https://n8n.example.com"
FLOW_DIR="$HOME/workflows"

# Pull latest from server
cd "$FLOW_DIR"
n8n-deploy --server-url "$SERVER" wf pull --all

# Commit to Git
git add *.json
git commit -m "sync: daily workflow update $(date +%Y-%m-%d)" || true
git push origin master

# Backup database metadata
n8n-deploy db backup
```

### Workflow Deployment Pipeline

```bash
#!/bin/bash
# deploy-workflows.sh - Deploy workflows to production

# Validate workflows locally
n8n-deploy wf list --no-emoji

# Run tests (custom validation)
./validate-workflows.sh

# Backup production database
n8n-deploy db backup

# Deploy
for workflow in $(cat deploy-list.txt); do
    echo "Deploying: $workflow"
    n8n-deploy --server-url "$PROD_SERVER" wf push "$workflow"
done

echo "Deployment complete"
```

---

{: .note }
> These patterns demonstrate how n8n-deploy integrates into real-world workflows. Adapt them to your specific needs and environment.
