#!/usr/bin/env python3
"""
Folder path utilities for n8n folder management

Provides pure functions for building and finding folder paths
without dependencies on HTTP client logic.
"""

from typing import Any, Dict, List, Optional


def build_folder_path(folders: List[Dict[str, Any]], folder_id: str) -> str:
    """Build full folder path from folder list.

    Traverses the folder hierarchy from the target folder up to the root,
    building the complete path.

    Args:
        folders: List of all folder dicts (must contain 'id', 'name', 'parentId')
        folder_id: Target folder ID to build path for

    Returns:
        Full path like "parent/child/folder"

    Example:
        >>> folders = [
        ...     {"id": "1", "name": "root", "parentId": None},
        ...     {"id": "2", "name": "sub", "parentId": "1"},
        ... ]
        >>> build_folder_path(folders, "2")
        'root/sub'
    """
    folder_map = {f["id"]: f for f in folders}
    path_parts: List[str] = []
    current_id: Optional[str] = folder_id

    while current_id and current_id in folder_map:
        folder = folder_map[current_id]
        path_parts.insert(0, folder.get("name", ""))
        current_id = folder.get("parentId")

    return "/".join(path_parts)


def find_folder_by_path(
    folders: List[Dict[str, Any]],
    path: str,
) -> Optional[Dict[str, Any]]:
    """Find folder by its full path.

    Searches through all folders to find one matching the given path.

    Args:
        folders: List of all folder dicts
        path: Path like "parent/child/folder"

    Returns:
        Folder dict if found, None otherwise

    Example:
        >>> folders = [{"id": "1", "name": "root", "parentId": None}]
        >>> find_folder_by_path(folders, "root")
        {'id': '1', 'name': 'root', 'parentId': None}
    """
    for folder in folders:
        folder_path = build_folder_path(folders, folder["id"])
        if folder_path == path:
            return folder
    return None


def split_path_parts(path: str) -> List[str]:
    """Split folder path into non-empty parts.

    Args:
        path: Folder path like "parent/child/folder" or "/parent/child/"

    Returns:
        List of non-empty path parts

    Example:
        >>> split_path_parts("/parent/child/folder/")
        ['parent', 'child', 'folder']
    """
    return [p for p in path.split("/") if p]
