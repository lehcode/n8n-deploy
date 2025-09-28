# n8n-deploy Python API Reference

> *"The first 90% of the code accounts for the first 90% of the development time. The remaining 10% of the code accounts for the other 90% of the development time."* - Tom Cargill's Rule (Programming Laws)

This document provides comprehensive documentation for using n8n-deploy as a Python library, covering all public APIs, classes, and usage patterns.

## Table of Contents

- [Overview](#overview)
- [Installation for Library Use](#installation-for-library-use)
- [Quick Start](#quick-start)
- [Configuration API](#configuration-api)
- [Database API](#database-api)
- [Workflow Manager API](#workflow-manager-api)
- [API Key Manager API](#api-key-manager-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Type Hints](#type-hints)
- [Examples](#examples)

## Overview

n8n-deploy provides a clean Python API for programmatic workflow management. The library follows modern Python practices with comprehensive type hints, Pydantic data models, and clean separation of concerns.

### Key Features

- **Type Safety**: Full mypy compatibility with strict mode
- **Modern Python**: Uses Python 3.8+ features and patterns
- **Pydantic Integration**: Comprehensive data validation and serialization
- **Context Managers**: Proper resource management
- **Clean APIs**: Intuitive method names and consistent interfaces

### Architecture Summary

```python
# High-level API structure
from api.config import get_config, n8n_deploy_Config
from api.manager import WorkflowManager
from api.n8n_deploy_db import n8n_deploy_DB
from api.api_keys import ApiKeyManager
from api.models import Workflow, WorkflowType, WorkflowStatus
```

## Installation for Library Use

Install n8n-deploy with optional dependencies for library usage:

```bash
# Basic installation
pip install n8n-deploy

# Development installation with type stubs
pip install n8n-deploy types-requests

# From source with all dependencies
pip install -e .[dev,test]
```

## Quick Start

### Basic Library Usage

```python
from api.config import get_config
from api.manager import WorkflowManager
from api.models import Workflow, WorkflowType, WorkflowStatus

# Initialize configuration
config = get_config(
    base_folder="/app/data",
    flow_folder="/workflow/files"
)

# Create manager
manager = WorkflowManager(config=config)

# List workflows
workflows = manager.list_workflows()
print(f"Found {len(workflows)} workflows")

# Add workflow
workflow_id = manager.add_workflow(
    workflow_id="wf-001",
    name="API Test Workflow",
    file_path="workflows/test.json",
    workflow_type="main"
)

# Get workflow details
workflow = manager.db.get_workflow(workflow_id)
if workflow:
    print(f"Workflow: {workflow.name} ({workflow.type})")
```

### Context Manager Usage

```python
from api.n8n_deploy_db import n8n_deploy_DB
from api.config import get_config

config = get_config()
db = n8n_deploy_DB(config=config)

# Use database with automatic connection management
with db.get_connection() as conn:
    cursor = conn.execute("SELECT COUNT(*) FROM workflows")
    count = cursor.fetchone()[0]
    print(f"Total workflows: {count}")
```

## Configuration API

### `api.config` Module

#### `n8n_deploy_Config` Class

The main configuration container for n8n-deploy paths and settings.

```python
@dataclass
class n8n_deploy_Config:
    """Configuration container for n8n_deploy_ paths and settings"""

    base_folder: Path                    # Application data directory
    flow_folder: Optional[Path] = None   # Workflow files directory

    @property
    def database_path(self) -> Path:
        """Path to the SQLite database (in app base folder)"""

    @property
    def workflows_path(self) -> Path:
        """Path to workflow files directory (in flow folder)"""

    @property
    def backups_path(self) -> Path:
        """Path to backup files directory (in app base folder)"""

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""

    def validate_paths(self) -> None:
        """Validate that paths are accessible and writable"""
```

**Usage:**

```python
from api.config import n8n_deploy_Config
from pathlib import Path

# Create configuration manually
config = n8n_deploy_Config(
    base_folder=Path("/app/data"),
    flow_folder=Path("/workflow/files")
)

# Access computed paths
print(f"Database: {config.database_path}")
print(f"Workflows: {config.workflows_path}")
print(f"Backups: {config.backups_path}")

# Ensure directories exist and are writable
config.ensure_directories()
config.validate_paths()
```

#### `get_config()` Function

Factory function for creating configurations with priority resolution.

```python
def get_config(
    base_folder: Optional[Union[str, Path]] = None,
    flow_folder: Optional[Union[str, Path]] = None,
) -> n8n_deploy_Config:
    """Get n8n_deploy_ configuration with priority order"""
```

**Usage:**

```python
from api.config import get_config

# Use defaults (current directory)
config = get_config()

# Specify custom paths
config = get_config(
    base_folder="/opt/n8n-deploy",
    flow_folder="/data/workflows"
)

# Mix of explicit and environment-based
import os
os.environ['N8N_FLOW_DIR'] = "/env/workflows"
config = get_config(base_folder="/custom/app")  # Uses env for flow_folder
```

## Database API

### `api.n8n_deploy_db` Module

#### `n8n_deploy_DB` Class

The main database manager for workflow metadata and API keys.

```python
class n8n_deploy_DB:
    """n8n_deploy_ database manager - where workflows transform and mature"""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        config: Optional[n8n_deploy_Config] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize database with configuration or explicit path"""

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections"""

    def close(self) -> None:
        """Close database connection"""
```

#### Workflow Operations

```python
# Create workflow
def create_workflow(self, workflow: Workflow) -> str:
    """Create a new workflow record"""

# Read workflow
def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
    """Get a workflow by ID"""

# List workflows
def list_workflows(
    self,
    status: Optional[str] = None,
    workflow_type: Optional[str] = None
) -> List[Workflow]:
    """List workflows with optional filtering"""

# Update workflow
def update_workflow(self, workflow: Workflow) -> bool:
    """Update an existing workflow"""

# Delete workflow
def delete_workflow(self, workflow_id: str) -> bool:
    """Delete a workflow and its dependencies"""
```

#### Search Operations

```python
def search_workflows(self, query: str) -> List[Workflow]:
    """Search workflows using full-text search"""

def rebuild_search_index(self) -> None:
    """Rebuild the full-text search index"""
```

#### Database Maintenance

```python
def get_database_stats(self) -> DatabaseStats:
    """Get comprehensive database statistics"""

def vacuum(self) -> None:
    """Reclaim unused space (VACUUM)"""

def compact(self) -> None:
    """Compact database for optimal performance"""

def backup(self, backup_path: str) -> None:
    """Create database backup"""
```

**Usage Examples:**

```python
from api.n8n_deploy_db import n8n_deploy_DB
from api.models import Workflow, WorkflowType, WorkflowStatus
from api.config import get_config

# Initialize database
config = get_config()
db = n8n_deploy_DB(config=config)

# Create workflow
workflow = Workflow(
    id="wf-001",
    name="Test Workflow",
    type=WorkflowType.MAIN,
    status=WorkflowStatus.ACTIVE,
    file_path="workflows/test.json"
)

workflow_id = db.create_workflow(workflow)
print(f"Created workflow: {workflow_id}")

# Get workflow
retrieved = db.get_workflow(workflow_id)
if retrieved:
    print(f"Retrieved: {retrieved.name}")

# Search workflows
results = db.search_workflows("test")
print(f"Search found {len(results)} workflows")

# Database maintenance
stats = db.get_database_stats()
print(f"Database size: {stats.database_size} bytes")
print(f"Total workflows: {stats.tables.get('workflows', 0)}")

# Clean up
db.vacuum()
db.close()
```

## Workflow Manager API

### `api.manager` Module

#### `WorkflowManager` Class

High-level workflow management with business logic orchestration.

```python
class WorkflowManager:
    """Main workflow management class"""

    def __init__(
        self,
        config: Optional[n8n_deploy_Config] = None,
        base_path: Optional[Path] = None,  # Legacy compatibility
    ) -> None:
        """Initialize with configuration or legacy base path"""

    # Core workflow operations
    def add_workflow(
        self,
        workflow_id: str,
        name: str,
        file_path: str,
        workflow_type: str = "main"
    ) -> str:
        """Add new workflow to management"""

    def remove_workflow(self, workflow_id: str) -> bool:
        """Remove workflow from management"""

    def list_workflows(self, only_backupable: bool = False) -> List[Dict[str, Any]]:
        """List all workflows with enhanced metadata"""

    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow statistics"""

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows by content"""

    def sync_to_database(self, workflow_id: str) -> bool:
        """Sync workflow metadata to database"""
```

#### n8n Integration Methods

```python
# n8n server operations (requires API keys)
def pull_workflow(self, workflow_id: str) -> bool:
    """Pull workflow from n8n instance"""

def push_workflow(self, workflow_id: str) -> bool:
    """Push workflow to n8n instance"""

def sync_with_n8n(self, workflow_id: str) -> bool:
    """Bidirectional sync with n8n server"""
```

#### Backup Operations

```python
def backup_all_workflows(
    self,
    backup_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Create tar.gz backup of all registered workflows"""

def restore_workflows_backup(
    self,
    backup_file: Path,
    force: bool = False
) -> bool:
    """Restore workflows from tar.gz backup"""

def verify_backup_integrity(self, backup_file: Path) -> bool:
    """Verify backup file integrity"""

def list_backups(self) -> List[Dict[str, Any]]:
    """List all available workflow backups"""
```

**Usage Examples:**

```python
from api.manager import WorkflowManager
from api.config import get_config

# Initialize manager
config = get_config(
    base_folder="/app/data",
    flow_folder="/workflows"
)
manager = WorkflowManager(config=config)

# Add workflow
workflow_id = manager.add_workflow(
    workflow_id="wf-api-001",
    name="API Example Workflow",
    file_path="workflows/api-example.json",
    workflow_type="main"
)

# List workflows with metadata
workflows = manager.list_workflows()
for wf in workflows:
    print(f"Workflow: {wf['name']} - Backupable: {wf['backupable']}")

# Get detailed statistics
stats = manager.get_workflow_stats(workflow_id)
print(f"Node count: {stats['node_count']}")
print(f"File exists: {stats['file_exists']}")

# Search functionality
results = manager.search_workflows("email")
print(f"Found {len(results)} workflows containing 'email'")

# Backup operations
backup_metadata = manager.backup_all_workflows()
print(f"Backup created: {backup_metadata['filename']}")
print(f"Workflows backed up: {backup_metadata['workflow_count']}")

# Verify backup
is_valid = manager.verify_backup_integrity(
    Path(backup_metadata['filename'])
)
print(f"Backup integrity: {'Valid' if is_valid else 'Invalid'}")
```

## API Key Manager API

### `api.api_keys` Module

#### `ApiKey` Dataclass

```python
@dataclass
class ApiKey:
    """API Key data model"""

    id: str
    name: str
    plain_key: str                      # API key in plain text
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    description: Optional[str] = None
```

#### `ApiKeyManager` Class

```python
class ApiKeyManager:
    """API key storage and management"""

    def __init__(self, config: Optional[n8n_deploy_Config] = None) -> None:
        """Initialize with configuration"""

    def add_api_key(
        self,
        name: str,
        api_key: str,
        description: Optional[str] = None,
        expires_days: Optional[int] = None,
        service: str = "n8n",  # For compatibility
    ) -> str:
        """Add a new API key to storage"""

    def get_api_key(
        self,
        key_id_or_name: str,
        update_last_used: bool = True
    ) -> Optional[str]:
        """Retrieve API key by ID or name"""

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all stored API keys metadata"""

    def deactivate_api_key(self, key_id_or_name: str) -> bool:
        """Deactivate an API key (soft delete)"""

    def delete_api_key(self, key_id_or_name: str, confirm: bool = False) -> bool:
        """Permanently delete an API key"""

    def test_api_key(self, key_id_or_name: str) -> bool:
        """Test if an API key is valid and accessible"""
```

**Usage Examples:**

```python
from api.api_keys import ApiKeyManager
from api.config import get_config
from datetime import datetime, timedelta

# Initialize API key manager
config = get_config()
api_manager = ApiKeyManager(config=config)

# Add API key
key_id = api_manager.add_api_key(
    name="production_server",
    api_key="n8n_api_key_production_123",
    description="Production n8n server API key",
    expires_days=90
)
print(f"Added API key: {key_id}")

# Get API key for use
api_key = api_manager.get_api_key("production_server")
if api_key:
    print(f"Retrieved key: {api_key[:8]}...")

# List all API keys
keys = api_manager.list_api_keys()
for key_info in keys:
    print(f"Key: {key_info['name']} - Status: {key_info['status']}")

# Test API key accessibility
is_accessible = api_manager.test_api_key("production_server")
print(f"Key accessible: {is_accessible}")

# Deactivate expired key
api_manager.deactivate_api_key("old_key")

# Permanently delete key
api_manager.delete_api_key("unused_key", confirm=True)
```

## Data Models

### `api.models` Module

n8n-deploy uses Pydantic v2 for comprehensive data validation and serialization.

#### Enums

```python
class WorkflowType(str, Enum):
    MAIN = "main"        # Primary workflows
    SUBFLOW = "subflow"  # Reusable components
    UTILITY = "utility"  # Helper workflows

class WorkflowStatus(str, Enum):
    ACTIVE = "active"      # Currently in use
    INACTIVE = "inactive"  # Temporarily disabled
    ARCHIVED = "archived"  # Long-term storage

class DependencyType(str, Enum):
    SUBFLOW = "subflow"
    WEBHOOK = "webhook"
    TRIGGER = "trigger"
```

#### Core Models

```python
class Workflow(BaseModel):
    """Core workflow model"""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    type: WorkflowType = Field(default=WorkflowType.MAIN)
    description: Optional[str] = None
    file_path: str = Field(..., description="Path to workflow JSON file")
    node_count: int = Field(default=0)
    status: WorkflowStatus = Field(default=WorkflowStatus.ACTIVE)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced: Optional[datetime] = None
    n8n_version_id: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}
```

#### Extended Models

```python
class WorkflowVersion(BaseModel):
    """Workflow version tracking"""

    id: Optional[int] = None
    workflow_id: str
    version: str
    changes_summary: Optional[str] = None
    changes_detail: Dict[str, Any] = Field(default_factory=dict)
    file_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="system")

class WorkflowDependency(BaseModel):
    """Workflow dependencies"""

    id: Optional[int] = None
    parent_workflow_id: str
    child_workflow_id: str
    dependency_type: DependencyType
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DatabaseStats(BaseModel):
    """Database statistics"""

    database_path: str
    database_size: int
    schema_version: int
    tables: Dict[str, int]
    last_updated: datetime
```

**Usage Examples:**

```python
from api.models import Workflow, WorkflowType, WorkflowStatus
from datetime import datetime

# Create workflow model
workflow = Workflow(
    id="wf-model-001",
    name="Model Example Workflow",
    type=WorkflowType.MAIN,
    status=WorkflowStatus.ACTIVE,
    file_path="workflows/model-example.json",
    node_count=15,
    tags=["automation", "email", "api"]
)

# Access model properties
print(f"Workflow ID: {workflow.id}")
print(f"Type: {workflow.type}")  # Uses enum value
print(f"Created: {workflow.created_at}")

# JSON serialization
workflow_json = workflow.model_dump_json()
print(f"JSON: {workflow_json}")

# Create from dictionary
workflow_data = {
    "id": "wf-dict-001",
    "name": "From Dict Workflow",
    "file_path": "workflows/dict.json"
}
workflow_from_dict = Workflow(**workflow_data)
print(f"From dict: {workflow_from_dict.name}")

# Validation
try:
    invalid_workflow = Workflow(
        id="",  # Invalid: empty ID
        name="Invalid Workflow",
        file_path=""  # Invalid: empty file path
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

## Error Handling

n8n-deploy uses a hierarchical error handling approach with specific exceptions for different layers.

### Common Exceptions

```python
# Standard Python exceptions
ValueError          # Data validation errors
FileNotFoundError  # Missing workflow files
PermissionError    # Directory access issues
sqlite3.Error      # Database operation errors

# Click CLI exceptions (when using CLI integration)
import click
click.ClickException    # User-friendly CLI errors
click.UsageError       # Command usage errors
```

### Error Handling Patterns

```python
from api.manager import WorkflowManager
from api.config import get_config
import sqlite3

try:
    # Configuration errors
    config = get_config(
        base_folder="/nonexistent/path"
    )
    manager = WorkflowManager(config=config)

except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle invalid paths, permissions, etc.

try:
    # Database errors
    workflow = manager.db.get_workflow("nonexistent-id")

except sqlite3.Error as e:
    print(f"Database error: {e}")
    # Handle database connectivity, corruption, etc.

try:
    # Workflow file errors
    manager.add_workflow(
        "wf-001",
        "Test",
        "nonexistent.json"
    )

except FileNotFoundError as e:
    print(f"File error: {e}")
    # Handle missing workflow files

except PermissionError as e:
    print(f"Permission error: {e}")
    # Handle directory access issues
```

### Defensive Programming

```python
from api.n8n_deploy_db import n8n_deploy_DB
from api.config import get_config

def safe_database_operation():
    """Example of safe database operations"""
    config = get_config()
    db = None

    try:
        db = n8n_deploy_DB(config=config)

        # Use context manager for connection safety
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM workflows")
            count = cursor.fetchone()[0]
            return count

    except Exception as e:
        print(f"Database operation failed: {e}")
        return 0

    finally:
        if db:
            db.close()

# Usage
workflow_count = safe_database_operation()
print(f"Safe count: {workflow_count}")
```

## Advanced Usage

### Custom Configuration Classes

```python
from api.config import n8n_deploy_Config
from pathlib import Path
import os

class ProductionConfig(n8n_deploy_Config):
    """Production-specific configuration"""

    def __init__(self):
        super().__init__(
            base_folder=Path("/opt/n8n-deploy"),
            flow_folder=Path("/data/workflows")
        )

    def validate_paths(self) -> None:
        """Enhanced validation for production"""
        super().validate_paths()

        # Additional production checks
        if os.getenv("ENV") != "production":
            raise ValueError("Production config requires ENV=production")

        # Check disk space
        stat = os.statvfs(self.base_folder)
        free_gb = (stat.f_frsize * stat.f_available) // (1024**3)
        if free_gb < 1:
            raise ValueError(f"Insufficient disk space: {free_gb}GB")

# Usage
prod_config = ProductionConfig()
```

### Custom Workflow Processing

```python
from api.manager import WorkflowManager
from api.models import Workflow
import json

class EnhancedWorkflowManager(WorkflowManager):
    """Extended workflow manager with custom processing"""

    def analyze_workflow_complexity(self, workflow_id: str) -> Dict[str, Any]:
        """Analyze workflow complexity metrics"""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Load workflow file for analysis
        workflow_file = self.config.workflows_path / workflow.file_path

        try:
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            return {"error": "Workflow file not found"}

        # Analyze complexity
        nodes = workflow_data.get('nodes', [])
        connections = workflow_data.get('connections', {})

        return {
            "node_count": len(nodes),
            "connection_count": sum(len(conns) for conns in connections.values()),
            "complexity_score": len(nodes) * 2 + sum(len(conns) for conns in connections.values()),
            "node_types": list(set(node.get('type', 'unknown') for node in nodes)),
            "has_webhooks": any(node.get('type') == 'webhook' for node in nodes),
            "has_schedules": any(node.get('type') in ['cron', 'schedule'] for node in nodes)
        }

# Usage
enhanced_manager = EnhancedWorkflowManager(config=get_config())
complexity = enhanced_manager.analyze_workflow_complexity("wf-001")
print(f"Complexity score: {complexity['complexity_score']}")
```

### Bulk Operations

```python
from api.manager import WorkflowManager
from api.config import get_config
from pathlib import Path
import json

def bulk_import_workflows(workflow_dir: Path, manager: WorkflowManager):
    """Import all workflows from a directory"""
    imported = []
    errors = []

    for workflow_file in workflow_dir.glob("*.json"):
        try:
            # Load workflow data to get ID and name
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)

            workflow_id = workflow_data.get('id')
            workflow_name = workflow_data.get('name', workflow_file.stem)

            if not workflow_id:
                errors.append(f"No ID in {workflow_file}")
                continue

            # Add to management
            manager.add_workflow(
                workflow_id=workflow_id,
                name=workflow_name,
                file_path=str(workflow_file.relative_to(manager.config.base_folder)),
                workflow_type="main"
            )

            imported.append(workflow_id)

        except Exception as e:
            errors.append(f"Failed to import {workflow_file}: {e}")

    return {
        "imported": imported,
        "errors": errors,
        "total": len(imported)
    }

# Usage
config = get_config()
manager = WorkflowManager(config=config)
result = bulk_import_workflows(Path("/import/workflows"), manager)
print(f"Imported {result['total']} workflows")
for error in result['errors']:
    print(f"Error: {error}")
```

## Type Hints

n8n-deploy provides comprehensive type hints for all public APIs:

### Type Import Examples

```python
from typing import Optional, List, Dict, Any, Union, Iterator
from pathlib import Path
from datetime import datetime

# n8n-deploy specific types
from api.models import Workflow, WorkflowType, WorkflowStatus
from api.config import n8n_deploy_Config
```

### Custom Type Definitions

```python
from typing import TypedDict, Protocol

class WorkflowMetadata(TypedDict):
    """Type definition for workflow metadata"""
    id: str
    name: str
    type: str
    status: str
    file_exists: bool
    backupable: bool
    node_count: int
    last_synced: Optional[datetime]

class WorkflowProcessor(Protocol):
    """Protocol for custom workflow processors"""

    def process_workflow(self, workflow: Workflow) -> bool:
        """Process a workflow and return success status"""
        ...

# Usage with type checking
def process_workflows(
    workflows: List[Workflow],
    processor: WorkflowProcessor
) -> Dict[str, Any]:
    """Process workflows with type safety"""
    results = {"successful": 0, "failed": 0}

    for workflow in workflows:
        try:
            if processor.process_workflow(workflow):
                results["successful"] += 1
            else:
                results["failed"] += 1
        except Exception:
            results["failed"] += 1

    return results
```

## Examples

### Complete Application Example

```python
#!/usr/bin/env python3
"""
Complete n8n-deploy API usage example
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from api.config import get_config
from api.manager import WorkflowManager
from api.models import Workflow, WorkflowType, WorkflowStatus
from api.api_keys import ApiKeyManager

def main():
    """Main application example"""

    # 1. Configuration
    print("🔧 Setting up configuration...")
    config = get_config(
        base_folder="/tmp/n8n-deploy-example",
        flow_folder="/tmp/workflows-example"
    )

    # Ensure directories exist
    config.ensure_directories()
    print(f"   App directory: {config.base_folder}")
    print(f"   Flow directory: {config.workflows_path}")

    # 2. Initialize managers
    print("\n📊 Initializing managers...")
    manager = WorkflowManager(config=config)
    api_manager = ApiKeyManager(config=config)

    # 3. API Key management
    print("\n🔐 Managing API keys...")
    key_id = api_manager.add_api_key(
        name="example_server",
        api_key="example_api_key_123",
        description="Example n8n server",
        expires_days=30
    )
    print(f"   Added API key: {key_id}")

    # List API keys
    keys = api_manager.list_api_keys()
    print(f"   Total API keys: {len(keys)}")

    # 4. Create example workflow file
    print("\n📄 Creating example workflow...")
    workflow_file = config.workflows_path / "example.json"
    example_workflow = {
        "id": "example-workflow-001",
        "name": "Example API Workflow",
        "nodes": [
            {
                "id": "node-1",
                "type": "start",
                "name": "Start"
            },
            {
                "id": "node-2",
                "type": "webhook",
                "name": "Webhook"
            }
        ],
        "connections": {
            "Start": {
                "main": [["Webhook"]]
            }
        }
    }

    with open(workflow_file, 'w') as f:
        json.dump(example_workflow, f, indent=2)

    # 5. Add workflow to management
    print("\n➕ Adding workflow to management...")
    workflow_id = manager.add_workflow(
        workflow_id="example-workflow-001",
        name="Example API Workflow",
        file_path="example.json",
        workflow_type="main"
    )
    print(f"   Added workflow: {workflow_id}")

    # 6. List and analyze workflows
    print("\n📋 Analyzing workflows...")
    workflows = manager.list_workflows()
    print(f"   Total workflows: {len(workflows)}")

    for wf in workflows:
        print(f"   - {wf['name']}: {wf['type']} ({wf['status']})")

    # Get detailed stats
    stats = manager.get_workflow_stats(workflow_id)
    print(f"   Workflow stats: {stats['node_count']} nodes")

    # 7. Search functionality
    print("\n🔍 Testing search...")
    results = manager.search_workflows("example")
    print(f"   Search results: {len(results)} workflows found")

    # 8. Database operations
    print("\n🗄️ Database operations...")
    db_stats = manager.db.get_database_stats()
    print(f"   Database size: {db_stats.database_size:,} bytes")
    print(f"   Workflows in DB: {db_stats.tables.get('workflows', 0)}")

    # 9. Backup operations
    print("\n📦 Creating backup...")
    backup_metadata = manager.backup_all_workflows()
    print(f"   Backup file: {backup_metadata['filename']}")
    print(f"   Workflows backed up: {backup_metadata['workflow_count']}")

    # Verify backup integrity
    backup_file = config.backups_path / backup_metadata['filename']
    is_valid = manager.verify_backup_integrity(backup_file)
    print(f"   Backup integrity: {'✅ Valid' if is_valid else '❌ Invalid'}")

    # 10. Cleanup
    print("\n🧹 Cleaning up...")
    manager.db.close()

    print("\n✅ Example completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
```

### Testing Helper Example

```python
"""
Testing helper utilities for n8n-deploy API
"""

import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

from api.config import get_config, n8n_deploy_Config
from api.manager import WorkflowManager

@contextmanager
def temporary_n8n_deploy():
    """Context manager for temporary n8n-deploy setup"""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create temporary configuration
        config = n8n_deploy_Config(
            base_folder=temp_dir / "app",
            flow_folder=temp_dir / "workflows"
        )
        config.ensure_directories()

        # Create manager
        manager = WorkflowManager(config=config)

        yield manager, config

    finally:
        # Cleanup
        manager.db.close()
        shutil.rmtree(temp_dir)

# Usage in tests
def test_workflow_operations():
    """Test workflow operations with temporary setup"""

    with temporary_n8n_deploy() as (manager, config):
        # Test operations
        workflow_id = manager.add_workflow(
            "test-001",
            "Test Workflow",
            "test.json"
        )

        workflows = manager.list_workflows()
        assert len(workflows) == 1
        assert workflows[0]['id'] == "test-001"

        # Manager and config automatically cleaned up

# Run test
test_workflow_operations()
print("✅ Test passed!")
```

---

This API reference provides comprehensive documentation for using n8n-deploy as a Python library. For CLI usage, see [CLI-REFERENCE.md](CLI-REFERENCE.md). For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).