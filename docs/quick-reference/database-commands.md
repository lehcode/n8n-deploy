---
layout: default
title: Database Commands Quick Reference
parent: Quick Reference
nav_order: 1
description: "One-page cheat sheet for n8n-deploy database operations"
---

# Database Commands Quick Reference

## Initialize Database

```bash
# Basic init
n8n-deploy db init

# Custom directory
n8n-deploy --data-dir /opt/n8n-deploy db init

# Custom filename
n8n-deploy db init --db-filename my-workflows.db

# Script mode
n8n-deploy db init --json --no-emoji
```

## Check Status

```bash
# Rich output
n8n-deploy db status

# JSON format
n8n-deploy db status --json

# Script mode
n8n-deploy db status --no-emoji
```

## Create Backup

```bash
# Default location
n8n-deploy db backup

# Specific path
n8n-deploy db backup /backups/n8n-$(date +%Y%m%d).db

# With custom data dir
n8n-deploy --data-dir /opt/n8n-deploy db backup
```

## Compact Database

```bash
# Reclaim space
n8n-deploy db compact

# Script mode
n8n-deploy db compact --no-emoji
```

## Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Backup | Daily | `n8n-deploy db backup /backups/daily.db` |
| Status Check | Weekly | `n8n-deploy db status` |
| Compact | Monthly | `n8n-deploy db compact` |
| Backup Cleanup | Monthly | `find /backups -mtime +30 -delete` |

## Emergency Recovery

```bash
# 1. Restore from backup
cp /backups/latest.db ~/.n8n-deploy/n8n-deploy.db

# 2. Verify integrity
n8n-deploy db status

# 3. Check workflows
n8n-deploy wf list
```

## Environment Variables

```bash
# Set data directory
export N8N_DEPLOY_DATA_DIR=/opt/n8n-deploy

# Verify config
n8n-deploy env
```

## Common Issues

**Database locked**: Wait or kill blocking process
**Corrupted database**: Restore from backup
**Permission denied**: Check file permissions (chmod 600)

---

**See Also**: [Database Management](../core-features/database/) | [Configuration](../configuration/)
