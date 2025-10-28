---
layout: default
title: Database Operations
parent: Database Management
grand_parent: Core Features
nav_order: 1
description: "Initialize, manage, backup, and compact databases"
---

# Database Operations

Essential database operations for managing your n8n-deploy metadata store.

## 🚀 Initialize Database

Create the SQLite database with required schema:

```bash
# Basic initialization
n8n-deploy db init

# Initialize with custom directory
n8n-deploy --data-dir /opt/n8n-deploy db init

# Initialize with custom filename
n8n-deploy db init --db-filename my-workflows.db

# JSON output for automation
n8n-deploy db init --json --no-emoji
```

**What happens during initialization:**
1. Creates SQLite database file
2. Sets up schema with 5 tables
3. Initializes schema versioning
4. Creates indexes for performance

{: .note }
> If the database already exists, you'll be prompted for confirmation. Use `--import` flag to accept existing databases without prompting.

---

## 📊 Check Database Status

View database statistics:

```bash
# Rich emoji output
n8n-deploy db status

# Script-friendly output
n8n-deploy db status --no-emoji

# JSON for parsing
n8n-deploy db status --json
```

**Status information includes:**
- Database file location and size
- Schema version
- Record counts (workflows, API keys, servers)
- Last backup timestamp
- Database integrity status

**Example output:**
```
📊 Database Status

Database Path: /home/user/.n8n-deploy/n8n-deploy.db
Size: 128 KB
Schema Version: 2.0

📈 Statistics:
  Workflows: 15
  API Keys: 3
  Servers: 2
  Backups: 5

✅ Database is healthy
```

---

## 💾 Backup Database

Create timestamped database backups:

```bash
# Backup to default location
n8n-deploy db backup

# Backup to specific path
n8n-deploy db backup /backups/n8n-deploy-$(date +%Y%m%d).db

# With custom data directory
n8n-deploy --data-dir /opt/n8n-deploy db backup
```

**Backup features:**
- **Atomic operations**: Backup completes or fails entirely
- **SHA256 checksums**: Verify backup integrity
- **Metadata tracking**: Store backup history in database
- **No downtime**: Backup while using the database

{: .warning }
> **Important**: Backups only include the database file (metadata). Workflow JSON files should be managed with git version control.

**Backup verification:**

```bash
# Verify backup integrity
sha256sum /backups/n8n-deploy-20251006.db

# Compare with stored checksum
n8n-deploy db status --json | jq -r '.last_backup.checksum'
```

---

## 🔧 Compact Database

Optimize database storage by reclaiming unused space:

```bash
# Compact database
n8n-deploy db compact

# Script-friendly output
n8n-deploy db compact --no-emoji
```

**When to compact:**
- After deleting many workflows
- After removing unused API keys
- Monthly maintenance routine
- Before creating backups

**What compacting does:**
- Runs SQLite `VACUUM` command
- Rebuilds database file
- Reclaims deleted space
- Defragments data pages
- Rebuilds indexes

{: .tip }
> **Best Practice**: Compact before creating backups to reduce backup file size.

**Before/After comparison:**

```bash
# Check size before
n8n-deploy db status | grep Size

# Compact
n8n-deploy db compact

# Check size after (should be smaller if had deletions)
n8n-deploy db status | grep Size
```

---

## 📊 Database Size Guidelines

| Workflows | Expected Size | Maintenance Action |
|-----------|---------------|-------------------|
| 1-50 | < 1 MB | Normal operation |
| 51-200 | 1-5 MB | Monitor growth |
| 201-500 | 5-20 MB | Monthly compact |
| 500+ | 20+ MB | Weekly compact |

---

## 🔄 Maintenance Routines

### Daily Backup Script

```bash
#!/bin/bash
# daily-backup.sh

BACKUP_DIR="/backups/n8n-deploy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
n8n-deploy db backup "${BACKUP_DIR}/n8n-deploy_${TIMESTAMP}.db" --no-emoji

# Verify backup
if [ -f "${BACKUP_DIR}/n8n-deploy_${TIMESTAMP}.db" ]; then
    echo "✓ Backup created successfully"
else
    echo "✗ Backup failed"
    exit 1
fi
```

### Monthly Compaction

```bash
# Add to crontab
0 2 1 * * /usr/local/bin/n8n-deploy db compact --no-emoji
```

### Backup Rotation

```bash
# Keep only last 30 days of backups
find /backups/n8n-deploy -name "*.db" -mtime +30 -delete
```

---

## 📖 Related Documentation

- [Database Schema](schema/) - Table structures and relationships
- [Troubleshooting](troubleshooting/) - Common issues and solutions
- [DevOps Guide](../../../devops-guide/backup-strategies/) - Automated backup strategies
- [Configuration](../../../configuration/) - Environment variables

---

## 💡 Best Practices

1. **Regular Backups**: Schedule daily database backups
2. **Verify Integrity**: Check SHA256 checksums after backups
3. **Monitor Size**: Track database growth over time
4. **Compact Regularly**: Monthly compaction for optimal performance
5. **Test Restores**: Periodically verify backup restoration works
6. **Off-Site Storage**: Copy backups to remote locations
7. **Version Control**: Keep workflow JSON files in git
8. **Secure Permissions**: Protect database with `chmod 600`
