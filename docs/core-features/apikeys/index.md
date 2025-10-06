---
layout: default
title: API Key Management
parent: Core Features
nav_order: 4
has_children: false
description: "Managing API keys for n8n server access"
---

# API Key Management

n8n-deploy provides streamlined API key management for authenticating with n8n servers across multiple environments.

## 🎯 Overview

API keys in n8n-deploy serve as authentication tokens for n8n server operations:

- **Push/Pull Workflows**: Sync workflows with remote servers
- **Server Management**: Link keys to specific server instances
- **Multi-Environment Support**: Manage separate keys for dev/staging/prod
- **Plain Text Storage**: Simplified storage in SQLite (secure your database file!)

{: .note }
> API keys are **n8n JWT tokens** generated from the n8n web interface under Settings → API.

---

## 🔑 API Key Operations

### Add API Key

Store an API key with a memorable name:

```bash
# Interactive input (recommended for security)
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | n8n-deploy apikey add - --name production_key

# Direct input (visible in shell history)
n8n-deploy apikey add "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --name staging_key

# Link to server during creation
n8n-deploy apikey add - --name prod_key --server "Production Server 🚀"

# Add with description
n8n-deploy apikey add - --name dev_key --description "Development environment key"

# Auto-link to server from environment
N8N_SERVER_URL=http://n8n.local:5678 n8n-deploy apikey add - --name local_key
```

**Options:**

- `--name`: Unique identifier (supports UTF-8, emojis)
- `--server`: Link to specific server (creates server if doesn't exist)
- `--description`: Optional documentation string

{: .tip }
> **Pro Tip**: Use descriptive names like `prod_readonly` or `staging_admin` to indicate environment and permission level.

### List API Keys

View all stored API keys:

```bash
# Rich emoji output (credentials masked)
n8n-deploy apikey list

# Script-friendly output (credentials masked)
n8n-deploy apikey list --no-emoji

# Display actual credentials (SECURITY WARNING: use with extreme caution)
n8n-deploy apikey list --unmask

# JSON format for parsing
n8n-deploy apikey list --json
```

**Output includes:**

- Key name and description
- Creation timestamp
- Last used timestamp
- Active/inactive status
- Linked servers (if any)
- API key credentials (only with `--unmask` flag)

**Example output (credentials masked by default):**

```text
🔑 API Keys

┌────────────────────┬─────────────────────┬──────────────┬────────────┐
│ Name               │ Created             │ Last Used    │ Status     │
├────────────────────┼─────────────────────┼──────────────┼────────────┤
│ production_key     │ 2025-09-15 10:30:00 │ 2025-10-05   │ ✅ Active  │
│ staging_key        │ 2025-09-20 14:15:00 │ 2025-10-01   │ ✅ Active  │
│ dev_key            │ 2025-10-01 08:00:00 │ Never        │ ✅ Active  │
│ old_key            │ 2025-08-01 12:00:00 │ 2025-08-15   │ 🚫 Inactive│
└────────────────────┴─────────────────────┴──────────────┴────────────┘
```

{: .warning }
> **Security Warning**: The `--unmask` flag displays actual API credentials. Use only when absolutely necessary and never in logs, shared terminals, or automated scripts.

### Test API Key

Validate an API key against an n8n server:

```bash
# Test key validity
n8n-deploy apikey test production_key

# Test with specific server
n8n-deploy --server-url http://n8n.example.com:5678 apikey test staging_key
```

**What testing checks:**

- Key format (JWT structure)
- Server connectivity
- Authentication success
- Token expiration status

**Example output:**

```text
🧪 Testing API key: production_key

✓ Key format valid
✓ Server reachable (http://n8n.example.com:5678)
✓ Authentication successful
✓ Token expires: 2025-12-31

✅ API key is valid and working
```

### Deactivate API Key

Soft-delete a key (keeps in database but marks inactive):

```bash
# Deactivate key
n8n-deploy apikey deactivate old_key

# Confirm deactivation
n8n-deploy apikey list | grep old_key
```

{: .note }
> Deactivated keys remain in database for audit purposes but cannot be used for operations.

### Delete API Key

Permanently remove an API key:

```bash
# Delete with confirmation prompt
n8n-deploy apikey delete old_key

# Force delete without confirmation
n8n-deploy apikey delete temp_key --confirm

# Delete and unlink from all servers
n8n-deploy apikey delete staging_key --confirm
```

{: .warning }
> **Permanent Action**: Deleted keys cannot be recovered. Ensure you have backups or can regenerate from n8n.

---

## 🔗 Server-Key Association

### Linking Keys to Servers

API keys can be associated with specific servers for automatic authentication:

```bash
# Link existing key to server
n8n-deploy server link production_key "Production Server"

# Add key and link in one command
n8n-deploy apikey add - --name prod_key --server "Production Server"

# View keys linked to server
n8n-deploy server keys "Production Server"
```

**Benefits of linking:**

- **Automatic authentication**: No need to specify key for each operation
- **Multi-server support**: Different keys for different environments
- **Organized management**: Group keys by server purpose

### Multi-Environment Workflow

Typical setup for DevOps teams:

```bash
# Development Environment
n8n-deploy server create http://n8n-dev.internal:5678 --name "Development"
n8n-deploy apikey add - --name dev_key --server "Development"

# Staging Environment
n8n-deploy server create http://n8n-staging.internal:5678 --name "Staging"
n8n-deploy apikey add - --name staging_key --server "Staging"

# Production Environment
n8n-deploy server create https://n8n.example.com --name "Production 🚀"
n8n-deploy apikey add - --name prod_key --server "Production 🚀"

# List all configurations
n8n-deploy server list
n8n-deploy apikey list
```

---

## 🛡️ Security Best Practices

### Storage Security

API keys are stored in **plain text** within the SQLite database. Protect your database:

```bash
# Set restrictive permissions
chmod 600 ~/.n8n-deploy/n8n-deploy.db
chmod 700 ~/.n8n-deploy

# For multi-user systems
chown $USER:$USER ~/.n8n-deploy
```

### Key Generation

Generate secure API keys from n8n:

1. Open n8n web interface
2. Navigate to **Settings** → **API**
3. Click **Create API Key**
4. Copy the JWT token immediately
5. Store in n8n-deploy within 60 seconds

{: .tip }
> **Best Practice**: Generate separate keys for each environment and purpose (read-only vs. full access).

### Key Rotation Strategy

Regular key rotation enhances security:

```bash
#!/bin/bash
# rotate-keys.sh - Monthly key rotation script

# Generate new key in n8n first, then:

# Add new key
echo "new_jwt_token" | n8n-deploy apikey add - --name prod_key_new --server "Production"

# Test new key
n8n-deploy apikey test prod_key_new

# Deactivate old key
n8n-deploy apikey deactivate prod_key_old

# After verification period, delete old key
# n8n-deploy apikey delete prod_key_old --confirm
```

---

## 📋 API Key Database Schema

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,        -- Key identifier (UTF-8 supported)
    api_key TEXT NOT NULL,            -- Plain text n8n JWT token
    description TEXT,                 -- Optional documentation
    created_at TIMESTAMP NOT NULL,    -- Creation time
    last_used_at TIMESTAMP,           -- Last usage time
    is_active INTEGER DEFAULT 1       -- Active status (1=yes, 0=no)
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

{: .note }
> The `server_api_keys` junction table enables many-to-many relationships between servers and API keys.

---

## 🆘 Troubleshooting

### Invalid API Key Format

**Error**: `Invalid JWT token format`

**Causes**:

- Incomplete token (copying error)
- Extra whitespace or newlines
- Expired token

**Solutions**:

```bash
# Verify token format (should start with eyJ)
echo "$API_KEY" | head -c 10

# Remove whitespace
API_KEY=$(echo "$API_KEY" | tr -d '[:space:]')
echo "$API_KEY" | n8n-deploy apikey add - --name fixed_key
```

### Authentication Failed

**Error**: `403 Forbidden` or `401 Unauthorized`

**Diagnosis**:

```bash
# Test key explicitly
n8n-deploy apikey test suspicious_key

# Check server connectivity
curl -I http://n8n.example.com:5678

# Verify key in n8n interface
# Settings → API → Active Keys
```

**Solutions**:

- Regenerate key in n8n
- Check server URL is correct
- Verify key hasn't expired
- Ensure key has necessary permissions

---

## 📖 Related Documentation

- [Server Management](/n8n-deploy/core-features/servers/) - Manage n8n server connections
- [Database Management](/n8n-deploy/core-features/database/) - Database operations and backups
- [Configuration](/n8n-deploy/configuration/) - Environment variables and settings
- [Workflow Management](/n8n-deploy/core-features/workflows/) - Push/pull workflows using API keys
- [Troubleshooting](/n8n-deploy/troubleshooting/) - Common issues and solutions

---

## 💡 Pro Tips

1. **Descriptive Naming**: Use `{environment}_{purpose}` pattern (e.g., `prod_readonly`, `staging_admin`)
2. **Regular Rotation**: Rotate production keys every 90 days minimum
3. **Separate Keys**: Never share keys between environments
4. **Test Before Deploy**: Always test new keys before deactivating old ones
5. **Audit Trail**: Review `last_used_at` timestamps regularly
6. **Backup Database**: API keys are only stored in the database
7. **Emergency Plan**: Document key revocation procedures
8. **Limit Permissions**: Use n8n's role-based permissions for granular access
9. **Monitor Usage**: Track key usage patterns for anomaly detection
10. **CI/CD Ephemeral Keys**: Use temporary keys that auto-delete after pipeline completion

---

**Last Updated**: October 2025
**Security Notice**: Always secure your n8n-deploy database with appropriate filesystem permissions
