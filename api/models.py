#!/usr/bin/env python3
"""
Data models for wf management
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Workflow(BaseModel):
    """Core wf model"""

    id: str = Field(..., description="Unique wf identifier")
    name: str = Field(..., description="Human-readable wf name")
    file: Optional[str] = Field(None, description="Filename of the wf")
    file_folder: Optional[str] = Field(None, description="Directory where wf JSON file is located")
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
