#!/usr/bin/env python3
"""
Parse n8n workflow JSON for Execute Command nodes and extract script references.

This module analyzes workflow JSON to find external scripts (.js, .cjs, .py)
referenced in Execute Command nodes.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class ScriptReference:
    """A reference to an external script in a workflow."""

    node_id: str
    node_name: str
    script_path: str  # Path extracted from command
    extension: str  # .js, .cjs, or .py
    command_raw: str  # Original command string

    @property
    def filename(self) -> str:
        """Extract filename from script path."""
        return Path(self.script_path).name

    @property
    def is_absolute(self) -> bool:
        """Check if the script path is absolute."""
        return self.script_path.startswith("/")


class WorkflowScriptParser:
    """Parse n8n workflow JSON for script references in Execute Command nodes."""

    # Node type for Execute Command
    EXECUTE_COMMAND_TYPE = "n8n-nodes-base.executeCommand"

    # Supported script extensions
    SUPPORTED_EXTENSIONS: Set[str] = {".js", ".cjs", ".py"}

    # Regex patterns for script path extraction (ordered by specificity)
    SCRIPT_PATTERNS: List[re.Pattern[str]] = [
        # Quoted paths with interpreters: python "/path/to/script.py"
        re.compile(r'(?:python3?|node)\s+["\']([^"\']+\.(?:js|cjs|py))["\']'),
        # Quoted paths standalone: "/path/to/script.py"
        re.compile(r'["\']([^"\']+\.(?:js|cjs|py))["\']'),
        # Direct interpreter invocation: python /path/to/script.py
        re.compile(r"(?:python3?|node)\s+([^\s&|;\"']+\.(?:js|cjs|py))"),
        # Script path in command: /path/to/script.py args
        re.compile(r"([^\s&|;\"']+\.(?:js|cjs|py))"),
    ]

    def __init__(self, workflow_data: Dict[str, Any]) -> None:
        """Initialize parser with workflow JSON data.

        Args:
            workflow_data: Parsed n8n workflow JSON
        """
        self.workflow_data = workflow_data
        self.workflow_id: str = str(workflow_data.get("id", "unknown"))
        self.workflow_name: str = str(workflow_data.get("name", "Unknown"))

    def find_execute_command_nodes(self) -> List[Dict[str, Any]]:
        """Find all Execute Command nodes in the workflow.

        Returns:
            List of node dictionaries with type 'n8n-nodes-base.executeCommand'
        """
        nodes = self.workflow_data.get("nodes", [])
        return [node for node in nodes if node.get("type") == self.EXECUTE_COMMAND_TYPE]

    def extract_script_path(self, command: str) -> Optional[str]:
        """Extract script path from command string.

        Args:
            command: The command string from Execute Command node

        Returns:
            Script path if found and has supported extension, None otherwise
        """
        for pattern in self.SCRIPT_PATTERNS:
            match = pattern.search(command)
            if match:
                path = match.group(1)
                ext = Path(path).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    return path
        return None

    def extract_all_script_paths(self, command: str) -> List[str]:
        """Extract all script paths from command string.

        Some commands might reference multiple scripts.

        Args:
            command: The command string from Execute Command node

        Returns:
            List of script paths found
        """
        paths: List[str] = []
        seen: Set[str] = set()

        for pattern in self.SCRIPT_PATTERNS:
            for match in pattern.finditer(command):
                path = match.group(1)
                ext = Path(path).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS and path not in seen:
                    paths.append(path)
                    seen.add(path)

        return paths

    def parse_scripts(self) -> List[ScriptReference]:
        """Parse workflow and extract all script references.

        Returns:
            List of ScriptReference objects for each script found
        """
        references: List[ScriptReference] = []

        for node in self.find_execute_command_nodes():
            command = node.get("parameters", {}).get("command", "")
            if not command:
                continue

            # Handle n8n expressions - extract literal parts
            # Expressions like {{ $json.script }} are skipped
            if "{{" in command and "}}" in command:
                # Try to extract literal script paths around expressions
                literal_parts = re.split(r"\{\{[^}]+\}\}", command)
                command = " ".join(literal_parts)

            for script_path in self.extract_all_script_paths(command):
                ext = Path(script_path).suffix.lower()
                ref = ScriptReference(
                    node_id=str(node.get("id", "")),
                    node_name=str(node.get("name", "")),
                    script_path=script_path,
                    extension=ext,
                    command_raw=str(node.get("parameters", {}).get("command", "")),
                )
                references.append(ref)

        return references

    def get_script_filenames(self) -> Set[str]:
        """Get unique script filenames referenced in workflow.

        Returns:
            Set of script filenames (basename only)
        """
        return {ref.filename for ref in self.parse_scripts()}

    def get_script_paths(self) -> Set[str]:
        """Get unique script paths referenced in workflow.

        Returns:
            Set of full script paths as written in the workflow
        """
        return {ref.script_path for ref in self.parse_scripts()}


def parse_workflow_scripts(workflow_json_path: Path) -> List[ScriptReference]:
    """Convenience function to parse scripts from workflow file.

    Args:
        workflow_json_path: Path to workflow JSON file

    Returns:
        List of ScriptReference objects

    Raises:
        FileNotFoundError: If workflow file doesn't exist
        json.JSONDecodeError: If workflow file is not valid JSON
    """
    with open(workflow_json_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)

    parser = WorkflowScriptParser(workflow_data)
    return parser.parse_scripts()


def parse_workflow_data_scripts(workflow_data: Dict[str, Any]) -> List[ScriptReference]:
    """Parse scripts from workflow data dictionary.

    Args:
        workflow_data: Parsed workflow JSON data

    Returns:
        List of ScriptReference objects
    """
    parser = WorkflowScriptParser(workflow_data)
    return parser.parse_scripts()
