# n8n-deploy CLI Reference

> *"The more complex the mind, the greater the need for the simplicity of play."* - Albert Einstein's Rule of Complex Simplicity

This document provides a complete reference for all n8n-deploy CLI commands, options, and usage patterns.

## Table of Contents

- [Global Options](#global-options)
- [Command Groups](#command-groups)
- [Workflow Management Commands](#workflow-management-commands)
- [Database Management Commands](#database-management-commands)
- [API Key Management Commands](#api-key-management-commands)
- [Backup Operations Commands](#backup-operations-commands)
- [Output Formats](#output-formats)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)

## Global Options

These options are available for all commands:

```bash
n8n-deploy [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Option Reference

| Option | Type | Description | Example |
|--------|------|-------------|---------|
| `--app-dir PATH` | Path | Application directory for n8n-deploy data (database, backups). Defaults to current directory | `--app-dir /opt/n8n-deploy` |
| `--flow-dir PATH` | Path | Flow folder for workflow files. Uses N8N_FLOW_DIR env var or same as app directory if not specified | `--flow-dir /data/workflows` |
| `--no-emoji` | Flag | Disable emoji output for script parsing | `--no-emoji` |
| `--version` | Flag | Show version and exit | `--version` |
| `--help` | Flag | Show help message and exit | `--help` |

### Global Option Examples

```bash
# Use custom app directory for all data
n8n-deploy --app-dir /custom/path list

# Use separate directories for app data and workflow files
n8n-deploy --app-dir /app/data --flow-dir /workflow/files list

# Script-friendly output without emojis
n8n-deploy --no-emoji list

# Check version
n8n-deploy --version
```

## Command Groups

n8n-deploy organizes commands into logical groups:

### Main Commands
- `add`, `remove`, `list`, `search`, `stats`, `sync`
- `pull`, `push`
- `backup-workflows`, `restore-workflows`, `verify-backup`, `list-backups`

### Command Groups
- `db` - Database management commands
- `apikey` - API key management commands

## Workflow Management Commands

### `list` - List All Workflows

Display all registered workflows with their status and metadata.

```bash
n8n-deploy list [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice: table, json | table | Output format |
| `--only` | Flag | False | Show only workflows that can be backed up |
| `--table` | Flag | False | Force table output (overrides --format) |

#### Examples

```bash
# Basic workflow list
n8n-deploy list

# JSON format for scripting
n8n-deploy list --format=json

# Show only backupable workflows
n8n-deploy list --only

# Force table format with explicit flag
n8n-deploy list --table
```

#### Sample Output

```
                               Workflows
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ ID           ┃ Name            ┃ Type     ┃ Status   ┃ File Exists ┃ Backupable  ┃ Nodes ┃ Last Synced       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ THGiY5j3x... │ Main Workflow   │ main     │ active   │ ✓           │ ✓           │    12 │ 2024-09-24 10:30  │
│ 7iMYjwbkT... │ Helper Subflow  │ subflow  │ active   │ ✓           │ ✓           │     8 │ Never             │
└──────────────┴─────────────────┴──────────┴──────────┴─────────────┴─────────────┴───────┴───────────────────┘
```

### `add` - Add New Workflow

Register a new workflow for management.

```bash
n8n-deploy add WORKFLOW_ID NAME FILE_PATH [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Unique workflow identifier |
| `NAME` | Text | Yes | Human-readable workflow name |
| `FILE_PATH` | Path | Yes | Path to workflow JSON file |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice: main, subflow, utility | main | Workflow type |

#### Examples

```bash
# Add main workflow
n8n-deploy add "wf-001" "Email Processor" "workflows/email.json"

# Add subflow with explicit type
n8n-deploy add "sf-001" "Helper Functions" "workflows/helpers.json" --type subflow

# Add utility workflow
n8n-deploy add "ut-001" "Data Cleanup" "workflows/cleanup.json" --type utility
```

### `remove` - Remove Workflow

Remove workflow from management (with confirmation).

```bash
n8n-deploy remove WORKFLOW_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Workflow identifier to remove |

#### Examples

```bash
# Remove workflow (will prompt for confirmation)
n8n-deploy remove "wf-001"
```

#### Interactive Confirmation

```
Are you sure you want to remove this workflow? [y/N]: y
✅ Removed workflow: wf-001
```

### `search` - Search Workflows

Search workflows by content using full-text search.

```bash
n8n-deploy search QUERY
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `QUERY` | Text | Yes | Search query string |

#### Examples

```bash
# Search by workflow name
n8n-deploy search "email"

# Search by description content
n8n-deploy search "webhook"

# Search by tags
n8n-deploy search "automation"
```

#### Sample Output

```
                    Search Results for 'email'
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID           ┃ Name            ┃ Type     ┃ Description                                       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ THGiY5j3x... │ Email Processor │ main     │ Processes incoming emails and routes them to...   │
└──────────────┴─────────────────┴──────────┴───────────────────────────────────────────────────┘
```

### `stats` - Workflow Statistics

Show detailed statistics for a specific workflow.

```bash
n8n-deploy stats WORKFLOW_ID [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Workflow identifier |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice: table, json | table | Output format |

#### Examples

```bash
# Basic workflow statistics
n8n-deploy stats "wf-001"

# JSON format for processing
n8n-deploy stats "wf-001" --format=json
```

#### Sample Output

```
                       Workflow Stats: Email Processor
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property                              ┃ Value                                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Id                                    │ wf-001                                  │
│ Name                                  │ Email Processor                         │
│ Type                                  │ main                                    │
│ Status                                │ active                                  │
│ File Path                             │ workflows/email.json                    │
│ Node Count                            │ 12                                      │
│ Created At                            │ 2024-09-24 10:30:45                    │
│ Updated At                            │ 2024-09-24 15:22:13                    │
│ Last Synced                           │ 2024-09-24 15:22:13                    │
└───────────────────────────────────────┴─────────────────────────────────────────┘
```

### `sync` - Sync Workflow Metadata

Synchronize workflow metadata to database.

```bash
n8n-deploy sync WORKFLOW_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Workflow identifier to sync |

#### Examples

```bash
# Sync workflow metadata
n8n-deploy sync "wf-001"
```

### `pull` - Pull from n8n Server

Download workflow from n8n instance (requires API key).

```bash
n8n-deploy pull WORKFLOW_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Workflow identifier to pull |

#### Examples

```bash
# Pull workflow from n8n server
n8n-deploy pull "wf-001"
```

#### Prerequisites

```bash
# Must have API key configured
n8n-deploy apikey add n8n_server --key YOUR_API_KEY
```

### `push` - Push to n8n Server

Upload workflow to n8n instance (requires API key).

```bash
n8n-deploy push WORKFLOW_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `WORKFLOW_ID` | Text | Yes | Workflow identifier to push |

#### Examples

```bash
# Push workflow to n8n server
n8n-deploy push "wf-001"
```

## Database Management Commands

All database commands are accessed through the `db` subcommand group.

### `db init` - Initialize Database

Create and initialize the n8n-deploy database.

```bash
n8n-deploy db init
```

#### Examples

```bash
# Initialize database in current directory
n8n-deploy db init

# Initialize in custom app directory
n8n-deploy --app-dir /custom/path db init
```

### `db status` - Database Status

Show database statistics and health information.

```bash
n8n-deploy db status [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice: table, json | table | Output format |

#### Examples

```bash
# Basic database status
n8n-deploy db status

# JSON format for monitoring
n8n-deploy db status --format=json
```

#### Sample Output

```
                           Database Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property                              ┃ Value                                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Database Path                         │ /opt/n8n-deploy/n8n-deploy.db          │
│ Database Size                         │ 86,016 bytes                            │
│ Schema Version                        │ 1                                       │
│ Last Updated                          │ 2024-09-24 15:22:13                    │
└───────────────────────────────────────┴─────────────────────────────────────────┘

                          Table Statistics
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Table                                 ┃ Records                                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Workflows                             │ 15                                      │
│ Api_keys                              │ 3                                       │
│ Configurations                        │ 0                                       │
│ Schema_info                           │ 1                                       │
└───────────────────────────────────────┴─────────────────────────────────────────┘
```

### `db backup` - Create Database Backup

Create a backup of the SQLite database.

```bash
n8n-deploy db backup [BACKUP_PATH]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `BACKUP_PATH` | Path | No | Custom backup file path (default: timestamped file in backups/) |

#### Examples

```bash
# Create backup with automatic filename
n8n-deploy db backup

# Create backup at specific location
n8n-deploy db backup /backups/manual-backup.db
```

### `db vacuum` - Optimize Database Storage

Reclaim unused space and optimize database structure.

```bash
n8n-deploy db vacuum
```

#### Examples

```bash
# Optimize database storage
n8n-deploy db vacuum
```

### `db compact` - Compact Database

Compact database to optimize storage and performance.

```bash
n8n-deploy db compact
```

#### Examples

```bash
# Compact database
n8n-deploy db compact
```

## API Key Management Commands

All API key commands are accessed through the `apikey` subcommand group.

### `apikey add` - Add API Key

Store a new API key for n8n server access.

```bash
n8n-deploy apikey add NAME [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME` | Text | Yes | User-friendly name for the API key |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--key` | Text | Prompted | API key value (will be prompted securely) |
| `--description` | Text | None | Description of the API key |
| `--expires-days` | Integer | None | Number of days until expiration |

#### Examples

```bash
# Add API key (will prompt for key value)
n8n-deploy apikey add production_server

# Add with description and expiration
n8n-deploy apikey add dev_server --description "Development server key" --expires-days 30
```

#### Interactive Key Input

```
API key: ••••••••••••••••••••••••••••••••
✅ API key 'production_server' added successfully
ID: AbCdEf123456
```

### `apikey list` - List API Keys

Show all stored API keys with metadata (keys are hidden).

```bash
n8n-deploy apikey list [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice: table, json | table | Output format |

#### Examples

```bash
# List all API keys
n8n-deploy apikey list

# JSON format for scripting
n8n-deploy apikey list --format=json
```

#### Sample Output

```
                                        API Keys
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID           ┃ Name            ┃ Created             ┃ Last Used           ┃ Expires             ┃ Status   ┃ Description                    ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ AbCdEf123... │ prod_server     │ 2024-09-24 10:00   │ 2024-09-24 15:30   │ -                   │ active   │ Production server API key      │
│ XyZ789abc... │ dev_server      │ 2024-09-20 14:30   │ Never               │ 2024-10-20 14:30   │ active   │ Development server key         │
└──────────────┴─────────────────┴─────────────────────┴─────────────────────┴─────────────────────┴──────────┴────────────────────────────────┘
```

### `apikey get` - Get API Key Details

Retrieve API key information (optionally show the key value).

```bash
n8n-deploy apikey get NAME_OR_ID [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME_OR_ID` | Text | Yes | API key name or ID |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--show-key` | Flag | False | Display the actual API key value |

#### Examples

```bash
# Get API key metadata
n8n-deploy apikey get prod_server

# Show the actual key value (use with caution)
n8n-deploy apikey get prod_server --show-key
```

### `apikey test` - Test API Key

Test API key accessibility and basic validation.

```bash
n8n-deploy apikey test NAME_OR_ID
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME_OR_ID` | Text | Yes | API key name or ID |

#### Examples

```bash
# Test API key accessibility
n8n-deploy apikey test prod_server
```

#### Sample Output

```
✅ API key is accessible
   Key length: 32 characters
   Key prefix: n8n_api_...
```

### `apikey delete` - Delete API Key

Permanently delete an API key (requires confirmation).

```bash
n8n-deploy apikey delete NAME_OR_ID [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `NAME_OR_ID` | Text | Yes | API key name or ID |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--confirm` | Flag | False | Skip confirmation prompt |

#### Examples

```bash
# Delete API key (will prompt for confirmation)
n8n-deploy apikey delete old_key

# Delete without confirmation prompt
n8n-deploy apikey delete old_key --confirm
```

## Backup Operations Commands

### `backup-workflows` - Create Workflow Backup

Create a compressed backup of all registered workflows.

```bash
n8n-deploy backup-workflows [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backup-dir` | Path | ./backups | Directory to store backup |

#### Examples

```bash
# Create backup in default location
n8n-deploy backup-workflows

# Create backup in custom directory
n8n-deploy backup-workflows --backup-dir /external/backups
```

#### Sample Output

```
📦 Backup Summary:
   📁 File: workflows_backup_20240924_152213.tar.gz
   📊 Workflows: 15
   💾 Size: 245,680 bytes
   🔍 Hash: a1b2c3d4e5f6789012345678901234567890abcdef...
```

### `restore-workflows` - Restore from Backup

Restore workflows from a backup archive.

```bash
n8n-deploy restore-workflows BACKUP_FILE [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `BACKUP_FILE` | Path | Yes | Path to backup file |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | Flag | False | Skip confirmation prompt |

#### Examples

```bash
# Restore from backup (will prompt for confirmation)
n8n-deploy restore-workflows backup_20240924_152213.tar.gz

# Restore without confirmation
n8n-deploy restore-workflows backup.tar.gz --force
```

### `verify-backup` - Verify Backup Integrity

Verify the integrity of a backup file.

```bash
n8n-deploy verify-backup BACKUP_FILE
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `BACKUP_FILE` | Path | Yes | Path to backup file |

#### Examples

```bash
# Verify backup integrity
n8n-deploy verify-backup backup_20240924_152213.tar.gz
```

#### Sample Output

```
✅ Backup integrity verified
   📁 File: backup_20240924_152213.tar.gz
   🔍 SHA256: a1b2c3d4e5f6789012345678901234567890abcdef...
   📊 Workflows: 15
   💾 Size: 245,680 bytes
```

### `list-backups` - List Available Backups

Show all available workflow backups.

```bash
n8n-deploy list-backups [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | Choice: table, json | table | Output format |

#### Examples

```bash
# List all backups
n8n-deploy list-backups

# JSON format for processing
n8n-deploy list-backups --format=json
```

#### Sample Output

```
                                      Workflow Backups
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Filename                              ┃ Created           ┃ Workflows   ┃ Size        ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ workflows_backup_20240924_152213.tar.gz │ 2024-09-24 15:22 │ 15          │ 245,680     │ Tracked   │
│ workflows_backup_20240923_100000.tar.gz │ 2024-09-23 10:00 │ 12          │ 198,432     │ Tracked   │
└───────────────────────────────────────────┴───────────────────┴─────────────┴─────────────┴───────────┘
```

## Output Formats

n8n-deploy supports multiple output formats for different use cases:

### Table Format (Default)

Human-readable tables with emoji icons (can be disabled with `--no-emoji`):

```bash
n8n-deploy list
n8n-deploy --no-emoji list  # Script-friendly version
```

### JSON Format

Machine-readable JSON for scripting and automation:

```bash
n8n-deploy list --format=json
n8n-deploy db status --format=json
```

### Emoji Control

Control emoji output for different environments:

```bash
# Default: Emojis enabled for human-readable output
n8n-deploy list

# Script mode: Emojis disabled for reliable parsing
n8n-deploy --no-emoji list

# Environment variable control
export NO_EMOJI=1
n8n-deploy list
```

## Usage Examples

### Common Workflow Operations

```bash
# Initialize new n8n-deploy installation
n8n-deploy db init
n8n-deploy apikey add my_server --key YOUR_API_KEY

# Add existing workflow to management
n8n-deploy add "wf-001" "Email Processor" "workflows/email.json"

# Pull latest version from n8n server
n8n-deploy pull "wf-001"

# Make local changes and push back
n8n-deploy push "wf-001"

# Create backup before major changes
n8n-deploy backup-workflows
```

### Multi-Environment Setup

```bash
# Development environment
n8n-deploy --app-dir ~/dev/n8n-deploy --flow-dir ~/dev/workflows list

# Production environment
n8n-deploy --app-dir /opt/n8n-deploy --flow-dir /data/workflows list

# Using environment variables
export N8N_FLOW_DIR=/staging/workflows
n8n-deploy --app-dir /staging/n8n-deploy list
```

### Backup and Recovery Workflow

```bash
# Create comprehensive backup
n8n-deploy backup-workflows --backup-dir /external/backups
n8n-deploy db backup /external/backups/database-backup.db

# Verify backup integrity
n8n-deploy verify-backup /external/backups/backup_20240924_152213.tar.gz

# List available backups
n8n-deploy list-backups

# Restore if needed
n8n-deploy restore-workflows /external/backups/backup_20240924_152213.tar.gz
```

### Scripting Examples

```bash
# Get workflow count (script-friendly)
n8n-deploy --no-emoji list --format=json | jq '. | length'

# Check database health in monitoring
n8n-deploy db status --format=json | jq '.database_size'

# List expired API keys
n8n-deploy apikey list --format=json | jq '.[] | select(.status == "expired")'

# Find workflows by type
n8n-deploy --no-emoji list --format=json | jq '.[] | select(.type == "subflow")'
```

### API Key Management Workflow

```bash
# Add production API key with expiration
n8n-deploy apikey add prod_n8n \
  --description "Production n8n server" \
  --expires-days 90

# Test connectivity
n8n-deploy apikey test prod_n8n

# Monitor key usage
n8n-deploy apikey list

# Rotate expired key
n8n-deploy apikey delete old_prod_key --confirm
n8n-deploy apikey add new_prod_key --expires-days 90
```

## Environment Variables

### Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `N8N_FLOW_DIR` | Directory containing workflow files | `/data/workflows` |
| `N8N_DEPLOY_TESTING` | Testing mode flag (prevents default workflows) | `1` |

### Future Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `N8N_API_URL` | Default n8n server URL | `https://n8n.example.com` |
| `N8N_API_KEY` | Default API key | `n8n_api_key_...` |

### Environment Variable Examples

```bash
# Set workflow directory globally
export N8N_FLOW_DIR=/opt/workflows
n8n-deploy list

# Testing environment
export N8N_DEPLOY_TESTING=1
python -m pytest tests/

# Future: Default server configuration
export N8N_API_URL=https://n8n.production.com
export N8N_API_KEY=n8n_api_key_production_123
n8n-deploy pull wf-001
```

## Error Handling

n8n-deploy provides clear error messages and suggestions for common issues:

### Common Error Patterns

```bash
# Database not initialized
$ n8n-deploy list
Error: Database not found. Run 'n8n-deploy db init' first.

# Missing API key for n8n operations
$ n8n-deploy pull wf-001
Error: No API key found. Add one with 'n8n-deploy apikey add <name>'.

# Workflow file not found
$ n8n-deploy add wf-001 "Test" "missing.json"
Error: Workflow file not found: missing.json

# Permission denied
$ n8n-deploy --app-dir /readonly db init
Error: Permission denied. Check directory permissions.
```

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Command line usage error |
| 3 | Permission error |
| 4 | File not found |
| 5 | Database error |

---

This CLI reference provides comprehensive documentation for all n8n-deploy commands. For architectural details, see [ARCHITECTURE.md](ARCHITECTURE.md). For installation guidance, see [INSTALLATION.md](INSTALLATION.md).