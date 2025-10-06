---
layout: default
title: Troubleshooting
parent: Database Management
grand_parent: Core Features
nav_order: 3
description: "Common database issues and solutions"
---

# Database Troubleshooting

Common database issues and their solutions.

## 🔒 Database Locked

**Error**: `database is locked`

### Causes
- Another n8n-deploy process is running
- Backup operation in progress
- File system lock not released
- NFS/network filesystem latency

### Solutions

**1. Check for running processes:**
```bash
ps aux | grep n8n-deploy
```

**2. Wait for operations to complete:**
```bash
# Wait 5 seconds and retry
sleep 5 && n8n-deploy db status
```

**3. Identify lock holder (Linux):**
```bash
fuser /path/to/n8n-deploy.db
lsof /path/to/n8n-deploy.db
```

**4. Check for stale locks:**
```bash
# Remove journal files if process died abnormally
rm -f ~/.n8n-deploy/n8n-deploy.db-journal
rm -f ~/.n8n-deploy/n8n-deploy.db-wal
```

{: .warning }
> Only remove journal files if you're certain no n8n-deploy processes are running!

---

## 💔 Corrupted Database

**Error**: `database disk image is malformed`

### Causes - Corruption
- System crash during write
- Disk full during operation
- Hardware failure
- Improper shutdown

### Recovery Steps

**1. Restore from latest backup:**
```bash
# List available backups
ls -lh /backups/n8n-deploy/

# Restore backup
cp /backups/n8n-deploy/latest.db ~/.n8n-deploy/n8n-deploy.db

# Verify integrity
n8n-deploy db status
```

**2. Verify backup integrity:**
```bash
sqlite3 /backups/latest.db "PRAGMA integrity_check;"
```

**3. Attempt repair (if no backup):**
```bash
# Dump and rebuild
sqlite3 corrupted.db ".dump" | sqlite3 repaired.db

# Move repaired database
mv repaired.db ~/.n8n-deploy/n8n-deploy.db

# Verify
n8n-deploy db status
```

**4. Check filesystem:**
```bash
# Check disk space
df -h ~/.n8n-deploy

# Check filesystem errors (requires unmount)
sudo fsck /dev/sdXX
```

---

## ❓ Missing Database

**Error**: `Oops! Database not found`

### Causes - Performance
- Database never initialized
- Wrong `--data-dir` path
- Database file deleted
- Environment variable misconfigured

#### Solutions - Performance

**1. Check database location:**
```bash
# Show expected location
n8n-deploy env | grep DATA_DIR

# Verify file exists
ls -lh ~/.n8n-deploy/n8n-deploy.db
```

**2. Initialize new database:**
```bash
n8n-deploy db init
```

**3. Restore from backup:**
```bash
# Import existing database
n8n-deploy db init --import /backups/n8n-deploy.db
```

**4. Check environment variables:**
```bash
# Show all configuration
n8n-deploy env

# Set correct data directory
export N8N_DEPLOY_DATA_DIR=/correct/path
n8n-deploy db status
```

---

## 🐌 Performance Issues

**Symptoms**: Slow operations, high CPU usage

### Diagnosis

**1. Check database size:**
```bash
n8n-deploy db status | grep Size
```

**2. Analyze query performance:**
```bash
sqlite3 n8n-deploy.db "PRAGMA stats;"
```

**3. Check filesystem I/O:**
```bash
# Monitor I/O
iotop -o | grep n8n-deploy

# Check disk latency
iostat -x 1
```

#### Solutions - Recovery

**1. Compact database:**
```bash
n8n-deploy db compact
```

**2. Verify indexes exist:**
```bash
sqlite3 n8n-deploy.db ".indexes"
```

**3. Check available disk space:**
```bash
df -h ~/.n8n-deploy
```

**4. Move to faster storage:**
```bash
# Move database to SSD
mv ~/.n8n-deploy /mnt/ssd/n8n-deploy
export N8N_DEPLOY_DATA_DIR=/mnt/ssd/n8n-deploy
```

---

## 🔐 Permission Denied

**Error**: `Permission denied` or `cannot open database file`

### Causes - Missing DB
- Incorrect file permissions
- Wrong file ownership
- SELinux/AppArmor restrictions
- Read-only filesystem

#### Solutions - Missing DB

**1. Fix file permissions:**
```bash
# Database file
chmod 644 ~/.n8n-deploy/n8n-deploy.db

# Directory
chmod 755 ~/.n8n-deploy
```

**2. Fix ownership:**
```bash
chown $USER:$USER ~/.n8n-deploy/n8n-deploy.db
```

**3. Check SELinux (if applicable):**
```bash
# Check SELinux status
sestatus

# Allow access
chcon -t user_home_t ~/.n8n-deploy/n8n-deploy.db
```

**4. Verify filesystem is writable:**
```bash
# Check mount options
mount | grep $(dirname ~/.n8n-deploy)

# Remount if read-only
sudo mount -o remount,rw /path/to/filesystem
```

---

## 📏 Disk Space Issues

**Error**: `disk I/O error` or `database or disk is full`

### Prevention

**1. Monitor disk usage:**
```bash
# Check available space
df -h ~/.n8n-deploy

# Set up alert (example)
if [ $(df ~/.n8n-deploy | tail -1 | awk '{print $5}' | sed 's/%//') -gt 90 ]; then
    echo "Warning: Disk usage above 90%"
fi
```

**2. Automate cleanup:**
```bash
# Rotate old backups
find /backups -name "*.db" -mtime +30 -delete

# Compact database monthly
0 2 1 * * n8n-deploy db compact --no-emoji
```

#### Solutions - Space

**1. Free up space:**
```bash
# Remove old backups
rm /backups/old-backup-*.db

# Compact database
n8n-deploy db compact
```

**2. Move database to larger partition:**
```bash
# Copy to larger disk
cp -r ~/.n8n-deploy /larger/disk/n8n-deploy

# Update configuration
export N8N_DEPLOY_DATA_DIR=/larger/disk/n8n-deploy
```

---

## 🔍 Diagnostic Commands

### Quick Health Check

```bash
#!/bin/bash
# database-health-check.sh

echo "=== Database Health Check ==="

# 1. Check database exists
if [ ! -f ~/.n8n-deploy/n8n-deploy.db ]; then
    echo "❌ Database not found"
    exit 1
fi

# 2. Check permissions
if [ ! -r ~/.n8n-deploy/n8n-deploy.db ]; then
    echo "❌ Database not readable"
    exit 1
fi

# 3. Check integrity
if sqlite3 ~/.n8n-deploy/n8n-deploy.db "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "✓ Database integrity OK"
else
    echo "❌ Database corrupted"
    exit 1
fi

# 4. Check size
SIZE=$(du -sh ~/.n8n-deploy/n8n-deploy.db | cut -f1)
echo "✓ Database size: $SIZE"

# 5. Check disk space
AVAILABLE=$(df -h ~/.n8n-deploy | tail -1 | awk '{print $4}')
echo "✓ Available space: $AVAILABLE"

echo "=== All checks passed ==="
```

### Detailed Diagnostics

```bash
# Show database statistics
sqlite3 n8n-deploy.db << EOF
SELECT 'Workflows: ' || COUNT(*) FROM workflows;
SELECT 'API Keys: ' || COUNT(*) FROM api_keys;
SELECT 'Servers: ' || COUNT(*) FROM servers;
SELECT 'Schema Version: ' || MAX(version) FROM schema_info;
EOF

# Check for fragmentation
sqlite3 n8n-deploy.db "PRAGMA page_count; PRAGMA freelist_count;"
```

---

## 📖 Related Documentation

- [Database Operations](operations/) - Normal operations
- [Database Schema](schema/) - Schema reference
- [DevOps Guide](../../../devops-guide/monitoring/) - Health monitoring
- [Configuration](../../../configuration/) - Environment setup

---

## 💡 Prevention Best Practices

1. **Regular Backups**: Schedule daily automated backups
2. **Monitor Disk Space**: Set up alerts for disk usage
3. **Compact Regularly**: Monthly compaction prevents fragmentation
4. **Test Restores**: Verify backup restoration works
5. **Use SSD Storage**: Better performance and reliability
6. **Proper Permissions**: Secure database file (chmod 600)
7. **Graceful Shutdowns**: Don't kill processes during writes
8. **Version Control**: Keep workflow JSON files in git
