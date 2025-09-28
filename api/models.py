#!/usr/bin/env python3
"""
Data models for workflow management
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowType(str, Enum):
    MAIN = "main"
    SUBFLOW = "subflow"
    UTILITY = "utility"


class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DependencyType(str, Enum):
    SUBFLOW = "subflow"
    WEBHOOK = "webhook"
    TRIGGER = "trigger"


class Workflow(BaseModel):
    """Core workflow model"""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    type: WorkflowType = Field(default=WorkflowType.MAIN, description="Workflow type")
    description: Optional[str] = Field(None, description="Workflow description")
    file_path: str = Field(..., description="Path to workflow JSON file")
    node_count: int = Field(default=0, description="Number of nodes in workflow")
    status: WorkflowStatus = Field(
        default=WorkflowStatus.ACTIVE, description="Workflow status"
    )
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    last_synced: Optional[datetime] = Field(None, description="Last sync with n8n")
    n8n_version_id: Optional[str] = Field(None, description="n8n version identifier")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowVersion(BaseModel):
    """Workflow version tracking"""

    id: Optional[int] = Field(None, description="Auto-increment primary key")
    workflow_id: str = Field(..., description="Workflow identifier")
    version: str = Field(..., description="Version identifier")
    changes_summary: Optional[str] = Field(None, description="Brief summary of changes")
    changes_detail: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed changes (JSON diff)"
    )
    file_hash: Optional[str] = Field(None, description="File content hash")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Version creation time"
    )
    created_by: str = Field(default="system", description="Who created this version")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowDependency(BaseModel):
    """Workflow dependencies"""

    id: Optional[int] = Field(None, description="Auto-increment primary key")
    parent_workflow_id: str = Field(..., description="Parent workflow ID")
    child_workflow_id: str = Field(..., description="Child workflow ID")
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Dependency creation time"
    )

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowConfiguration(BaseModel):
    """Workflow configuration snapshots"""

    id: Optional[int] = Field(None, description="Auto-increment primary key")
    workflow_id: str = Field(..., description="Workflow identifier")
    config_type: str = Field(
        ..., description="Configuration type (settings, credentials, variables)"
    )
    config_data: Dict[str, Any] = Field(..., description="Configuration data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Configuration creation time"
    )
    is_active: bool = Field(
        default=True, description="Whether this configuration is active"
    )

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
