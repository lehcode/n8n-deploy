# n8n-deploy

[![GitHub](https://img.shields.io/badge/GitHub-lehcode%2Fn8n--deploy-blue?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy)
[![CI/CD Pipeline](https://github.com/lehcode/n8n-deploy/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/lehcode/n8n-deploy/actions)
[![GitHub stars](https://img.shields.io/github/stars/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/commits/master)
[![GitHub issues](https://img.shields.io/github/issues/lehcode/n8n-deploy?style=flat-square&logo=github)](https://github.com/lehcode/n8n-deploy/issues)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue?style=flat-square&logo=python)](https://github.com/lehcode/n8n-deploy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://github.com/lehcode/n8n-deploy/blob/master/LICENSE)
[![Coverage](https://img.shields.io/codecov/c/github/lehcode/n8n-deploy?style=flat-s
  quare)](https://codecov.io/gh/lehcode/n8n-deploy)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/n8n-deploy?style=flat-square&logo=pypi)](https://pypi.org/project/n8n-deploy/)
[![Downloads](https://img.shields.io/pypi/dm/n8n-deploy?style=flat-square)](https://pypi.org/project/n8n-deploy/)

> *"The first rule of intelligent tinkering is to save all the parts."* - Paul R. Ehrlich

**A privacy-first Python CLI tool for managing n8n workflows with SQLite metadata storage.**

n8n-deploy is designed for n8n users who need better workflow management, especially when working with remote servers where web UI access isn't available. It provides database-first workflow management with complete local control and zero data collection.

## 🔒 Privacy & Transparency

**Your data stays on your machine, period.**

- **Zero data collection** - No analytics, no tracking, no telemetry
- **No external communications** except to YOUR specified n8n server when YOU tell it to
- **Local-first storage** - Everything stored in local SQLite database
- **Open source transparency** - Complete source code available on GitHub

## ⚡ Install in 30 Seconds

### Option 1: PyPI (Recommended)
```bash
pip install n8n-deploy
```

### Option 2: GitHub Latest
```bash
pip install git+https://github.com/lehcode/n8n-deploy.git
```

### Option 3: No Installation Required
```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
./n8n-deploy --help  # Works immediately
```

## 🚀 Get Started in 3 Steps

### Step 1: Initialize (one-time setup)
```bash
n8n-deploy db init
```

### Step 2: Add your n8n server API key (optional)
```bash
echo "your-n8n-api-token" | n8n-deploy apikey add --name my_serverKey
```

### Step 3: Start managing workflows
```bash
# List your workflows
n8n-deploy list

# Pull from your n8n server
N8N_SERVER_URL=http://localhost:5678 n8n-deploy pull workflow_name

# Create backups
n8n-deploy backup-workflows --backup-dir ./backups
```

**That's it!** You're ready to manage workflows like a pro.

## ✨ Core Features

### 🎯 Simple Workflow Management
- **Manage workflows** with intuitive commands
- **Search and filter** workflows by name, description, or tags
- **Sync metadata** automatically from JSON files
- **Beautiful, colorful output** that's also script-friendly

### 🌐 n8n Server Integration
- **Push/pull workflows** to/from any n8n server
- **Official n8n REST API** - Uses only the official n8n public API endpoints
- **API key storage** (locally, in plain text)
- **SSL verification** with optional skip for dev environments

### 💾 Backup & Restore
- **Workflow backups** with SHA256 integrity verification
- **Metadata preservation** - restore exactly what you backed up
- **Selective restoration** - choose what to restore
- **Backup verification** to ensure data integrity

### 🗄️ Local Database Management
- **SQLite backend** - fast, reliable, and portable
- **Schema versioning** with automatic migrations
- **Database optimization** tools (compact)
- **Full backup capabilities** backup data DB in plain text

## 📚 Configuration (All Optional)

n8n-deploy works out of the box with smart defaults, but you can customize everything:

```bash
# Where to store n8n-deploy data (database, backups)
export N8N_DEPLOY_APP_DIR="/path/to/n8n-deply-app/data"

# Where your workflow JSON file is located
export N8N_FLOW_DIR="/path/to/your/workflows"

# Your n8n server URL (for push/pull operations)
export N8N_SERVER_URL="http://localhost:5678"

# Your n8n API key (fallback when no database API keys exist)
export N8N_API_KEY="your-n8n-api-key"
```

### Configuration Priority
1. **Command-line flags** (highest priority)
2. **Environment variables**
3. **Smart defaults** (current directory, intelligent path resolution)

### Use Custom Directories
```bash
# Use custom directories
n8n-deploy --app-dir /custom/app/path --flow-dir /custom/workflows list

# Or set environment variables
export N8N_DEPLOY_APP_DIR="/team/shared/n8n-deploy"
export N8N_FLOW_DIR="/team/shared/workflows"
n8n-deploy list
```

## 🎮 Usage Examples

### Daily Workflow Management
```bash
# List all workflows with status
n8n-deploy list

# Search for specific workflows
n8n-deploy search "googleEmail-collect"

# Get detailed stats about a workflow
n8n-deploy stats deAVBp391wvomsWY

# Sync file changes to database
n8n-deploy sync deAVBp391wvomsWY
```

### Working with n8n Servers
```bash
# List workflows on your server
n8n-deploy --server-url http://localhost:5678 list-server

# Pull a workflow from server (see note below about finding Workflow ID)
n8n-deploy pull deAVBp391wvomsWY

# Push local changes to server
n8n-deploy push deAVBp391wvomsWY

# Override server URL for one command
n8n-deploy --server-url http://staging.example.com list-server
```

**💡 Finding Workflow ID:** The Workflow ID is the last part of your n8n workflow URL. For example, in `https://user-n8n-server.dev:5678/workflow/deAVBp391wvomsWY`, the Workflow ID is `deAVBp391wvomsWY`. You can also find the workflow ID in your n8n workflow settings or by using the n8n API to list workflows.

**🔌 n8n API Integration:** n8n-deploy exclusively uses the official n8n public REST API for all server communications. This ensures compatibility with all n8n versions and maintains the security and reliability standards of the official n8n platform.

### Backup Operations
```bash
# Create a complete backup
n8n-deploy backup-workflows --backup-dir /safe/location

# List all available backups
n8n-deploy list-backups --backup-dir /safe/location

# Verify backup integrity
n8n-deploy verify-backup /safe/location/backup.tar.gz

# Restore from backup
n8n-deploy restore-workflows /safe/location/backup.tar.gz
```

### API Key Management
```bash
# Add a new API key
echo "jwt-token-here" | n8n-deploy apikey add --name production

# List all stored keys (keys hidden by default)
n8n-deploy apikey list

# Test a key
n8n-deploy apikey test production

# Retrieve a key (use with caution)
n8n-deploy apikey get production --show-key
```

### Script-Friendly Output
```bash
# Disable emojis for automation
n8n-deploy --no-emoji list

# JSON output for parsing
n8n-deploy list --format json

# Database status as JSON
n8n-deploy db status --format json
```

## 🛠️ Advanced Usage

### Multiple n8n Servers
```bash
# Store different API keys for different servers
echo "prod-token" | n8n-deploy apikey add --name production
echo "dev-token" | n8n-deploy apikey add --name development

# Switch between servers easily
n8n-deploy --server-url http://prod.example.com list-server
n8n-deploy --server-url http://dev.example.com list-server
```

### Database Maintenance
```bash
# Check database status
n8n-deploy db status

# Optimize database storage
n8n-deploy db compact

# Create database backup
n8n-deploy db backup /backup/path/database-backup.db
```

### SQLite Database Browsing

Want to explore your workflow data directly? Use these popular SQLite tools:

**GUI Tools:**
- **[DB Browser for SQLite](https://sqlitebrowser.org/)** - Cross-platform, user-friendly interface
- **[SQLiteStudio](https://sqlitestudio.pl/)** - Feature-rich with advanced query capabilities

**Command Line:**
- **sqlite3** (built into most systems) - `sqlite3 ~/.local/share/n8n-deploy/n8n-deploy.db`
- **[litecli](https://litecli.com/)** - Modern CLI with syntax highlighting

```bash
# Quick database inspection
sqlite3 ~/.local/share/n8n-deploy/n8n-deploy.db ".tables"
sqlite3 ~/.local/share/n8n-deploy/n8n-deploy.db "SELECT name, status FROM workflows;"
```

## 🔧 Development & Contributing

### Local Development Setup
```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Option 1: Using uv (faster)
uv venv --python /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Option 2: Standard pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Development installation
pip install -e .

# Run tests
python run_tests.py --unit
python run_tests.py --integration
```

### Project Structure
```
n8n-deploy/
├── api/                    # Core application modules
│   ├── cli/               # CLI command modules
│   ├── database/          # Database operations
│   └── workflow/          # Workflow management
├── tests/                 # Comprehensive test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
└── n8n-deploy            # Wrapper script (no installation)
```

## 💡 FAQ

### Q: Is my data safe?
**A:** Absolutely. n8n-deploy stores everything locally on your machine. No data is ever sent anywhere except to YOUR n8n server when YOU explicitly request it.

### Q: Do I need to configure anything?
**A:** No! n8n-deploy works out of the box. Configuration is only needed if you want to customize paths or work with remote n8n servers.

### Q: Can I use this with multiple n8n servers?
**A:** Yes! You can store multiple API keys and switch between servers using command-line flags or environment variables.

### Q: What happens to my workflow files?
**A:** Your JSON files are never modified by n8n-deploy. The tool only reads them and stores minimal metadata in its own database. Your original files remain untouched.

### Q: Can I automate this in scripts?
**A:** Absolutely! Use the `--no-emoji` flag and/or `--format json` options for script-friendly output. All commands are designed to work well in automation.

## 📋 System Requirements

- **Python 3.8+** (tested on 3.8-3.12)
- **Operating System:** Linux, macOS, Windows
- **Dependencies:** Minimal (click, rich, pydantic, requests)
- **Storage:** SQLite database (no external database required)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **GitHub Repository:** https://github.com/lehcode/n8n-deploy
- **PyPI Package:** https://pypi.org/project/n8n-deploy/
- **Issue Tracker:** https://github.com/lehcode/n8n-deploy/issues
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

**Happy workflow managing!** 🎭✨

*n8n-deploy: Because your workflows deserve better management.*
