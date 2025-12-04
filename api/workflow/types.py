#!/usr/bin/env python3
"""
Typed response models for n8n API operations

Provides structured result types that distinguish between different
error conditions (404 not found, network errors, auth failures, etc.)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class N8nApiErrorType(str, Enum):
    """Types of n8n API errors"""

    NOT_FOUND = "not_found"  # 404 - workflow doesn't exist on server
    AUTH_FAILURE = "auth_failure"  # 401/403 - authentication/authorization failed
    SERVER_ERROR = "server_error"  # 5xx - server-side error
    NETWORK_ERROR = "network_error"  # Connection errors
    TIMEOUT = "timeout"  # Request timeout
    UNKNOWN = "unknown"  # Other errors


@dataclass
class N8nApiResult:
    """Result of an n8n API call with error type information

    Allows callers to distinguish between different error conditions,
    particularly important for differentiating 404 (stale ID) from
    network errors during push operations.
    """

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_type: Optional[N8nApiErrorType] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None

    @property
    def is_not_found(self) -> bool:
        """Check if result represents a 404 Not Found"""
        return self.error_type == N8nApiErrorType.NOT_FOUND

    @property
    def is_network_error(self) -> bool:
        """Check if result represents a network/connection error"""
        return self.error_type in (N8nApiErrorType.NETWORK_ERROR, N8nApiErrorType.TIMEOUT)

    @property
    def is_auth_error(self) -> bool:
        """Check if result represents an authentication/authorization error"""
        return self.error_type == N8nApiErrorType.AUTH_FAILURE

    @property
    def is_server_error(self) -> bool:
        """Check if result represents a server-side error"""
        return self.error_type == N8nApiErrorType.SERVER_ERROR
