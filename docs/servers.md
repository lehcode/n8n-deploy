---
layout: default
title: Server Management
nav_order: 5
description: "Managing n8n server connections and configurations"
---

# Server Management

> "If you can't manage one server, adding more won't help." — Murphy's Law of Distributed Systems

n8n-deploy enables management of multiple n8n server connections, each with dedicated API keys and configurations for seamless multi-environment workflows.

## 🎯 Overview

Server management in n8n-deploy provides:
- **Multi-Server Support**: Connect to development, staging, and production n8n instances
- **Server-Key Linking**: Associate specific API keys with servers
- **UTF-8 Names**: Use descriptive names with international characters and emojis
- **Active/Inactive States**: Toggle server availability without deletion
- **Centralized Configuration**: All servers managed from single database

---

## 🖥️ Server Operations

### Create Server

Register a new n8n server:

```bash
# Basic server creation
n8n-deploy server create "Production" http://n8n.example.com:5678

# UTF-8 server names with emojis
n8n-deploy server create "Production 🚀" https://n8n-prod.company.com
n8n-deploy server create "Dev 🔧" http://localhost:5678
n8n-deploy server create "Staging 🧪" http://n8n-staging:5678

# Create and link API key in one workflow
n8n-deploy server create "QA Server" http://n8n-qa:5678
echo "$QA_API_KEY" | n8n-deploy apikey add - --name qa_key --server "QA Server"
```

**Server naming guidelines:**
- UTF-8 characters supported (emojis, international text)
- No path separators (/, \)
- Must be unique across all servers
- Descriptive names recommended

{: .tip }
> **Pro Tip**: Use emojis to quickly identify server environments: 🚀 Production, 🧪 Staging, 🔧 Development

### List Servers

View all configured servers:

```bash
# All servers (rich output)
n8n-deploy server list

# Active servers only
n8n-deploy server list --active

# Script-friendly output
n8n-deploy server list --no-emoji

# JSON format
n8n-deploy server list --json

# Table format (default)
n8n-deploy server list --table
```

**Example output:**
```
🖥️  n8n Servers

┌─────────────────────┬────────────────────────────────┬────────┬─────────────────────┬─────────────┐
│ Name                │ URL                            │ Status │ Created             │ Last Used   │
├─────────────────────┼────────────────────────────────┼────────┼─────────────────────┼─────────────┤
│ Production 🚀       │ https://n8n.example.com        │ ✅ Active │ 2025-09-01 10:00:00 │ 2025-10-05  │
│ Staging 🧪          │ http://n8n-staging:5678        │ ✅ Active │ 2025-09-15 14:30:00 │ 2025-10-03  │
│ Dev 🔧              │ http://localhost:5678          │ ✅ Active │ 2025-09-20 09:00:00 │ 2025-10-06  │
│ Old Server          │ http://legacy.n8n.old          │ ⭕ Inactive │ 2025-01-10 08:00:00 │ 2025-08-20  │
└─────────────────────┴────────────────────────────────┴────────┴─────────────────────┴─────────────┘

Total: 4 servers (3 active)
```

### View Server API Keys

Display all API keys linked to a server:

```bash
# View keys for server
n8n-deploy server keys "Production 🚀"

# JSON output
n8n-deploy server keys "Staging 🧪" --json

# Table format
n8n-deploy server keys "Dev 🔧" --table
```

**Example output:**
```
🔑 API Keys for Server: Production 🚀

┌─────────────────┬─────────────────────┬─────────────────────┐
│ Key Name        │ Created             │ Linked              │
├─────────────────┼─────────────────────┼─────────────────────┤
│ prod_admin      │ 2025-09-01 10:30:00 │ 2025-09-01 10:31:00 │
│ prod_readonly   │ 2025-09-15 14:00:00 │ 2025-09-15 14:05:00 │
│ ci_deploy       │ 2025-10-01 08:00:00 │ 2025-10-01 08:01:00 │
└─────────────────┴─────────────────────┴─────────────────────┘

Total: 3 keys linked
```

### Remove Server

Delete a server from configuration:

```bash
# Remove with confirmation prompt
n8n-deploy server remove "Old Server"

# Skip confirmation
n8n-deploy server remove "Temp Server" --confirm

# Preserve linked API keys (default)
n8n-deploy server remove "Staging 🧪" --preserve-keys

# Delete keys only used by this server
n8n-deploy server remove "Dev 🔧" --delete-keys --confirm
```

**Removal behavior:**
- `--preserve-keys` (default): Keeps all linked API keys intact
- `--delete-keys`: Deletes API keys used **exclusively** by this server
- Shared keys are never deleted automatically

{: .warning }
> **Important**: Removing a server does not affect workflow files or database workflows. Only the server configuration is deleted.

---

## 🔗 Server-API Key Management

### Linking Workflow

Associate API keys with servers for automatic authentication:

```bash
# Method 1: Link during API key creation
echo "$API_KEY" | n8n-deploy apikey add - --name prod_key --server "Production 🚀"

# Method 2: Link during server creation
n8n-deploy server create "Staging" http://staging.n8n.com
echo "$STAGING_KEY" | n8n-deploy apikey add - --name staging_key --server "Staging"

# Method 3: Create both explicitly
n8n-deploy server create "QA" http://qa.n8n.internal:5678
echo "$QA_KEY" | n8n-deploy apikey add - --name qa_key
# Link via server link command (if available)
```

### Multi-Key Scenarios

Servers can have multiple API keys for different purposes:

```bash
# Production server with multiple keys
n8n-deploy server create "Production 🚀" https://n8n-prod.com

# Admin key (full access)
echo "$ADMIN_KEY" | n8n-deploy apikey add - --name prod_admin --server "Production 🚀"

# Read-only key (monitoring)
echo "$READONLY_KEY" | n8n-deploy apikey add - --name prod_readonly --server "Production 🚀"

# CI/CD key (deployment only)
echo "$CI_KEY" | n8n-deploy apikey add - --name prod_ci --server "Production 🚀"

# View all keys
n8n-deploy server keys "Production 🚀"
```

---

## 🏗️ Real-World DevOps Scenarios

### Scenario 1: Complete Multi-Environment Setup

Setup for enterprise DevOps team:

```bash
#!/bin/bash
# setup-environments.sh

# Initialize database
n8n-deploy db init

# Development Environment
n8n-deploy server create "Development 🔧" http://n8n-dev.internal:5678
echo "$DEV_KEY" | n8n-deploy apikey add - --name dev_team --server "Development 🔧"

# QA Environment
n8n-deploy server create "QA 🧪" http://n8n-qa.internal:5678
echo "$QA_KEY" | n8n-deploy apikey add - --name qa_automation --server "QA 🧪"

# Staging Environment
n8n-deploy server create "Staging 🎭" https://n8n-staging.company.com
echo "$STAGING_ADMIN_KEY" | n8n-deploy apikey add - --name staging_admin --server "Staging 🎭"
echo "$STAGING_READONLY_KEY" | n8n-deploy apikey add - --name staging_readonly --server "Staging 🎭"

# Production Environment
n8n-deploy server create "Production 🚀" https://n8n.company.com
echo "$PROD_ADMIN_KEY" | n8n-deploy apikey add - --name prod_admin --server "Production 🚀"
echo "$PROD_READONLY_KEY" | n8n-deploy apikey add - --name prod_readonly --server "Production 🚀"
echo "$PROD_CI_KEY" | n8n-deploy apikey add - --name prod_ci --server "Production 🚀"

# Verify configuration
echo "=== Servers ==="
n8n-deploy server list --no-emoji

echo -e "\n=== API Keys ==="
n8n-deploy apikey list --no-emoji

echo -e "\n=== Production Keys ==="
n8n-deploy server keys "Production 🚀" --no-emoji
```

### Scenario 2: Environment Migration

Migrate workflows from staging to production:

```bash
#!/bin/bash
# migrate-to-production.sh

WORKFLOW_NAME="Customer Onboarding"
STAGING_SERVER="Staging 🎭"
PROD_SERVER="Production 🚀"

# Pull from staging
n8n-deploy --server-url "$(n8n-deploy server list --json | jq -r ".[] | select(.name==\"$STAGING_SERVER\") | .url")" wf pull "$WORKFLOW_NAME"

# Push to production
n8n-deploy --server-url "$(n8n-deploy server list --json | jq -r ".[] | select(.name==\"$PROD_SERVER\") | .url")" wf push "$WORKFLOW_NAME"

echo "✓ Workflow migrated: $STAGING_SERVER → $PROD_SERVER"
```

### Scenario 3: Server Health Monitoring

Automated health checks for all servers:

```bash
#!/bin/bash
# health-check.sh

SERVERS=$(n8n-deploy server list --json --no-emoji)

echo "$SERVERS" | jq -r '.[] | select(.is_active==true) | .name' | while read -r SERVER; do
    echo "Checking $SERVER..."

    # Get server URL
    SERVER_URL=$(echo "$SERVERS" | jq -r ".[] | select(.name==\"$SERVER\") | .url")

    # Check connectivity
    if curl -sf "$SERVER_URL/healthz" > /dev/null 2>&1; then
        echo "  ✓ $SERVER is healthy ($SERVER_URL)"
    else
        echo "  ✗ $SERVER is unreachable ($SERVER_URL)"
        # Send alert notification
        # notify-team.sh "$SERVER is down"
    fi
done
```

### Scenario 4: Temporary Test Server

Create and cleanup temporary server for testing:

```bash
#!/bin/bash
# temp-test-server.sh

# Create temporary server
TEST_SERVER="Temp Test $(date +%Y%m%d_%H%M%S)"
n8n-deploy server create "$TEST_SERVER" http://localhost:5678

# Add temporary API key
echo "$TEMP_KEY" | n8n-deploy apikey add - --name temp_key --server "$TEST_SERVER"

# Run tests
./run-integration-tests.sh "$TEST_SERVER"

# Cleanup
n8n-deploy server remove "$TEST_SERVER" --delete-keys --confirm
echo "✓ Temporary server cleaned up"
```

### Scenario 5: Blue-Green Deployment

Manage blue-green server deployments:

```bash
#!/bin/bash
# blue-green-deployment.sh

# Current production (Blue)
BLUE_SERVER="Production Blue 🔵"
BLUE_URL="https://n8n-blue.company.com"

# New production (Green)
GREEN_SERVER="Production Green 🟢"
GREEN_URL="https://n8n-green.company.com"

# Setup green environment
n8n-deploy server create "$GREEN_SERVER" "$GREEN_URL"
echo "$PROD_KEY" | n8n-deploy apikey add - --name green_key --server "$GREEN_SERVER"

# Deploy to green
n8n-deploy --server-url "$GREEN_URL" wf push "Critical Workflow"

# Health check green
if n8n-deploy apikey test green_key; then
    echo "✓ Green environment healthy"

    # Switch traffic (external load balancer update)
    # update-load-balancer.sh "$GREEN_URL"

    # Mark blue as inactive (keep for rollback)
    echo "Blue environment kept for rollback"
else
    echo "✗ Green deployment failed, keeping blue active"
    n8n-deploy server remove "$GREEN_SERVER" --delete-keys --confirm
    exit 1
fi
```

---

## 🔒 Security Considerations

### Server URL Security

Protect server URLs in documentation and logs:

```bash
# Good: Reference by name
n8n-deploy server keys "Production 🚀"

# Bad: Hardcoded URLs in scripts
# n8n-deploy --server-url https://secret-server.internal:5678
```

### Access Control

Implement least-privilege principle:

```bash
# Developers: read-only production access
n8n-deploy server create "Production (RO)" https://n8n.company.com
echo "$READONLY_KEY" | n8n-deploy apikey add - --name dev_readonly --server "Production (RO)"

# DevOps: full access
echo "$ADMIN_KEY" | n8n-deploy apikey add - --name devops_admin --server "Production (RO)"
```

### Audit Logging

Track server access and modifications:

```bash
# Log all server operations
LOG_FILE="/var/log/n8n-deploy/servers.log"

function log_operation() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

log_operation "Server created: $SERVER_NAME by $USER"
n8n-deploy server create "$SERVER_NAME" "$SERVER_URL"
```

---

## 📊 Server Database Schema

```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,                -- Server URL (e.g., http://n8n.example.com:5678)
    name TEXT NOT NULL UNIQUE,        -- Server name (UTF-8 supported)
    is_active INTEGER DEFAULT 1,      -- Active status (1=active, 0=inactive)
    created_at TIMESTAMP NOT NULL,    -- Creation timestamp
    last_used TIMESTAMP               -- Last connection timestamp
);

CREATE TABLE server_api_keys (
    server_id INTEGER NOT NULL,
    api_key_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (server_id, api_key_id),
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
);
```

**Relationships:**
- Servers can have multiple API keys (one-to-many)
- API keys can be linked to multiple servers (many-to-many via junction table)
- Deleting a server cascades to `server_api_keys` but preserves `api_keys`

---

## 🆘 Troubleshooting

### Server Already Exists

**Error**: `UNIQUE constraint failed: servers.name`

**Solutions**:
```bash
# List existing servers
n8n-deploy server list

# Remove old server
n8n-deploy server remove "Conflicting Name" --confirm

# Use different name
n8n-deploy server create "Staging v2" http://n8n-staging:5678
```

### Connection Refused

**Error**: `Failed to connect to server`

**Diagnosis**:
```bash
# Check server URL
n8n-deploy server list --json | jq -r '.[] | select(.name=="Production") | .url'

# Test connectivity
SERVER_URL=$(n8n-deploy server list --json | jq -r '.[] | select(.name=="Production") | .url')
curl -I "$SERVER_URL"

# Verify n8n is running
curl "$SERVER_URL/healthz"
```

**Solutions**:
- Verify server URL is correct (protocol, hostname, port)
- Check firewall rules
- Ensure n8n service is running
- Validate network connectivity

### No API Keys Linked

**Error**: `No API keys linked to server 'XYZ'`

**Solutions**:
```bash
# List available API keys
n8n-deploy apikey list

# Link existing key
echo "$API_KEY" | n8n-deploy apikey add - --name key_for_xyz --server "XYZ"

# Verify linking
n8n-deploy server keys "XYZ"
```

### Server Not Found

**Error**: `Server 'XYZ' not found`

**Solutions**:
```bash
# List all servers (check spelling, case-sensitivity)
n8n-deploy server list

# Server names are case-sensitive
n8n-deploy server keys "Production"    # ✓ Correct
n8n-deploy server keys "production"    # ✗ Wrong case
```

---

## 📖 Related Documentation

- [API Key Management](apikeys/) - Manage authentication keys
- [Database Management](database/) - Database operations and backups
- [Workflow Management](workflows/) - Push/pull workflows using servers
- [Configuration](configuration/) - Environment variables and settings
- [Troubleshooting](troubleshooting/) - Common issues and solutions

---

## 💡 Pro Tips

1. **Emoji Conventions**: Establish team standards (🚀 prod, 🧪 staging, 🔧 dev)
2. **Descriptive Names**: Include purpose and environment (`prod_admin`, `staging_readonly`)
3. **Multi-Key Strategy**: Use separate keys for different access levels
4. **Regular Audits**: Review `last_used` timestamps monthly
5. **Inactive Cleanup**: Remove unused servers to reduce clutter
6. **URL Consistency**: Use HTTPS for production, HTTP for local/dev
7. **Health Monitoring**: Automate connectivity checks
8. **Blue-Green Support**: Keep old servers inactive for rollback scenarios
9. **Documentation**: Maintain inventory of servers and their purposes
10. **Backup Database**: Server configurations stored only in database

---

## 🎯 Quick Command Reference

| Operation | Command |
|-----------|---------|
| Create server | `n8n-deploy server create "Name" URL` |
| List servers | `n8n-deploy server list` |
| Active servers | `n8n-deploy server list --active` |
| Server keys | `n8n-deploy server keys "Name"` |
| Remove server | `n8n-deploy server remove "Name"` |
| JSON output | `n8n-deploy server list --json` |

---

**Last Updated**: October 2025
**Feature Status**: Stable (v2.x)
