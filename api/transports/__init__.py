#!/usr/bin/env python3
"""
Transport plugins for n8n-deploy script synchronization.

This module provides an extensible plugin architecture for file transfer
operations. The default transport is SCP.

Usage:
    from api.transports import PluginRegistry, TransportTarget

    # Get available plugins
    plugins = PluginRegistry.list_plugins()

    # Create a transport instance
    transport = PluginRegistry.create_instance("scp")

    # Configure target
    target = TransportTarget(
        host="example.com",
        port=22,
        username="deploy",
        base_path="/opt/n8n/scripts",
        key_file=Path("~/.ssh/id_rsa").expanduser(),
    )

    # Upload files
    result = transport.upload_files(target, files, remote_subdir="my-workflow")
"""

from .base import (
    PluginRegistry,
    ScriptSyncResult,
    TransportErrorType,
    TransportPlugin,
    TransportResult,
    TransportTarget,
)

# Import SCP transport to register it
from . import scp  # noqa: F401

__all__ = [
    "PluginRegistry",
    "ScriptSyncResult",
    "TransportErrorType",
    "TransportPlugin",
    "TransportResult",
    "TransportTarget",
]
