#!/usr/bin/env python3
"""
Data models for workflow management
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SyncDirection(str, Enum):
    """Direction for folder synchronization"""

    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"


class Workflow(BaseModel):
    """Core workflow model"""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    file: Optional[str] = Field(None, description="Filename of the workflow")
    file_folder: Optional[str] = Field(None, description="Directory where workflow JSON file is located")
    server_id: Optional[int] = Field(None, description="Linked server ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.ACTIVE, description="Workflow status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    last_synced: Optional[datetime] = Field(None, description="Last sync with n8n")
    n8n_version_id: Optional[str] = Field(None, description="n8n version identifier")
    push_count: int = Field(default=0, description="Number of push operations")
    pull_count: int = Field(default=0, description="Number of pull operations")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowConfiguration(BaseModel):
    """Workflow configuration snapshots"""

    id: Optional[int] = Field(None, description="Auto-increment primary key")
    workflow_id: str = Field(..., description="Workflow identifier")
    config_type: str = Field(..., description="Configuration type (settings, credentials, variables)")
    config_data: Dict[str, Any] = Field(..., description="Configuration data")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Configuration creation time")
    is_active: bool = Field(default=True, description="Whether this configuration is active")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class DatabaseStats(BaseModel):
    """Database statistics"""

    database_path: str
    database_size: int
    schema_version: int
    tables: Dict[str, int]
    last_updated: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class N8nFolder(BaseModel):
    """n8n remote folder representation"""

    id: Optional[int] = Field(default=None, description="Local database ID")
    n8n_folder_id: str = Field(..., description="UUID from n8n server")
    n8n_project_id: str = Field(..., description="Project UUID from n8n")
    folder_path: str = Field(..., description="Full folder path, e.g., 'openminded/test'")
    server_id: int = Field(..., description="Server ID this folder belongs to")
    last_synced: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FolderMapping(BaseModel):
    """Local to remote folder mapping"""

    id: Optional[int] = Field(default=None, description="Local database ID")
    local_path: str = Field(..., description="Local directory path")
    n8n_folder_id: int = Field(..., description="Reference to n8n_folders.id")
    sync_direction: SyncDirection = Field(default=SyncDirection.BIDIRECTIONAL, description="Sync direction")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ServerCredentials(BaseModel):
    """Internal API credentials for n8n server"""

    id: Optional[int] = Field(default=None, description="Local database ID")
    server_id: int = Field(..., description="Server this credential is for")
    email: str = Field(..., description="n8n login email")
    session_cookie: Optional[str] = Field(default=None, description="Session cookie value")
    cookie_expires_at: Optional[datetime] = Field(default=None, description="Cookie expiration")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SyncResult(BaseModel):
    """Result of a folder sync operation"""

    success: bool = Field(..., description="Whether sync completed successfully")
    pushed: int = Field(default=0, description="Number of workflows pushed")
    pulled: int = Field(default=0, description="Number of workflows pulled")
    conflicts: int = Field(default=0, description="Number of conflicts detected")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
