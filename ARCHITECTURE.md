# n8n-deploy Architecture Documentation

> *"The first rule of intelligent tinkering is to save all the parts."* - Paul Ehrlich's Rule (Murphy's Computer Laws)

## Overview

n8n-deploy implements a **database-first architecture** with a clean 3-layer separation of concerns. The design prioritizes simplicity, reliability, and local-only operation while providing comprehensive workflow management capabilities.

## Core Design Principles

### 1. Database-First Architecture
- **SQLite as Single Source of Truth**: All workflow metadata lives in the database
- **File System Integration**: Files complement but never replace database records
- **Atomic Operations**: Database transactions ensure consistency
- **Schema Evolution**: Versioned migrations support future enhancements

### 2. Privacy-First Design
- **Local-Only Storage**: No external service dependencies
- **Plain Text API Keys**: Simple, accessible storage without encryption complexity
- **Zero Telemetry**: No usage tracking, performance metrics, or external calls
- **File System Permissions**: Relies on OS-level security

### 3. Configuration Flexibility
- **Dual Directory System**: Separate app data from user workflow files
- **Environment Variable Support**: N8N_FLOW_DIR for workflow file location
- **CLI Override Options**: Runtime configuration via --app-dir and --flow-dir
- **Legacy Compatibility**: Seamless migration from older configurations

## 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (api/cli.py)                    │
├─────────────────────────────────────────────────────────────┤
│  • Click command groups and decorators                       │
│  • Rich console output with emoji/no-emoji modes            │
│  • Global configuration management via context              │
│  • Error handling with user-friendly messages               │
│  • Table formatting and JSON output options                 │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                 Manager Layer (api/manager.py)               │
├─────────────────────────────────────────────────────────────┤
│  • WorkflowManager: Core business logic orchestration       │
│  • File system operations and workflow file management      │
│  • n8n API integration (pull/push operations)              │
│  • Backup/restore operations with tar.gz + SHA256          │
│  • API key coordination and credential management           │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│               Database Layer (api/n8n_deploy_db.py)          │
├─────────────────────────────────────────────────────────────┤
│  • n8n_deploy_DB: SQLite operations and schema management   │
│  • Connection pooling with WAL mode optimization           │
│  • CRUD operations with Pydantic model integration         │
│  • Full-text search with FTS5 virtual tables               │
│  • Database maintenance (vacuum, compact, backup)          │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Configuration System (api/config.py)

The configuration system provides flexible path resolution with clear priority ordering:

```python
@dataclass
class n8n_deploy_Config:
    base_folder: Path      # App data: database, backups
    flow_folder: Path      # User workflow files (optional)

    @property
    def database_path(self) -> Path:
        return self.base_folder / "n8n-deploy.db"

    @property
    def workflows_path(self) -> Path:
        if self.flow_folder:
            return self.flow_folder / "workflows"
        return self.base_folder / "n8n"  # Legacy fallback
```

**Priority Resolution:**

**Base Folder (app data):**
1. CLI `--app-dir` parameter (highest priority)
2. Current working directory (default)

**Flow Folder (workflow files):**
1. CLI `--flow-dir` parameter (highest priority)
2. `N8N_FLOW_DIR` environment variable
3. Same as base folder (legacy compatibility)

### Data Models (api/models.py)

The project uses Pydantic v2 for comprehensive data validation and serialization:

```python
class WorkflowType(str, Enum):
    MAIN = "main"        # Primary workflows
    SUBFLOW = "subflow"  # Reusable components
    UTILITY = "utility"  # Helper workflows

class WorkflowStatus(str, Enum):
    ACTIVE = "active"      # Currently in use
    INACTIVE = "inactive"  # Temporarily disabled
    ARCHIVED = "archived"  # Long-term storage

class Workflow(BaseModel):
    id: str                           # n8n workflow identifier
    name: str                        # Human-readable name
    type: WorkflowType = MAIN        # Workflow category
    file_path: str                   # Relative path to JSON file
    status: WorkflowStatus = ACTIVE  # Current status
    tags: List[str] = []            # Classification tags
    created_at: datetime            # Initial creation
    updated_at: datetime            # Last modification
    last_synced: Optional[datetime] # Last n8n sync
    n8n_version_id: Optional[str]   # n8n version tracking
```

### Database Schema

The SQLite schema consists of 6 tables with careful normalization and indexing:

#### Core Tables

**1. workflows** - Primary workflow metadata
```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,              -- n8n workflow ID
    name TEXT NOT NULL,               -- Display name
    type TEXT DEFAULT 'main',         -- WorkflowType enum
    description TEXT,                 -- Optional description
    file_path TEXT NOT NULL,          -- Relative file path
    node_count INTEGER DEFAULT 0,     -- Workflow complexity metric
    status TEXT DEFAULT 'active',     -- WorkflowStatus enum
    tags TEXT,                        -- JSON array of tags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_synced DATETIME,            -- Last n8n synchronization
    n8n_version_id TEXT              -- n8n version tracking
);
```

**2. api_keys** - Simple API key storage
```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,             -- Unique key identifier
    name TEXT NOT NULL,              -- User-friendly name
    api_key TEXT NOT NULL,           -- Plain text API key
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME,              -- Usage tracking
    expires_at DATETIME,             -- Optional expiration
    is_active BOOLEAN DEFAULT 1,     -- Soft delete flag
    description TEXT                 -- Optional description
);
```

**3. configurations** - Workflow configuration snapshots
```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,       -- Foreign key to workflows.id
    config_type TEXT NOT NULL,       -- 'settings', 'credentials', 'variables'
    config_data TEXT NOT NULL,       -- JSON configuration data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,     -- Active configuration flag
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);
```

#### Schema Tables (Future Features)

**4. versions** - Workflow version tracking (schema-only)
**5. dependencies** - Workflow dependency mapping (schema-only)
**6. schema_info** - Database versioning for migrations

#### Full-Text Search Integration

```sql
-- FTS5 virtual table for content search
CREATE VIRTUAL TABLE workflows_fts USING fts5(
    id, name, description, tags,
    content=workflows,
    content_rowid=rowid
);

-- Automatic triggers maintain search index
CREATE TRIGGER workflows_fts_insert AFTER INSERT ON workflows BEGIN
    INSERT INTO workflows_fts(rowid, id, name, description, tags)
    VALUES (new.rowid, new.id, new.name, new.description, new.tags);
END;
```

#### Performance Optimization

**Strategic Indexing:**
```sql
-- Query optimization indexes
CREATE INDEX idx_workflows_type ON workflows(type);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_updated ON workflows(updated_at);
CREATE INDEX idx_configurations_workflow ON configurations(workflow_id);
CREATE INDEX idx_api_keys_name ON api_keys(name);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

**Database Optimization:**
- **WAL Mode**: Write-Ahead Logging for better concurrency
- **PRAGMA synchronous = NORMAL**: Balanced safety/performance
- **Foreign Key Enforcement**: Data integrity with ON DELETE CASCADE
- **Connection Reuse**: Single connection per manager instance

### API Key Management (api/api_keys.py)

The API key system prioritizes simplicity and accessibility:

```python
@dataclass
class ApiKey:
    id: str                          # Unique identifier
    name: str                        # User-friendly name
    plain_key: str                   # Actual API key (no encryption)
    created_at: datetime            # Creation timestamp
    last_used: Optional[datetime]   # Usage tracking
    expires_at: Optional[datetime]  # Optional expiration
    is_active: bool = True          # Soft delete flag
    description: Optional[str]      # Optional description

class ApiKeyManager:
    def add_api_key(self, name: str, api_key: str, ...) -> str:
        """Store API key in plain text with metadata"""

    def get_api_key(self, key_id_or_name: str) -> Optional[str]:
        """Retrieve API key by ID or name with expiration check"""

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all keys with metadata (excludes actual key values)"""
```

**Design Decisions:**
- **Plain Text Storage**: No encryption complexity, relies on file system security
- **No Service Categorization**: Simplified schema focused on n8n API keys
- **Expiration Support**: Optional time-based key expiration
- **Usage Tracking**: Last used timestamps for key management

### Backup System Architecture

The backup system provides comprehensive workflow archival with integrity verification:

```python
def backup_all_workflows(self, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Create tar.gz backup with metadata tracking"""

    # 1. Validate all workflow files exist
    workflows = self.list_workflows(only_backupable=True)

    # 2. Create tar.gz archive with workflow files
    backup_path = backup_dir or self.config.backups_path
    backup_file = backup_path / f"workflows_backup_{timestamp}.tar.gz"

    # 3. Generate SHA256 hash for integrity verification
    file_hash = hashlib.sha256(backup_content).hexdigest()

    # 4. Store backup metadata in database
    metadata = {
        'filename': backup_file.name,
        'workflow_count': len(workflows),
        'file_size': backup_file.stat().st_size,
        'sha256_hash': file_hash,
        'timestamp': datetime.now()
    }

    return metadata
```

**Backup Features:**
- **Selective Backup**: Only workflows with existing files
- **Integrity Verification**: SHA256 checksums stored in database
- **Metadata Tracking**: Complete backup history with workflow counts
- **Atomic Operations**: Database transactions ensure consistency
- **Compression**: Gzip compression for efficient storage

### CLI Interface Design

The CLI layer provides both human-friendly and script-compatible interfaces:

```python
@click.group()
@click.option("--app-dir", help="Application directory")
@click.option("--flow-dir", help="Flow folder for workflow files")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output")
@click.version_option(version="2.0.0")
def cli(ctx: click.Context, app_dir: str, flow_dir: str, no_emoji: bool):
    """Global configuration and emoji preference"""
    ctx.obj = {
        "no_emoji": no_emoji,
        "config": get_config(base_folder=app_dir, flow_folder=flow_dir)
    }
```

**Interface Patterns:**
- **Context Management**: Configuration passed through Click context
- **Dual Output Modes**: Rich tables with emoji OR plain text for scripts
- **Format Options**: Table and JSON output for programmatic use
- **Error Handling**: Click exceptions with user-friendly messages

## Data Flow Architecture

### Workflow Management Flow

```
User Command → CLI Parser → Manager Logic → Database Operations → File System
     ↓              ↓             ↓              ↓                    ↓
  click.Context → WorkflowManager → n8n_deploy_DB → SQLite + Files
```

**Example: Adding a Workflow**

1. **CLI Layer**: `n8n-deploy add workflow-id "Name" "path/to/file.json"`
2. **Manager Layer**: `WorkflowManager.add_workflow()` validates file existence
3. **Database Layer**: `n8n_deploy_DB.create_workflow()` stores metadata
4. **File System**: Workflow JSON remains in user-specified location

### Configuration Resolution Flow

```
CLI Options → Environment Variables → Defaults → Path Validation → Config Object
     ↓               ↓                   ↓             ↓              ↓
  --app-dir      N8N_FLOW_DIR      Current Dir  → Path.exists() → n8n_deploy_Config
```

### API Key Lifecycle

```
Add Key → Store Plain Text → Usage Tracking → Expiration Check → Soft Delete
    ↓           ↓                 ↓               ↓               ↓
CLI Input → Database Insert → Update last_used → Check expires_at → is_active=0
```

## Testing Architecture

### Test Environment Control

The testing system uses environment variables to prevent side effects:

```python
# Set in test files and CI environment
os.environ["N8N_DEPLOY_TESTING"] = "1"

# Prevents default workflow initialization in WorkflowManager
if not os.getenv("N8N_DEPLOY_TESTING"):
    self._ensure_default_workflows()
```

### Test Categories

**Unit Tests** (`tests/unit/`):
- **Component Isolation**: Mock external dependencies
- **Model Validation**: Pydantic schema testing
- **Database Operations**: SQLite transaction testing
- **Configuration Logic**: Path resolution testing

**Integration Tests** (`tests/integration/`):
- **CLI Commands**: End-to-end command testing
- **File System Operations**: Real file/directory operations
- **Database Integration**: Full workflow lifecycle testing
- **Backup/Restore**: Complete backup system validation

### CI/CD Environment Considerations

**Permission-Agnostic Testing:**
```python
# ❌ Unreliable in CI (may succeed with root permissions)
def test_mkdir_fail():
    with pytest.raises(PermissionError):
        os.mkdir("/nonexistent/path")

# ✅ Reliable across environments (filesystem constraint)
def test_mkdir_fail():
    with pytest.raises(NotADirectoryError):
        os.mkdir("/dev/null/invalid_path")
```

The CI environment runs in Docker containers with elevated permissions, so tests must be designed to work in both user and container environments.

## Performance Considerations

### Database Optimization

**Connection Management:**
```python
@contextmanager
def get_connection(self) -> Iterator[sqlite3.Connection]:
    """Reuse connection with optimized settings"""
    if self._connection is None:
        self._connection = sqlite3.connect(str(self.db_path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = NORMAL")
```

**Query Optimization:**
- **Strategic Indexing**: Indexes on commonly queried columns
- **Row Factory**: Efficient column access via sqlite3.Row
- **Connection Reuse**: Single connection per manager instance
- **WAL Mode**: Better concurrency for read-heavy workloads

### File System Performance

**Path Resolution Caching:**
- Configuration objects cache resolved paths
- Path validation occurs once during initialization
- Relative paths resolved against base configuration

**Backup Optimization:**
- **Selective Archival**: Only backup workflows with existing files
- **Streaming Operations**: Process files without loading entirely into memory
- **Compression**: Gzip compression reduces storage requirements

## Security Architecture

### Threat Model

**Assets Protected:**
- API keys for n8n servers
- Workflow metadata and files
- Database integrity

**Trust Assumptions:**
- **File System Security**: OS-level permissions protect database and files
- **Local Environment**: Tool runs on trusted local machine
- **Network Security**: n8n server connections secured externally

### Security Measures

**API Key Storage:**
```python
# Plain text storage - relies on file system permissions
api_key = self.get_api_key("server_name")  # Retrieved directly from database
```

**Database Security:**
- **File Permissions**: SQLite database protected by OS permissions
- **Foreign Key Constraints**: Prevent data integrity issues
- **Parameterized Queries**: Protection against SQL injection

**Input Validation:**
- **Pydantic Models**: Comprehensive data validation
- **Path Validation**: Ensure paths are accessible and writable
- **Click Parameters**: Type validation and constraints

## Extensibility Points

### Database Schema Evolution

The schema versioning system supports future enhancements:

```sql
CREATE TABLE schema_info (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Migration Pattern:**
```python
SCHEMA_VERSION = 2  # Increment for new features

def _initialize_database(self):
    # Apply migrations based on current version
    current_version = self._get_current_schema_version()
    if current_version < self.SCHEMA_VERSION:
        self._apply_migrations(current_version, self.SCHEMA_VERSION)
```

### Plugin Architecture Preparation

**Manager Layer Extensions:**
```python
class WorkflowManager:
    def __init__(self, config: n8n_deploy_Config, plugins: List[Plugin] = None):
        self.plugins = plugins or []
        # Plugin hooks for workflow operations
```

**CLI Command Extensions:**
```python
# Future plugin commands can extend CLI groups
@cli.group()
def plugin_group():
    """Plugin-specific commands"""
    pass
```

### Future Enhancement Areas

**Planned Features (Schema Tables Ready):**
1. **Version Tracking**: Full workflow version history with diffs
2. **Dependency Mapping**: Workflow relationship tracking
3. **Configuration Management**: Environment-specific settings
4. **Plugin System**: Custom workflow processing extensions

**API Integration Expansion:**
- **Multiple n8n Servers**: Server profile management
- **Webhook Management**: Endpoint configuration tracking
- **Credential Management**: Secure credential storage options

## Error Handling Strategy

### Exception Hierarchy

```python
# CLI Layer: User-friendly Click exceptions
raise click.ClickException("Database initialization failed")

# Manager Layer: Business logic exceptions
raise ValueError("Workflow file not found: {file_path}")

# Database Layer: Data operation exceptions
raise sqlite3.IntegrityError("Workflow ID already exists")
```

### Error Recovery Patterns

**Database Operations:**
```python
with self.get_connection() as conn:
    try:
        conn.execute("INSERT INTO workflows ...")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("Workflow already exists")
```

**File Operations:**
```python
try:
    workflow_content = json.loads(workflow_file.read_text())
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise click.ClickException(f"Invalid workflow file: {e}")
```

## Deployment Architecture

### Package Distribution

**Python Package Structure:**
```
n8n-deploy/
├── api/                    # Main package
│   ├── __init__.py
│   ├── cli.py             # Entry point
│   ├── manager.py         # Core logic
│   ├── n8n_deploy_db.py   # Database layer
│   ├── config.py          # Configuration
│   ├── api_keys.py        # Key management
│   └── models.py          # Data models
├── tests/                 # Test suite
├── pyproject.toml         # PEP 621 metadata
└── setup.sh              # Global alias installer
```

**Entry Point Configuration:**
```toml
[project.scripts]
n8n-deploy = "api.cli:main"
```

### GitLab CI/CD Pipeline Architecture

**Pipeline Stages:**
1. **Quality**: Type checking, formatting, coverage
2. **Security**: Secret detection, SAST scanning
3. **Test**: Unit and integration test execution
4. **Build Matrix**: Multi-version Python testing
5. **Build**: Production package creation

**Artifact Management:**
- **Test Reports**: JUnit XML and coverage reports
- **Package Distributions**: Wheel and source packages
- **Docker Images**: Containerized build environments

---

This architecture documentation provides a comprehensive technical overview of n8n-deploy's design decisions, component interactions, and extensibility planning. The system prioritizes simplicity, reliability, and local-only operation while maintaining professional software engineering standards.