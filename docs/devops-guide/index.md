---
layout: default
title: DevOps Guide
nav_order: 7
description: "CI/CD integration and automation patterns for n8n-deploy"
---

# DevOps Guide

> "Automation applied to an efficient operation will magnify the efficiency." — Bill Gates

Comprehensive guide for integrating n8n-deploy into DevOps workflows, CI/CD pipelines, and production environments.

## 🎯 Overview

This guide covers:
- **CI/CD Integration**: GitHub Actions, GitLab CI, Jenkins pipelines
- **Multi-Environment Setup**: Dev, staging, and production configurations
- **Backup Strategies**: Automated backups with rotation and verification
- **Monitoring**: Health checks and alerting
- **Security**: Best practices for production deployments

---

## 📚 Guide Sections

### CI/CD Integration
Integrate n8n-deploy into your continuous deployment pipelines.

**Topics covered:**
- GitHub Actions workflows
- GitLab CI/CD pipelines
- Jenkins job configuration
- Docker container automation
- Secrets management

[Learn more →](ci-cd-integration/)

### Multi-Environment Setup
Configure separate environments for development, staging, and production.

**Topics covered:**
- Environment separation strategies
- Server configuration per environment
- API key management across environments
- Blue-green deployment patterns
- Environment migration workflows

[Learn more →](multi-environment/)

### Backup Strategies
Automated backup solutions for database and workflows.

**Topics covered:**
- Scheduled database backups
- Backup rotation policies
- Integrity verification
- Restore procedures
- Off-site backup storage

[Learn more →](backup-strategies/)

### Monitoring & Health Checks
Monitor n8n-deploy operations and server health.

**Topics covered:**
- Database health monitoring
- Server connectivity checks
- API key validation
- Alerting and notifications
- Performance metrics

[Learn more →](monitoring/)

### Security Best Practices
Security patterns for production deployments.

**Topics covered:**
- File permissions and access control
- API key security
- Backup encryption
- Audit logging
- Network security

[Learn more →](security/)

---

## 🚀 Quick Examples

### GitHub Actions Workflow

```yaml
name: Deploy Workflows
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install n8n-deploy
        run: pip install n8n-deploy
      - name: Push workflows
        env:
          N8N_SERVER_URL: ${{ secrets.N8N_SERVER_URL }}
        run: |
          echo "${{ secrets.N8N_API_KEY }}" | n8n-deploy apikey add - --name ci_key
          n8n-deploy wf push "Production Workflow"
```

### Daily Backup Script

```bash
#!/bin/bash
# Automated daily backup with rotation

BACKUP_DIR="/backups/n8n-deploy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup
n8n-deploy db backup "${BACKUP_DIR}/backup_${TIMESTAMP}.db" --no-emoji

# Rotate old backups
find "${BACKUP_DIR}" -name "backup_*.db" -mtime +${RETENTION_DAYS} -delete

# Verify latest backup
if [ -f "${BACKUP_DIR}/backup_${TIMESTAMP}.db" ]; then
    echo "✓ Backup successful"
else
    echo "✗ Backup failed" | mail -s "Backup Alert" admin@example.com
fi
```

### Health Check Monitor

```bash
#!/bin/bash
# Monitor database and server health

# Check database status
if ! n8n-deploy db status --no-emoji > /dev/null 2>&1; then
    echo "❌ Database health check failed"
    exit 1
fi

# Check server connectivity
SERVERS=$(n8n-deploy server list --json --no-emoji | jq -r '.[] | select(.is_active==true) | .name')

for SERVER in $SERVERS; do
    SERVER_URL=$(n8n-deploy server list --json --no-emoji | jq -r ".[] | select(.name==\"$SERVER\") | .url")
    if curl -sf "${SERVER_URL}/healthz" > /dev/null 2>&1; then
        echo "✓ $SERVER is healthy"
    else
        echo "❌ $SERVER is unreachable"
    fi
done
```

---

## 📖 Related Documentation

- [Core Features](../core-features/) - Essential functionality
- [Configuration](../configuration/) - Environment variables
- [Quick Reference](../quick-reference/) - Command cheat sheets
- [Developer Guide](../developers/) - API reference and architecture

---

## 💡 Best Practices

1. **Separate Environments**: Use distinct databases for dev/staging/prod
2. **Automate Backups**: Schedule daily database backups with rotation
3. **Version Control**: Store workflow JSON files in git
4. **Secret Management**: Use CI/CD secrets, never hardcode API keys
5. **Health Monitoring**: Implement automated health checks
6. **Test Deployments**: Validate in staging before production
7. **Document Changes**: Maintain deployment logs and changelogs
8. **Access Control**: Limit production access with read-only keys

---

**Ready to integrate?** Start with [CI/CD Integration](ci-cd-integration/) for pipeline setup.
