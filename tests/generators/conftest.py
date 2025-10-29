#!/usr/bin/env python3
"""
Pytest configuration for property-based tests (Hypothesis)

Ensures all hypothesis-generated tests use temporary databases
to prevent pollution of the project database.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolated_test_environment() -> Iterator[Path]:
    """
    Automatically create isolated environment for each hypothesis test.

    This fixture runs automatically for ALL tests in this directory,
    ensuring that property-based tests cannot pollute the project database.
    """
    # Create temporary directories
    temp_app_dir = Path(tempfile.mkdtemp(prefix="n8n-deploy-hypothesis-"))
    temp_flow_dir = Path(tempfile.mkdtemp(prefix="n8n-deploy-flows-"))

    # Override environment to force tests to use temporary directories
    original_app_dir = os.environ.get("N8N_DEPLOY_DATA_DIR")
    original_flow_dir = os.environ.get("N8N_DEPLOY_FLOWS_DIR")

    os.environ["N8N_DEPLOY_TESTING"] = "1"
    os.environ["N8N_DEPLOY_DATA_DIR"] = str(temp_app_dir)
    os.environ["N8N_DEPLOY_FLOWS_DIR"] = str(temp_flow_dir)

    yield temp_app_dir

    # Cleanup: restore original environment and remove temporary directories
    os.environ.pop("N8N_DEPLOY_TESTING", None)

    if original_app_dir:
        os.environ["N8N_DEPLOY_DATA_DIR"] = original_app_dir
    else:
        os.environ.pop("N8N_DEPLOY_DATA_DIR", None)

    if original_flow_dir:
        os.environ["N8N_DEPLOY_FLOWS_DIR"] = original_flow_dir
    else:
        os.environ.pop("N8N_DEPLOY_FLOWS_DIR", None)

    # Remove temporary directories
    shutil.rmtree(temp_app_dir, ignore_errors=True)
    shutil.rmtree(temp_flow_dir, ignore_errors=True)
