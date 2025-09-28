# n8n-deploy Troubleshooting Guide

> *"If anything can go wrong, it will go wrong. If nothing can go wrong, something will still go wrong."* - Murphy's Universal Law

This comprehensive troubleshooting guide covers common issues, diagnostic procedures, and solutions for n8n-deploy across different environments and use cases.

## Table of Contents

- [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [Database Issues](#database-issues)
- [File System Problems](#file-system-problems)
- [API Key Management Issues](#api-key-management-issues)
- [Workflow Management Problems](#workflow-management-problems)
- [Backup and Restore Issues](#backup-and-restore-issues)
- [Performance Issues](#performance-issues)
- [Platform-Specific Problems](#platform-specific-problems)
- [Development and Testing Issues](#development-and-testing-issues)
- [GitLab CI/CD Issues](#gitlab-cicd-issues)
- [Recovery Procedures](#recovery-procedures)
- [Getting Help](#getting-help)

## Quick Diagnostic Checklist

When experiencing issues, run through this quick checklist:

```bash
# 1. Verify installation
n8n-deploy --version

# 2. Check environment
echo "N8N_FLOW_DIR: $N8N_FLOW_DIR"
echo "Current directory: $(pwd)"

# 3. Test database access
n8n-deploy db status

# 4. Check file permissions
ls -la $(n8n-deploy db status --format=json | jq -r '.database_path' | dirname)

# 5. Verify workflow directory
ls -la "$N8N_FLOW_DIR" || ls -la ./n8n/workflows/

# 6. Test basic functionality
n8n-deploy list

# 7. Check for error patterns
n8n-deploy --no-emoji list 2>&1 | grep -i error
```

If any step fails, proceed to the relevant section below.

## Installation Issues

### Issue: "Command not found: n8n-deploy"

**Symptoms:**
```bash
$ n8n-deploy --version
bash: n8n-deploy: command not found
```

**Causes:**
- n8n-deploy not installed
- Installation path not in PATH
- Virtual environment not activated
- Installation failed silently

**Solutions:**

1. **Verify Installation:**
   ```bash
   pip list | grep n8n-deploy
   pip show n8n-deploy
   ```

2. **Reinstall:**
   ```bash
   pip install --upgrade n8n-deploy
   ```

3. **Check PATH:**
   ```bash
   echo $PATH
   which n8n-deploy
   python -c "import sys; print('\n'.join(sys.path))"
   ```

4. **Use Python Module Directly:**
   ```bash
   python -m api.cli --version
   ```

5. **Virtual Environment Fix:**
   ```bash
   source .venv/bin/activate  # Activate if using venv
   pip install n8n-deploy
   ```

### Issue: "ImportError: No module named 'api'"

**Symptoms:**
```bash
$ n8n-deploy --version
ImportError: No module named 'api'
```

**Causes:**
- Development installation issue
- Python path problems
- Incomplete installation

**Solutions:**

1. **Development Installation:**
   ```bash
   cd /path/to/n8n-deploy
   pip install -e .
   ```

2. **Check Installation Location:**
   ```bash
   pip show n8n-deploy
   python -c "import api; print(api.__file__)"
   ```

3. **Reinstall from Source:**
   ```bash
   git clone https://github.com/lehcode/n8n-deploy.git
   cd n8n-deploy
   pip install -e .[dev,test]
   ```

### Issue: "Permission denied" during Installation

**Symptoms:**
```bash
$ pip install n8n-deploy
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions:**

1. **User Installation:**
   ```bash
   pip install --user n8n-deploy
   ```

2. **Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install n8n-deploy
   ```

3. **Fix pip Permissions:**
   ```bash
   sudo chown -R $USER ~/.local/
   pip install n8n-deploy
   ```

## Configuration Problems

### Issue: "Base folder does not exist"

**Symptoms:**
```bash
$ n8n-deploy list
Error: Base folder does not exist: /nonexistent/path
```

**Diagnosis:**
```bash
# Check current configuration
python -c "
from api.config import get_config
config = get_config()
print(f'Base folder: {config.base_folder}')
print(f'Flow folder: {config.flow_folder}')
print(f'Exists: {config.base_folder.exists()}')
"
```

**Solutions:**

1. **Create Directory:**
   ```bash
   mkdir -p /correct/path
   n8n-deploy --app-dir /correct/path db init
   ```

2. **Fix Environment Variable:**
   ```bash
   export N8N_FLOW_DIR=/correct/workflow/path
   n8n-deploy list
   ```

3. **Use Absolute Paths:**
   ```bash
   n8n-deploy --app-dir $(pwd)/n8n-deploy-data list
   ```

### Issue: "Flow folder not writable"

**Symptoms:**
```bash
$ n8n-deploy add wf-001 "Test" "test.json"
Error: Flow folder is not writable: /readonly/path
```

**Diagnosis:**
```bash
# Check permissions
ls -la "$N8N_FLOW_DIR"
touch "$N8N_FLOW_DIR/test" && rm "$N8N_FLOW_DIR/test"  # Write test
```

**Solutions:**

1. **Fix Permissions:**
   ```bash
   sudo chmod 755 "$N8N_FLOW_DIR"
   sudo chown $USER "$N8N_FLOW_DIR"
   ```

2. **Use Different Directory:**
   ```bash
   mkdir ~/workflows
   export N8N_FLOW_DIR=~/workflows
   n8n-deploy list
   ```

3. **Create Subdirectory:**
   ```bash
   mkdir -p ~/n8n-deploy/workflows
   n8n-deploy --app-dir ~/n8n-deploy --flow-dir ~/n8n-deploy list
   ```

### Issue: Environment Variables Not Working

**Symptoms:**
```bash
$ export N8N_FLOW_DIR=/custom/path
$ n8n-deploy list
# Still uses default directory
```

**Diagnosis:**
```bash
# Check variable is set and exported
echo "N8N_FLOW_DIR: '$N8N_FLOW_DIR'"
env | grep N8N_FLOW_DIR
declare -p N8N_FLOW_DIR  # Check if exported
```

**Solutions:**

1. **Proper Export:**
   ```bash
   export N8N_FLOW_DIR=/custom/path  # Must use export
   n8n-deploy list
   ```

2. **Shell Configuration:**
   ```bash
   echo "export N8N_FLOW_DIR=/custom/path" >> ~/.bashrc
   source ~/.bashrc
   ```

3. **CLI Override:**
   ```bash
   n8n-deploy --flow-dir /custom/path list
   ```

## Database Issues

### Issue: "Database initialization failed"

**Symptoms:**
```bash
$ n8n-deploy db init
Error: Database initialization failed
```

**Diagnosis:**
```bash
# Check database directory
ls -la $(dirname $(pwd)/n8n-deploy.db)
sqlite3 n8n-deploy.db ".tables" 2>&1  # Test SQLite access
```

**Solutions:**

1. **Directory Permissions:**
   ```bash
   mkdir -p ~/n8n-deploy
   cd ~/n8n-deploy
   n8n-deploy db init
   ```

2. **SQLite Installation:**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install sqlite3

   # On macOS
   brew install sqlite

   # On Windows
   # Install SQLite from https://sqlite.org/download.html
   ```

3. **Manual Database Creation:**
   ```bash
   python -c "
   from api.n8n_deploy_db import n8n_deploy_DB
   from api.config import get_config
   config = get_config()
   db = n8n_deploy_DB(config=config)
   print('Database created successfully')
   "
   ```

### Issue: "Database is locked"

**Symptoms:**
```bash
$ n8n-deploy list
Error: database is locked
```

**Diagnosis:**
```bash
# Check for other processes
lsof n8n-deploy.db  # Linux/macOS
fuser n8n-deploy.db  # Linux

# Check database file
ls -la n8n-deploy.db*
```

**Solutions:**

1. **Close Other Connections:**
   ```bash
   # Find and kill other n8n-deploy processes
   ps aux | grep n8n-deploy
   kill <process-id>
   ```

2. **Remove Lock Files:**
   ```bash
   # Remove WAL files if safe
   rm -f n8n-deploy.db-wal n8n-deploy.db-shm
   ```

3. **Database Recovery:**
   ```bash
   # Backup and recreate
   cp n8n-deploy.db n8n-deploy.db.backup
   sqlite3 n8n-deploy.db "PRAGMA integrity_check;"
   n8n-deploy db vacuum
   ```

### Issue: "Schema version mismatch"

**Symptoms:**
```bash
$ n8n-deploy list
Error: Schema version mismatch. Expected: 1, Found: 0
```

**Solutions:**

1. **Reinitialize Database:**
   ```bash
   mv n8n-deploy.db n8n-deploy.db.old
   n8n-deploy db init
   ```

2. **Manual Schema Update:**
   ```bash
   python -c "
   from api.n8n_deploy_db import n8n_deploy_DB
   db = n8n_deploy_DB()
   db._initialize_database()  # Force schema update
   "
   ```

## File System Problems

### Issue: "Workflow file not found"

**Symptoms:**
```bash
$ n8n-deploy add wf-001 "Test" "missing.json"
Error: Workflow file not found: missing.json
```

**Diagnosis:**
```bash
# Check file location
find . -name "*.json" | head -10
ls -la workflows/
echo "Looking in: $(n8n-deploy --help | grep flow-dir)"
```

**Solutions:**

1. **Correct Path:**
   ```bash
   # Use relative path from flow directory
   n8n-deploy add wf-001 "Test" "workflows/existing.json"
   ```

2. **Create Missing File:**
   ```bash
   mkdir -p workflows
   echo '{"id":"wf-001","name":"Test","nodes":[],"connections":{}}' > workflows/test.json
   n8n-deploy add wf-001 "Test" "workflows/test.json"
   ```

3. **Check Flow Directory:**
   ```bash
   export N8N_FLOW_DIR=$(pwd)
   n8n-deploy add wf-001 "Test" "workflows/test.json"
   ```

### Issue: "Permission denied reading workflow file"

**Symptoms:**
```bash
$ n8n-deploy sync wf-001
Error: Permission denied: /path/to/workflow.json
```

**Solutions:**

1. **Fix File Permissions:**
   ```bash
   chmod 644 /path/to/workflow.json
   ```

2. **Fix Directory Permissions:**
   ```bash
   chmod 755 /path/to/workflow/directory
   ```

3. **Change Ownership:**
   ```bash
   sudo chown $USER:$USER /path/to/workflow.json
   ```

## API Key Management Issues

### Issue: "API key not found"

**Symptoms:**
```bash
$ n8n-deploy pull wf-001
Error: No API key found. Add one with 'n8n-deploy apikey add <name>'.
```

**Diagnosis:**
```bash
# Check existing API keys
n8n-deploy apikey list

# Test API key access
n8n-deploy apikey get my_key
```

**Solutions:**

1. **Add API Key:**
   ```bash
   n8n-deploy apikey add n8n_server --key YOUR_API_KEY
   ```

2. **Check Key Name:**
   ```bash
   # n8n-deploy looks for 'n8n' key by default
   n8n-deploy apikey add n8n --key YOUR_API_KEY
   ```

3. **Test Key:**
   ```bash
   n8n-deploy apikey test n8n_server
   ```

### Issue: "API key has expired"

**Symptoms:**
```bash
$ n8n-deploy pull wf-001
Warning: API key has expired: 2024-09-01T10:30:00
Error: Failed to authenticate with n8n server
```

**Solutions:**

1. **Update Expired Key:**
   ```bash
   n8n-deploy apikey delete old_key --confirm
   n8n-deploy apikey add new_key --expires-days 365
   ```

2. **Check Expiration:**
   ```bash
   n8n-deploy apikey list
   ```

## Workflow Management Problems

### Issue: "Workflow already exists"

**Symptoms:**
```bash
$ n8n-deploy add wf-001 "Test" "test.json"
Error: Workflow already exists: wf-001
```

**Solutions:**

1. **Use Different ID:**
   ```bash
   n8n-deploy add wf-002 "Test" "test.json"
   ```

2. **Update Existing:**
   ```bash
   n8n-deploy remove wf-001  # Remove first
   n8n-deploy add wf-001 "Updated Test" "test.json"
   ```

3. **Check Existing Workflows:**
   ```bash
   n8n-deploy list
   n8n-deploy stats wf-001
   ```

### Issue: "No workflows found for backup"

**Symptoms:**
```bash
$ n8n-deploy backup-workflows
Error: No backupable workflows found
```

**Diagnosis:**
```bash
# Check workflow status
n8n-deploy list --only  # Show only backupable
n8n-deploy list  # Show all with backupable column
```

**Solutions:**

1. **Add Workflows:**
   ```bash
   n8n-deploy add wf-001 "Test" "workflows/test.json"
   ```

2. **Check File Existence:**
   ```bash
   # Create missing workflow files
   mkdir -p workflows
   echo '{"id":"wf-001","name":"Test"}' > workflows/test.json
   ```

3. **Sync Workflows:**
   ```bash
   n8n-deploy sync wf-001
   ```

## Backup and Restore Issues

### Issue: "Backup integrity check failed"

**Symptoms:**
```bash
$ n8n-deploy verify-backup backup.tar.gz
Error: Backup integrity check failed
```

**Diagnosis:**
```bash
# Check file
file backup.tar.gz
tar -tzf backup.tar.gz  # List contents
ls -la backup.tar.gz
```

**Solutions:**

1. **Verify File:**
   ```bash
   # Check if file is complete
   shasum -a 256 backup.tar.gz

   # Try to extract
   tar -tzf backup.tar.gz > /dev/null && echo "Archive OK"
   ```

2. **Create New Backup:**
   ```bash
   n8n-deploy backup-workflows --backup-dir ./backups
   ```

3. **Manual Verification:**
   ```bash
   # Extract and verify manually
   mkdir temp-verify
   tar -xzf backup.tar.gz -C temp-verify
   ls -la temp-verify/
   ```

### Issue: "Restore failed: conflicts detected"

**Symptoms:**
```bash
$ n8n-deploy restore-workflows backup.tar.gz
Error: Restore failed: Workflow conflicts detected
```

**Solutions:**

1. **Force Restore:**
   ```bash
   n8n-deploy restore-workflows backup.tar.gz --force
   ```

2. **Manual Resolution:**
   ```bash
   # List current workflows
   n8n-deploy list

   # Remove conflicting workflows
   n8n-deploy remove wf-conflicting-001

   # Try restore again
   n8n-deploy restore-workflows backup.tar.gz
   ```

## Performance Issues

### Issue: "Commands are slow"

**Symptoms:**
- Long delays for database operations
- Slow workflow listing
- Backup operations timeout

**Diagnosis:**
```bash
# Check database size and stats
n8n-deploy db status

# Test individual operations
time n8n-deploy list
time n8n-deploy search test
time n8n-deploy db vacuum
```

**Solutions:**

1. **Database Optimization:**
   ```bash
   # Vacuum database
   n8n-deploy db vacuum

   # Compact database
   n8n-deploy db compact

   # Check improvements
   n8n-deploy db status
   ```

2. **Check Disk Space:**
   ```bash
   df -h $(dirname $(pwd)/n8n-deploy.db)
   ```

3. **Rebuild Search Index:**
   ```bash
   python -c "
   from api.n8n_deploy_db import n8n_deploy_DB
   db = n8n_deploy_DB()
   db.rebuild_search_index()
   print('Search index rebuilt')
   "
   ```

### Issue: "Out of disk space"

**Symptoms:**
```bash
$ n8n-deploy backup-workflows
Error: No space left on device
```

**Solutions:**

1. **Check Space:**
   ```bash
   df -h
   du -sh ~/.n8n-deploy-*
   ```

2. **Clean Old Backups:**
   ```bash
   n8n-deploy list-backups
   # Remove old backups manually
   ls -la backups/
   rm backups/old-backup-*.tar.gz
   ```

3. **Use External Directory:**
   ```bash
   n8n-deploy backup-workflows --backup-dir /external/storage/backups
   ```

## Platform-Specific Problems

### Windows Issues

**Issue: Path separator problems**

```powershell
# Use PowerShell, not Command Prompt
py -m pip install n8n-deploy

# Set environment variables
$env:N8N_FLOW_DIR = "C:\workflows"

# Use forward slashes or escaped backslashes
n8n-deploy --app-dir "C:/n8n-deploy" list
```

**Issue: Encoding problems**

```powershell
# Set UTF-8 encoding
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# Use --no-emoji for compatibility
n8n-deploy --no-emoji list
```

### macOS Issues

**Issue: Python/pip conflicts**

```bash
# Use Python 3 explicitly
python3 -m pip install n8n-deploy

# Use Homebrew Python
brew install python
/usr/local/bin/python3 -m pip install n8n-deploy

# Fix PATH
export PATH="/usr/local/bin:$PATH"
```

### Linux Issues

**Issue: Missing dependencies**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv sqlite3

# CentOS/RHEL
sudo yum install python3-pip python3-venv sqlite

# Arch Linux
sudo pacman -S python-pip sqlite
```

## Development and Testing Issues

### Issue: "Tests failing in CI but passing locally"

**Common Causes:**
- Environment differences
- Permission differences
- Path differences

**Solutions:**

1. **Use Testing Environment Variable:**
   ```bash
   export N8N_DEPLOY_TESTING=1
   python run_tests.py --unit
   ```

2. **CI-Compatible Test Paths:**
   ```bash
   # Use environment-agnostic paths in tests
   # Instead of: mkdir("/nonexistent/path")  # May work in CI
   # Use: mkdir("/dev/null/invalid_path")    # Always fails
   ```

3. **Debug CI Environment:**
   ```bash
   # In CI pipeline
   whoami
   id
   pwd
   env | grep N8N
   ls -la
   ```

### Issue: "Type checking errors"

**Symptoms:**
```bash
$ mypy api/
error: Library stubs not found for "requests"
```

**Solutions:**

1. **Install Type Stubs:**
   ```bash
   pip install types-requests types-click types-dateutil
   ```

2. **Clear MyPy Cache:**
   ```bash
   rm -rf .mypy_cache/
   mypy api/ --install-types
   ```

## GitLab CI/CD Issues

### Issue: "Pipeline failing on dependency installation"

**Solutions:**

1. **Check APT Proxy Configuration:**
   ```yaml
   # In .gitlab-ci.yml
   before_script:
     - echo "Acquire::http::Proxy \"http://192.168.76.5:3142\";" > /etc/apt/apt.conf.d/01proxy || true
     - apt-get update && apt-get install -y git
   ```

2. **Use Cached Dependencies:**
   ```yaml
   cache:
     key: ${CI_COMMIT_REF_SLUG}
     paths:
       - .cache/pip/
       - .venv/
   ```

### Issue: "Docker builds failing"

**Solutions:**

1. **Check Docker Cache:**
   ```bash
   docker pull $CI_REGISTRY_IMAGE:cache || true
   ```

2. **Verify Runner Configuration:**
   ```bash
   # On GitLab runner host
   sudo gitlab-runner verify
   sudo gitlab-runner list
   ```

## Recovery Procedures

### Database Corruption Recovery

```bash
# 1. Backup corrupted database
cp n8n-deploy.db n8n-deploy.db.corrupted

# 2. Try integrity check
sqlite3 n8n-deploy.db "PRAGMA integrity_check;"

# 3. Dump and restore
sqlite3 n8n-deploy.db ".dump" > backup.sql
rm n8n-deploy.db
sqlite3 n8n-deploy.db < backup.sql

# 4. Reinitialize if needed
n8n-deploy db init
```

### Complete Reset Procedure

```bash
# 1. Backup important data
n8n-deploy backup-workflows --backup-dir /safe/location
n8n-deploy db backup /safe/location/database-backup.db
cp -r workflows/ /safe/location/workflows-backup/

# 2. Clean slate
rm -f n8n-deploy.db*
rm -rf backups/

# 3. Reinitialize
n8n-deploy db init

# 4. Restore workflows
n8n-deploy restore-workflows /safe/location/backup.tar.gz --force
```

### Configuration Reset

```bash
# 1. Clear environment
unset N8N_FLOW_DIR
unset N8N_DEPLOY_TESTING

# 2. Reset to defaults
cd ~/n8n-deploy-fresh
n8n-deploy db init

# 3. Test basic functionality
n8n-deploy list
n8n-deploy db status
```

## Getting Help

### Collecting Diagnostic Information

```bash
#!/bin/bash
# collect-diagnostics.sh

echo "=== n8n-deploy Diagnostic Information ==="
date

echo -e "\n=== System Information ==="
uname -a
python --version
pip --version

echo -e "\n=== n8n-deploy Installation ==="
n8n-deploy --version
pip show n8n-deploy
which n8n-deploy

echo -e "\n=== Environment ==="
env | grep -E "(N8N|PATH)" | sort

echo -e "\n=== Current Directory ==="
pwd
ls -la | head -10

echo -e "\n=== Database Status ==="
n8n-deploy db status || echo "Database status failed"

echo -e "\n=== Configuration Test ==="
python -c "
try:
    from api.config import get_config
    config = get_config()
    print(f'Base folder: {config.base_folder}')
    print(f'Flow folder: {config.flow_folder}')
    print(f'Database path: {config.database_path}')
    print(f'Base exists: {config.base_folder.exists()}')
except Exception as e:
    print(f'Configuration error: {e}')
"

echo -e "\n=== Recent Errors ==="
n8n-deploy --no-emoji list 2>&1 | tail -5

echo -e "\n=== End Diagnostic Information ==="
```

### When to Seek Help

**Seek help when:**
- Multiple solutions from this guide don't work
- Error messages are unclear or undocumented
- System-specific issues occur
- Data corruption or loss occurs

**Before seeking help, provide:**
- Output from diagnostic script above
- Complete error messages
- Steps to reproduce the issue
- n8n-deploy version and environment details

### Support Channels

- **GitHub Issues**: https://github.com/lehcode/n8n-deploy/issues
- **Documentation**: README.md, ARCHITECTURE.md, CLI-REFERENCE.md
- **GitLab Issues**: https://gitlab.pirouter.dev:8443/n8n/n8n-deploy

### Bug Report Template

```markdown
## Bug Report

### Environment
- n8n-deploy version: [run `n8n-deploy --version`]
- Python version: [run `python --version`]
- Operating System: [Linux/macOS/Windows with version]
- Installation method: [pip/source/container]

### Problem Description
[Clear description of the issue]

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [Error occurs]

### Expected Behavior
[What you expected to happen]

### Actual Behavior
[What actually happened]

### Error Messages
```
[Complete error messages]
```

### Additional Information
[Any other relevant information]
```

---

This troubleshooting guide covers the most common issues with n8n-deploy. For additional help, consult the other documentation files or seek support through the official channels.