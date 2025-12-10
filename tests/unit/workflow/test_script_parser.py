"""Unit tests for api/workflow/script_parser.py module

Tests for WorkflowScriptParser class methods.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from assertpy import assert_that

from api.workflow.script_parser import ScriptReference, WorkflowScriptParser


class TestWorkflowScriptParser:
    """Tests for WorkflowScriptParser class"""

    def test_init_with_dict(self) -> None:
        """Test WorkflowScriptParser initialization with dict"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [],
        }
        parser = WorkflowScriptParser(workflow_data)
        assert_that(parser.workflow_data).is_equal_to(workflow_data)

    def test_find_execute_command_nodes_empty(self) -> None:
        """Test finding execute command nodes in empty workflow"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [],
        }
        parser = WorkflowScriptParser(workflow_data)
        nodes = parser.find_execute_command_nodes()
        assert_that(nodes).is_empty()

    def test_find_execute_command_nodes_no_execute_commands(self) -> None:
        """Test finding execute command nodes when none exist"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "n8n-nodes-base.start", "name": "Start"},
                {"id": "node2", "type": "n8n-nodes-base.function", "name": "Function"},
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        nodes = parser.find_execute_command_nodes()
        assert_that(nodes).is_empty()

    def test_find_execute_command_nodes_with_execute_commands(self) -> None:
        """Test finding execute command nodes"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "n8n-nodes-base.start", "name": "Start"},
                {
                    "id": "node2",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script",
                    "parameters": {"command": "python /opt/scripts/test.py"},
                },
                {"id": "node3", "type": "n8n-nodes-base.function", "name": "Function"},
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        nodes = parser.find_execute_command_nodes()
        assert_that(nodes).is_length(1)
        assert_that(nodes[0]["id"]).is_equal_to("node2")

    def test_extract_script_path_python_quoted(self) -> None:
        """Test extracting Python script path with quoted path"""
        command = 'python "/opt/scripts/processor.py" --input data'
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/processor.py")

    def test_extract_script_path_python_unquoted(self) -> None:
        """Test extracting Python script path without quotes"""
        command = "python /opt/scripts/processor.py --input data"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/processor.py")

    def test_extract_script_path_node_js(self) -> None:
        """Test extracting Node.js script path"""
        command = "node /opt/scripts/helper.js"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/helper.js")

    def test_extract_script_path_cjs(self) -> None:
        """Test extracting CommonJS script path"""
        command = "node /opt/scripts/utility.cjs"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/utility.cjs")

    def test_extract_script_path_direct_script(self) -> None:
        """Test extracting direct script invocation"""
        command = "/opt/scripts/run.py"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/run.py")

    def test_extract_script_path_no_script(self) -> None:
        """Test no script found in command"""
        command = "echo hello world"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_none()

    def test_extract_script_path_unsupported_extension(self) -> None:
        """Test script with unsupported extension"""
        command = "bash /opt/scripts/test.sh"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_none()

    def test_extract_script_path_with_n8n_expression(self) -> None:
        """Test extracting script path with n8n expression placeholder"""
        command = "python /opt/scripts/processor.py --data {{ $json.data }}"
        parser = WorkflowScriptParser({"nodes": []})
        path = parser.extract_script_path(command)
        assert_that(path).is_equal_to("/opt/scripts/processor.py")

    def test_extract_all_script_paths(self) -> None:
        """Test extracting multiple script paths from command"""
        command = "python /opt/scripts/first.py && node /opt/scripts/second.js"
        parser = WorkflowScriptParser({"nodes": []})
        paths = parser.extract_all_script_paths(command)
        assert_that(paths).is_length(2)
        assert_that(paths).contains("/opt/scripts/first.py", "/opt/scripts/second.js")

    def test_parse_scripts_full_workflow(self) -> None:
        """Test parsing scripts from full workflow"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {"id": "node1", "type": "n8n-nodes-base.start", "name": "Start"},
                {
                    "id": "node2",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Python",
                    "parameters": {"command": "python /opt/scripts/processor.py"},
                },
                {
                    "id": "node3",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run JS",
                    "parameters": {"command": "node /opt/scripts/helper.js"},
                },
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        scripts = parser.parse_scripts()

        assert_that(scripts).is_length(2)
        assert_that(scripts[0].script_path).is_equal_to("/opt/scripts/processor.py")
        assert_that(scripts[0].node_name).is_equal_to("Run Python")
        assert_that(scripts[1].script_path).is_equal_to("/opt/scripts/helper.js")
        assert_that(scripts[1].node_name).is_equal_to("Run JS")

    def test_parse_scripts_no_command_parameter(self) -> None:
        """Test parsing node without command parameter"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Empty",
                    "parameters": {},
                },
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        scripts = parser.parse_scripts()
        assert_that(scripts).is_empty()

    def test_get_script_filenames(self) -> None:
        """Test getting unique script filenames"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script 1",
                    "parameters": {"command": "python /opt/scripts/processor.py"},
                },
                {
                    "id": "node2",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script 2",
                    "parameters": {"command": "python /different/path/processor.py"},
                },
                {
                    "id": "node3",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script 3",
                    "parameters": {"command": "node /opt/scripts/helper.js"},
                },
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        filenames = parser.get_script_filenames()

        # processor.py appears twice but should only be in set once
        assert_that(filenames).is_length(2)
        assert_that(filenames).contains("processor.py", "helper.js")

    def test_get_script_paths(self) -> None:
        """Test getting full script paths"""
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script",
                    "parameters": {"command": "python /opt/scripts/processor.py"},
                },
            ],
        }
        parser = WorkflowScriptParser(workflow_data)
        paths = parser.get_script_paths()

        assert_that(paths).is_length(1)
        assert_that(paths).contains("/opt/scripts/processor.py")


class TestScriptReference:
    """Tests for ScriptReference dataclass"""

    def test_script_reference_creation(self) -> None:
        """Test ScriptReference dataclass creation"""
        ref = ScriptReference(
            node_id="node1",
            node_name="Run Script",
            script_path="/opt/scripts/test.py",
            extension=".py",
            command_raw="python /opt/scripts/test.py",
        )
        assert_that(ref.node_id).is_equal_to("node1")
        assert_that(ref.node_name).is_equal_to("Run Script")
        assert_that(ref.script_path).is_equal_to("/opt/scripts/test.py")
        assert_that(ref.extension).is_equal_to(".py")
        assert_that(ref.command_raw).is_equal_to("python /opt/scripts/test.py")

    def test_script_reference_filename_property(self) -> None:
        """Test ScriptReference filename property"""
        ref = ScriptReference(
            node_id="node1",
            node_name="Run Script",
            script_path="/opt/scripts/nested/test.py",
            extension=".py",
            command_raw="python test.py",
        )
        assert_that(ref.filename).is_equal_to("test.py")
