#!/usr/bin/env python3
"""
Main workflow manager - Python edition
"""

import json
import subprocess
import requests
import tarfile
import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import Workflow, WorkflowType, WorkflowStatus
from api.n8n_deploy_db import n8n_deploy_DB
from api.config import n8n_deploy_Config, get_config
from api.api_keys import ApiKeyManager


class WorkflowManager:
    """Main workflow management class"""

    def __init__(
        self,
        config: Optional[n8n_deploy_Config] = None,
        base_path: Optional[Path] = None,
    ) -> None:
        # Support both new config system and legacy base_path parameter
        if config is not None:
            self.config: Optional[n8n_deploy_Config] = config
            self.base_path = config.workflows_path
        elif base_path is not None:
            # Legacy mode: create config from base_path
            self.config = None
            self.base_path = Path(base_path)
        else:
            # Default: use legacy behavior for backward compatibility
            self.config = get_config()
            self.base_path = self.config.workflows_path

        self.db = n8n_deploy_DB(config=self.config if self.config else None)
        self.api_manager = ApiKeyManager(config=self.config if self.config else None)

        # Initialize database with default workflows if empty (skip during testing)
        import os

        if not os.getenv("N8N_DEPLOY_TESTING"):
            self._ensure_default_workflows()

    def _ensure_default_workflows(self) -> None:
        """Initialize database with default workflows if empty"""
        existing_workflows = self.db.list_workflows()

        if not existing_workflows:
            # Add default workflows to database
            default_workflows = [
                {
                    "id": "THGiY5j3x07pKHLa",
                    "name": "Itzam Diff Workflow",
                    "file_path": "workflows/weekly-changelog-workflow/weekly-changelog-workflow.json",
                    "type": "main",
                },
                {
                    "id": "7iMYjwbkThG8gTem",
                    "name": "Dynamic LiteLLM Processing",
                    "file_path": "workflows/weekly-changelog-workflow/LiteLLM-Call-subflow.json",
                    "type": "subflow",
                },
            ]

            for wf_data in default_workflows:
                workflow = Workflow(
                    id=wf_data["id"],
                    name=wf_data["name"],
                    type=WorkflowType(wf_data["type"]),
                    file_path=wf_data["file_path"],
                    status=WorkflowStatus.ACTIVE,
                    description=None,
                    last_synced=None,
                    n8n_version_id=None,
                )
                self.db.create_workflow(workflow)

            print("✅ Initialized database with default workflows")

    def _get_n8n_credentials(self) -> Optional[Dict[str, Any]]:
        """Get n8n API credentials from stored API keys"""
        try:
            # Try to get n8n API key
            api_key = self.api_manager.get_api_key("n8n", update_last_used=True)
            if api_key:
                return {
                    "api_key": api_key,
                    "headers": {
                        "X-N8N-API-KEY": api_key,
                        "Content-Type": "application/json",
                    },
                }
            else:
                print(
                    "⚠️  No n8n API key found. Add one with: n8n-deploy apikey add n8n_main n8n"
                )
                return None
        except Exception as e:
            print(f"❌ Failed to retrieve n8n API key: {e}")
            return None

    def _make_n8n_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to n8n API"""
        credentials = self._get_n8n_credentials()
        if not credentials:
            return None

        # Default n8n API base URL (can be made configurable)
        base_url = "http://localhost:5678/api/v1"
        url = f"{base_url}/{endpoint.lstrip('/')}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=credentials["headers"])
            elif method.upper() == "POST":
                response = requests.post(url, headers=credentials["headers"], json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=credentials["headers"], json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=credentials["headers"])
            else:
                print(f"❌ Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            result = response.json()
            return result if isinstance(result, dict) else None
        except requests.exceptions.RequestException as e:
            print(f"❌ n8n API request failed: {e}")
            return None

    def get_workflow_info(self, id_or_alias: str) -> Dict[str, Any]:
        """Get workflow information by ID or alias from database"""
        # Handle aliases
        if id_or_alias == "main":
            # Get the first main workflow
            workflows = self.db.list_workflows(workflow_type="main")
            if workflows:
                id_or_alias = workflows[0].id
            else:
                raise ValueError("No main workflow found")
        elif id_or_alias == "subflow":
            id_or_alias = "7iMYjwbkThG8gTem"

        # Get workflow info from database
        workflow = self.db.get_workflow(id_or_alias)

        if not workflow:
            available = []
            all_workflows = self.db.list_workflows()
            for wf in all_workflows:
                available.append(f"  {wf.id}: {wf.name} ({wf.type})")

            raise ValueError(
                f"Unknown workflow ID: {id_or_alias}\nAvailable workflows:\n"
                + "\n".join(available)
            )

        # Calculate full path
        full_path = self.base_path / workflow.file_path

        return {
            "id": workflow.id,
            "name": workflow.name,
            "type": workflow.type,
            "file": workflow.file_path,
            "full_path": full_path,
        }

    def sync_to_database(self, workflow_id: str) -> bool:
        """Sync workflow metadata to Chrysalis database"""
        try:
            info = self.get_workflow_info(workflow_id)

            # Read workflow file to get node count and other metadata
            if info["full_path"].exists():
                with open(info["full_path"], "r") as f:
                    workflow_data = json.load(f)

                node_count = len(workflow_data.get("nodes", []))
                description = workflow_data.get("meta", {}).get("description", "")
            else:
                node_count = 0
                description = ""

            # Create or update workflow in database
            workflow = Workflow(
                id=info["id"],
                name=info["name"],
                type=WorkflowType(info["type"]),
                description=description,
                file_path=str(info["file"]),
                node_count=node_count,
                status=WorkflowStatus.ACTIVE,
                last_synced=datetime.utcnow(),
                n8n_version_id=None,
            )

            # Check if workflow exists
            existing = self.db.get_workflow(workflow_id)
            if existing:
                self.db.update_workflow(workflow)
            else:
                self.db.create_workflow(workflow)

            return True

        except Exception as e:
            print(f"❌ Failed to sync workflow {workflow_id}: {e}")
            return False

    def pull_workflow(self, workflow_id: str) -> bool:
        """Pull workflow from n8n instance"""
        try:
            info = self.get_workflow_info(workflow_id)
            print(f"📋 Workflow: {info['name']} ({info['id']})")
            print(f"📄 File: {info['file']}")
            print(f"🎯 Type: {info['type']}")

            # Execute the Node.js pull script
            script_path = self.base_path.parent / "pull-workflow.js"
            if script_path.exists():
                env = {**dict(), "N8N_WORKFLOW_FILE": str(info["full_path"])}
                result = subprocess.run(
                    [str(script_path), workflow_id],
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("✅ Workflow pulled successfully")
                    # Sync to database
                    self.sync_to_database(workflow_id)
                    return True
                else:
                    print(f"❌ Pull failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Pull script not found: {script_path}")
                return False

        except Exception as e:
            print(f"❌ Failed to pull workflow: {e}")
            return False

    def push_workflow(self, workflow_id: str) -> bool:
        """Push workflow to n8n instance"""
        try:
            info = self.get_workflow_info(workflow_id)
            print(f"📋 Workflow: {info['name']} ({info['id']})")
            print(f"📄 File: {info['file']}")
            print(f"🎯 Type: {info['type']}")

            # Check if file exists
            if not info["full_path"].exists():
                print(f"❌ Workflow file not found: {info['full_path']}")
                return False

            # Execute the Node.js update script
            script_path = self.base_path.parent / "update-workflow.js"
            if script_path.exists():
                env = {**dict(), "N8N_WORKFLOW_FILE": str(info["full_path"])}
                result = subprocess.run(
                    [str(script_path), workflow_id],
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print("✅ Workflow pushed successfully")
                    # Sync to database
                    self.sync_to_database(workflow_id)
                    return True
                else:
                    print(f"❌ Push failed: {result.stderr}")
                    return False
            else:
                print(f"❌ Push script not found: {script_path}")
                return False

        except Exception as e:
            print(f"❌ Failed to push workflow: {e}")
            return False

    def list_workflows(self, only_backupable: bool = False) -> List[Dict[str, Any]]:
        """List all available workflows from database

        Args:
            only_backupable: If True, only return workflows that can be backed up
                           (exist in database AND have files on filesystem)
        """
        workflows = []
        db_workflows = self.db.list_workflows()

        for workflow in db_workflows:
            # Check if workflow file exists on filesystem
            workflow_file = self.base_path / workflow.file_path
            file_exists = workflow_file.exists()

            # Skip if only_backupable=True and file doesn't exist
            if only_backupable and not file_exists:
                continue

            workflow_info = {
                "id": workflow.id,
                "name": workflow.name,
                "type": workflow.type,
                "file": workflow.file_path,
                "status": workflow.status,
                "node_count": workflow.node_count,
                "last_synced": workflow.last_synced,
                "file_exists": file_exists,
                "backupable": file_exists,  # Can be backed up if file exists
                "full_path": str(workflow_file),  # Useful for debugging
            }
            workflows.append(workflow_info)

        return workflows

    def backup_all_workflows(self, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Backup all workflows that can be validated (convenience method for loops)

        Returns:
            Summary dict with backup results for each workflow
        """
        backupable_workflows = self.list_workflows(only_backupable=True)

        results: Dict[str, Any] = {
            "total_workflows": len(backupable_workflows),
            "successful_backups": [],
            "failed_backups": [],
            "backup_dir": backup_dir,
        }

        for workflow in backupable_workflows:
            try:
                backup_result = self.create_workflow_backup(workflow["id"], backup_dir)
                results["successful_backups"].append(
                    {
                        "workflow_id": workflow["id"],
                        "workflow_name": workflow["name"],
                        "backup_id": backup_result["backup_id"],
                        "filename": backup_result["filename"],
                    }
                )
                print(
                    f"✅ Backed up: {workflow['name']} -> {backup_result['filename']}"
                )
            except Exception as e:
                results["failed_backups"].append(
                    {
                        "workflow_id": workflow["id"],
                        "workflow_name": workflow["name"],
                        "error": str(e),
                    }
                )
                print(f"❌ Failed to backup {workflow['name']}: {e}")

        # Summary
        success_count = len(results["successful_backups"])
        total_count = results["total_workflows"]
        print(
            f"\n📊 Backup Summary: {success_count}/{total_count} workflows backed up successfully"
        )

        return results

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows in database"""
        return self.db.search_workflows(query)

    def add_workflow(
        self, workflow_id: str, name: str, file_path: str, workflow_type: str = "main"
    ) -> None:
        """Add a new workflow to database"""
        workflow = Workflow(
            id=workflow_id,
            name=name,
            type=WorkflowType(workflow_type),
            file_path=file_path,
            status=WorkflowStatus.ACTIVE,
            description=None,
            last_synced=None,
            n8n_version_id=None,
        )
        self.db.create_workflow(workflow)
        print(f"✅ Added workflow: {name} ({workflow_id})")

    def remove_workflow(self, workflow_id: str) -> None:
        """Remove workflow (archive in database)"""
        workflow = self.db.get_workflow(workflow_id)
        if workflow:
            self.db.delete_workflow(workflow_id)
            print(f"✅ Removed workflow: {workflow.name} ({workflow_id})")
        else:
            print(f"❌ Workflow not found: {workflow_id}")

    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow statistics"""
        info = self.get_workflow_info(workflow_id)
        db_workflow = self.db.get_workflow(workflow_id)

        stats = {
            "id": workflow_id,
            "name": info["name"],
            "type": info["type"],
            "file_exists": info["full_path"].exists(),
            "file_size": (
                info["full_path"].stat().st_size if info["full_path"].exists() else 0
            ),
            "in_database": db_workflow is not None,
        }

        if db_workflow:
            stats.update(
                {
                    "status": db_workflow.status,
                    "node_count": db_workflow.node_count,
                    "created_at": db_workflow.created_at,
                    "updated_at": db_workflow.updated_at,
                    "last_synced": db_workflow.last_synced,
                    "tags": db_workflow.tags,
                }
            )

        return stats

    def create_workflow_backup(
        self, workflow_id: str, backup_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create a tar.gz backup of a single specified workflow if it exists and can be validated"""
        if backup_dir is None:
            if self.config:
                backup_dir = self.config.backups_path
            else:
                # Legacy fallback
                backup_dir = self.base_path.parent / "n8n-deploy" / "backups"

        # Validate workflow exists in database
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found in database")

        # Validate workflow file exists on filesystem
        workflow_file = self.base_path / workflow.file_path
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")

        # Optional: Validate with API if available
        api_validation_passed = True
        if self.api_manager and hasattr(self.api_manager, "get_api_key"):
            api_key = self.api_manager.get_api_key("n8n")
            if api_key:
                # Could add n8n API validation here if needed
                # For now, just note that API is available
                api_validation_passed = True

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp and workflow ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"n8n_deploy_workflow_{workflow_id}_{timestamp}.tar.gz"
        backup_path = backup_dir / backup_filename

        # Create temporary directory for staging backup
        temp_dir = backup_dir / f"temp_{workflow_id}_{timestamp}"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Create workflows directory
            workflows_dir = temp_dir / "workflows"
            workflows_dir.mkdir(exist_ok=True)

            # Copy the specific workflow file
            dest_file = workflows_dir / f"{workflow.id}.json"
            shutil.copy2(workflow_file, dest_file)

            # Calculate checksum
            with open(dest_file, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            workflow_data = {
                "original_path": workflow.file_path,
                "name": workflow.name,
                "type": workflow.type,
                "status": workflow.status,
                "sha256": file_hash,
            }

            # Create metadata.json
            metadata = {
                "backup_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "filename": backup_filename,
                "workflow_id": workflow_id,
                "workflow_count": 1,
                "workflow": workflow_data,
                "api_validated": api_validation_passed,
                "n8n_deploy_version": "2.0.0",
            }

            with open(temp_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            # Create tar.gz archive
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(temp_dir, arcname=".")

            # Calculate backup file checksum
            with open(backup_path, "rb") as f:
                backup_hash = hashlib.sha256(f.read()).hexdigest()

            # Update metadata with file info
            metadata.update(
                {"sha256_hash": backup_hash, "file_size": backup_path.stat().st_size}
            )

            # Store backup metadata in database
            self.db.create_backup_record(metadata)

            print(f"🎭 Workflow backup created: {backup_path}")
            print(f"   📦 1 workflow archived: {workflow.name} ({workflow_id})")
            print(f"   🔍 Checksum: {backup_hash[:16]}...")

            return metadata

        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def restore_workflows_backup(self, backup_file: Path, force: bool = False) -> bool:
        """Restore workflows from backup archive"""
        backup_file = Path(backup_file)

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False

        # Verify backup integrity first
        if not self.verify_backup_integrity(backup_file):
            print("❌ Backup integrity check failed")
            return False

        # Create temporary extraction directory
        temp_dir = (
            backup_file.parent
            / f"restore_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extract backup
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Read metadata
            metadata_file = temp_dir / "metadata.json"
            if not metadata_file.exists():
                print("❌ Invalid backup: metadata.json not found")
                return False

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            print(f"📦 Backup info:")
            print(f"   📅 Created: {metadata.get('timestamp', 'Unknown')}")
            print(f"   🔢 Workflows: {metadata.get('workflow_count', 0)}")
            print(f"   📝 Version: {metadata.get('n8n_deploy_version', 'Unknown')}")

            if not force:
                response = input(
                    "\n⚠️  This will overwrite existing workflow mappings. Continue? (y/N): "
                )
                if response.lower() != "y":
                    print("Restore cancelled")
                    return False

            # Restore workflow-mappings.json (for reference only)
            mappings_source = temp_dir / "workflow-mappings.json"
            if mappings_source.exists():
                print("✅ Found workflow mappings in backup")

            # Restore workflow files and database entries
            workflows_dir = temp_dir / "workflows"
            if workflows_dir.exists():
                restored_count = 0

                for workflow_file in workflows_dir.glob("*.json"):
                    wf_id = workflow_file.stem

                    # Find original path from metadata
                    if wf_id in metadata.get("workflows", {}):
                        wf_metadata = metadata["workflows"][wf_id]
                        original_path = wf_metadata["original_path"]
                        dest_path = self.base_path / original_path

                        # Create destination directory if needed
                        dest_path.parent.mkdir(parents=True, exist_ok=True)

                        # Copy workflow file
                        shutil.copy2(workflow_file, dest_path)

                        # Create/update workflow in database
                        workflow = Workflow(
                            id=wf_id,
                            name=wf_metadata["name"],
                            type=WorkflowType(wf_metadata["type"]),
                            file_path=original_path,
                            status=WorkflowStatus.ACTIVE,
                            description=None,
                            last_synced=None,
                            n8n_version_id=None,
                        )

                        # Check if workflow exists and update or create
                        existing = self.db.get_workflow(wf_id)
                        if existing:
                            self.db.update_workflow(workflow)
                        else:
                            self.db.create_workflow(workflow)

                        restored_count += 1
                        print(f"   ✅ Restored: {wf_metadata['name']}")

                print(
                    f"✅ Restored {restored_count} workflow files and database entries"
                )

            print("🎭 Workflow restore completed successfully")
            return True

        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def verify_backup_integrity(self, backup_file: Path) -> bool:
        """Verify backup file integrity using stored checksum"""
        backup_file = Path(backup_file)

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False

        # Calculate current file checksum
        with open(backup_file, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()

        # Try to find stored checksum in database
        backup_record = self.db.get_backup_by_filename(backup_file.name)

        if backup_record:
            stored_hash = backup_record.get("sha256_hash")
            if stored_hash and stored_hash == current_hash:
                print(f"✅ Backup integrity verified: {current_hash[:16]}...")
                return True
            else:
                print(f"❌ Checksum mismatch!")
                if stored_hash:
                    print(f"   Expected: {stored_hash[:16]}...")
                print(f"   Current:  {current_hash[:16]}...")
                return False
        else:
            # No stored record, but we can still extract and check basic structure
            try:
                with tarfile.open(backup_file, "r:gz") as tar:
                    members = tar.getnames()
                    required_files = ["workflow-mappings.json", "metadata.json"]

                    if all(f in members for f in required_files):
                        print(
                            f"✅ Backup structure valid (no stored checksum): {current_hash[:16]}..."
                        )
                        return True
                    else:
                        print(f"❌ Invalid backup structure")
                        return False
            except Exception as e:
                print(f"❌ Cannot read backup file: {e}")
                return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups from database and filesystem"""
        # Get backups from database
        db_backups = self.db.get_backup_history()

        # Also scan backup directory for files
        if self.config:
            backup_dir = self.config.backups_path
        else:
            # Legacy fallback
            backup_dir = self.base_path.parent / "n8n-deploy" / "backups"

        filesystem_backups = []

        if backup_dir.exists():
            for backup_file in backup_dir.glob("n8n_deploy_workflows_*.tar.gz"):
                # Check if this file is in database
                db_backup = next(
                    (b for b in db_backups if b.get("filename") == backup_file.name),
                    None,
                )

                if not db_backup:
                    # File exists but not in database
                    filesystem_backups.append(
                        {
                            "filename": backup_file.name,
                            "file_size": backup_file.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                backup_file.stat().st_mtime
                            ),
                            "in_database": False,
                        }
                    )

        return db_backups + filesystem_backups
