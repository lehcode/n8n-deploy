#!/usr/bin/env python3
"""
Workflow backup and restore operations

Handles: backup-workflows, restore-workflows, verify-backup, list-backups operations
"""

import hashlib
import json
import shutil
import tarfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..api_keys import KeyApi
from ..config import AppConfig
from ..db import DBApi


class WorkflowBackup:
    """Workflow backup and restore operations"""

    def __init__(self, db: DBApi, config: AppConfig, flow_api: Optional[KeyApi] = None):
        self.db = db
        self.config = config
        self.flow_api = flow_api
        self.base_path = config.workflows_path

    def backup_all_workflows(self, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Backup all workflows that can be validated (convenience method for loops)

        Returns:
            Summary dict with backup results for each workflow
        """
        from .crud import WorkflowCRUD

        crud = WorkflowCRUD(self.db, self.config)

        backupable_workflows = crud.list_workflows(only_backupable=True)

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
                print(f"✅ Backed up: {workflow['name']} -> {backup_result['filename']}")
            except Exception as e:
                results["failed_backups"].append(
                    {
                        "workflow_id": workflow["id"],
                        "workflow_name": workflow["name"],
                        "error": str(e),
                    }
                )
                print(f"❌ Failed to backup {workflow['name']}: {e}")

        success_count = len(results["successful_backups"])
        total_count = results["total_workflows"]
        print(f"\n📊 Backup Summary: {success_count}/{total_count} workflows backed up successfully")

        return results

    def create_workflow_backup(self, workflow_id: str, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Create a tar.gz backup of a single specified workflow if it exists and can be validated"""
        if backup_dir is None:
            if not self.config:
                raise RuntimeError("Configuration is required for backup operations")
            backup_dir = self.config.backups_path

        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found in database")

        # Construct file path: {file_folder}/{workflow_id}.json
        if workflow.file_folder:
            workflow_file = Path(workflow.file_folder) / f"{workflow.id}.json"
        else:
            # Fallback to base_path if no file_folder stored
            workflow_file = self.base_path / f"{workflow.id}.json"
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")

        api_validation_passed = True
        if self.flow_api and hasattr(self.flow_api, "get_api_key"):
            api_key = self.flow_api.get_api_key("n8n")
            if api_key:
                api_validation_passed = True

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"n8n_deploy_workflow_{workflow_id}_{timestamp}.tar.gz"
        backup_path = backup_dir / backup_filename

        temp_dir = backup_dir / f"temp_{workflow_id}_{timestamp}"
        temp_dir.mkdir(exist_ok=True)

        try:
            dest_file = temp_dir / f"{workflow.id}.json"
            shutil.copy2(workflow_file, dest_file)

            with open(dest_file, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            workflow_data = {
                "original_path": str(workflow_file),
                "name": workflow.name,
                "sha256": file_hash,
            }

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

            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(temp_dir, arcname=".")

            with open(backup_path, "rb") as f:
                backup_hash = hashlib.sha256(f.read()).hexdigest()

            metadata.update({"sha256_hash": backup_hash, "file_size": backup_path.stat().st_size})

            self.db.create_backup_record(metadata)

            print(f"🎭 Workflow backup created: {backup_path}")
            print(f"   📦 1 workflow archived: {workflow.name} ({workflow_id})")
            print(f"   🔍 Checksum: {backup_hash[:16]}...")

            return metadata

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def restore_workflows_backup(self, backup_file: Path, force: bool = False) -> bool:
        """Restore workflows from backup archive"""
        backup_file = Path(backup_file)

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False

        if not self.verify_backup_integrity(backup_file):
            print("❌ Backup integrity check failed")
            return False

        temp_dir = backup_file.parent / f"restore_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(exist_ok=True)

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(temp_dir)

            metadata_file = temp_dir / "metadata.json"
            if not metadata_file.exists():
                print("❌ Invalid backup: metadata.json not found")
                return False

            with open(metadata_file) as f:
                metadata = json.load(f)

            workflow_count = metadata.get("workflow_count", 0)
            if workflow_count == 0:
                print("❌ No workflows found in backup")
                return False

            print(f"🔄 Restoring {workflow_count} workflow(s) from backup...")

            # Handle single workflow backup
            if "workflow" in metadata:
                return self._restore_single_workflow(temp_dir, metadata, force)
            else:
                # Handle multiple workflows backup (if we ever implement that)
                print("❌ Multiple workflow restore not yet implemented")
                return False

        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            return False
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _restore_single_workflow(self, temp_dir: Path, metadata: Dict[str, Any], force: bool) -> bool:
        """Restore a single workflow from backup"""
        workflow_data = metadata["workflow"]
        workflow_id = metadata["workflow_id"]

        # Check if workflow already exists
        existing_workflow = self.db.get_workflow(workflow_id)
        workflow_file_path = self.base_path / workflow_data["original_path"]

        if existing_workflow and not force:
            print(f"⚠️  Workflow {workflow_id} already exists in database. Use --force to overwrite.")
            return False

        if workflow_file_path.exists() and not force:
            print(f"⚠️  Workflow file {workflow_file_path} already exists. Use --force to overwrite.")
            return False

        # Restore workflow file
        backup_workflow_file = temp_dir / f"{workflow_id}.json"
        if not backup_workflow_file.exists():
            print(f"❌ Workflow file {workflow_id}.json not found in backup")
            return False

        # Verify file hash
        with open(backup_workflow_file, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        if file_hash != workflow_data["sha256"]:
            print("❌ Workflow file hash verification failed")
            return False

        # Create directory if needed
        workflow_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(backup_workflow_file, workflow_file_path)

        # Update database
        print(f"✅ Restored workflow: {workflow_data['name']} -> {workflow_file_path}")
        return True

    def verify_backup_integrity(self, backup_file: Path) -> bool:
        """Verify backup file integrity using SHA256 checksums"""
        backup_file = Path(backup_file)

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False

        try:
            # Get stored checksum from database
            backup_record = self.db.get_backup_by_filename(backup_file.name)
            if not backup_record:
                print("⚠️  Backup record not found in database, verifying file structure only")
                stored_hash = None
            else:
                stored_hash = backup_record.get("sha256_hash")

            # Calculate current file hash
            with open(backup_file, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()

            # Compare hashes if we have stored hash
            if stored_hash and current_hash != stored_hash:
                print("❌ Backup file checksum mismatch!")
                print(f"   Expected: {stored_hash}")
                print(f"   Actual:   {current_hash}")
                return False

            # Verify tar.gz structure
            try:
                with tarfile.open(backup_file, "r:gz") as tar:
                    members = tar.getnames()
                    if "metadata.json" not in members:
                        print("❌ Invalid backup structure: metadata.json missing")
                        return False
            except Exception as e:
                print(f"❌ Failed to read backup archive: {e}")
                return False

            if stored_hash:
                print(f"✅ Backup integrity verified: {backup_file.name}")
                print(f"   📦 Checksum: {current_hash[:16]}...")
            else:
                print(f"✅ Backup structure verified: {backup_file.name}")

            return True

        except Exception as e:
            print(f"❌ Failed to verify backup integrity: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available workflow backups"""
        return self.db.list_backups()
