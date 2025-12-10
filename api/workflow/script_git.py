#!/usr/bin/env python3
"""
Git-based change detection for script synchronization.

Uses GitPython to detect which scripts have been modified, added, or deleted
since the last commit or a specified reference.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Set, Union

from git import InvalidGitRepositoryError, Repo
from git.diff import Diff, DiffIndex
from git.exc import GitCommandError


class ScriptChangeStatus(str, Enum):
    """Status of a script file in git."""

    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    UNTRACKED = "untracked"
    UNCHANGED = "unchanged"


@dataclass
class ScriptChange:
    """Represents a changed script file."""

    path: Path
    filename: str
    status: ScriptChangeStatus

    @property
    def needs_upload(self) -> bool:
        """Check if this change requires uploading to remote."""
        return self.status in (
            ScriptChangeStatus.MODIFIED,
            ScriptChangeStatus.ADDED,
            ScriptChangeStatus.UNTRACKED,
        )

    @property
    def needs_deletion(self) -> bool:
        """Check if this change requires deletion from remote."""
        return self.status == ScriptChangeStatus.DELETED


class GitScriptDetector:
    """Detect changed scripts using git."""

    SUPPORTED_EXTENSIONS: Set[str] = {".js", ".cjs", ".py"}

    def __init__(self, scripts_dir: Path) -> None:
        """Initialize detector with scripts directory.

        Args:
            scripts_dir: Path to the scripts directory

        Raises:
            ValueError: If directory is not in a git repository
        """
        self.scripts_dir = scripts_dir.resolve()
        self._repo: Optional[Repo] = None
        self._git_root: Optional[Path] = None
        self._validate_git_repo()

    def _validate_git_repo(self) -> None:
        """Validate that scripts_dir is in a git repository."""
        try:
            self._repo = Repo(self.scripts_dir, search_parent_directories=True)
            working_dir = self._repo.working_dir
            if working_dir is None:
                raise ValueError(
                    f"Directory {self.scripts_dir} is not in a git repository. " "Git is required for change detection."
                )
            self._git_root = Path(working_dir)
        except InvalidGitRepositoryError as e:
            raise ValueError(
                f"Directory {self.scripts_dir} is not in a git repository. " "Git is required for change detection."
            ) from e

    @property
    def git_root(self) -> Path:
        """Get the git repository root directory."""
        if self._git_root is None:
            raise ValueError("Git root not initialized")
        return self._git_root

    @property
    def repo(self) -> Repo:
        """Get the git repository object."""
        if self._repo is None:
            raise ValueError("Repository not initialized")
        return self._repo

    def _is_supported_script(self, path: str) -> bool:
        """Check if file has a supported script extension."""
        return Path(path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _relative_to_scripts_dir(self, git_path: str) -> Optional[Path]:
        """Convert git-relative path to scripts_dir-relative path.

        Args:
            git_path: Path relative to git root

        Returns:
            Path relative to scripts_dir, or None if not in scripts_dir
        """
        full_path = self.git_root / git_path
        try:
            # Check if the file is under scripts_dir
            full_path.relative_to(self.scripts_dir)
            return full_path
        except ValueError:
            return None

    def get_modified_scripts(
        self,
        since_commit: Optional[str] = None,
        include_staged: bool = True,
        include_unstaged: bool = True,
        include_untracked: bool = True,
    ) -> List[ScriptChange]:
        """Get list of modified script files.

        Args:
            since_commit: Compare against this commit (default: HEAD)
            include_staged: Include staged changes
            include_unstaged: Include unstaged changes
            include_untracked: Include untracked files

        Returns:
            List of ScriptChange objects
        """
        changes: List[ScriptChange] = []
        seen_paths: Set[str] = set()

        # Get relative path from git root to scripts_dir
        try:
            scripts_rel = self.scripts_dir.relative_to(self.git_root)
            # When scripts_dir == git_root, scripts_rel is Path('.'), so check for that
            if str(scripts_rel) == ".":
                scripts_prefix = ""
            else:
                scripts_prefix = str(scripts_rel) + "/"
        except ValueError:
            scripts_prefix = ""

        # Staged changes (index vs HEAD)
        if include_staged:
            try:
                staged_diffs = self.repo.index.diff("HEAD")
                self._process_diffs(staged_diffs, changes, seen_paths, scripts_prefix, is_staged=True)
            except GitCommandError:
                # No HEAD commit yet (empty repo)
                pass

        # Unstaged changes (working tree vs index)
        if include_unstaged:
            unstaged_diffs = self.repo.index.diff(None)
            self._process_diffs(unstaged_diffs, changes, seen_paths, scripts_prefix, is_staged=False)

        # Changes since specific commit
        if since_commit:
            try:
                commit = self.repo.commit(since_commit)
                commit_diffs = commit.diff(None)
                self._process_diffs(commit_diffs, changes, seen_paths, scripts_prefix, is_staged=False)
            except GitCommandError:
                pass

        # Untracked files
        if include_untracked:
            for filepath in self.repo.untracked_files:
                if not self._is_supported_script(filepath):
                    continue

                abs_path = self.git_root / filepath

                # Filter to files in scripts directory
                try:
                    abs_path.relative_to(self.scripts_dir)
                except ValueError:
                    continue

                if str(abs_path) not in seen_paths:
                    changes.append(
                        ScriptChange(
                            path=abs_path,
                            filename=Path(filepath).name,
                            status=ScriptChangeStatus.UNTRACKED,
                        )
                    )
                    seen_paths.add(str(abs_path))

        return changes

    def _process_diffs(
        self,
        diffs: DiffIndex[Diff],
        changes: List[ScriptChange],
        seen_paths: Set[str],
        scripts_prefix: str,
        is_staged: bool,
    ) -> None:
        """Process git diff objects.

        Args:
            diffs: DiffIndex containing Diff objects
            changes: List to append changes to
            seen_paths: Set of already-seen paths
            scripts_prefix: Prefix to filter files in scripts_dir
            is_staged: Whether these are staged changes
        """
        for diff in diffs:
            # Get the file path (a_path for deleted, b_path for others)
            filepath = diff.b_path if diff.b_path else diff.a_path
            if not filepath:
                continue

            # Filter to files in scripts directory
            if scripts_prefix and not filepath.startswith(scripts_prefix):
                continue

            if not self._is_supported_script(filepath):
                continue

            abs_path = self.git_root / filepath
            if str(abs_path) in seen_paths:
                continue

            # Determine status
            if diff.deleted_file:
                status = ScriptChangeStatus.DELETED
            elif diff.new_file:
                status = ScriptChangeStatus.ADDED
            else:
                status = ScriptChangeStatus.MODIFIED

            changes.append(
                ScriptChange(
                    path=abs_path,
                    filename=Path(filepath).name,
                    status=status,
                )
            )
            seen_paths.add(str(abs_path))

    def get_all_tracked_scripts(self) -> List[Path]:
        """Get all tracked script files in the scripts directory.

        Returns:
            List of script file paths
        """
        scripts: List[Path] = []

        # Get all tracked files from the index
        for entry_key in self.repo.index.entries:
            filepath = str(entry_key[0])  # entry_key is (path, stage) tuple
            if self._is_supported_script(filepath):
                full_path = self.git_root / filepath
                try:
                    full_path.relative_to(self.scripts_dir)
                    scripts.append(full_path)
                except ValueError:
                    pass

        return scripts

    def get_all_scripts(self, include_untracked: bool = True) -> List[Path]:
        """Get all script files (tracked and optionally untracked).

        Args:
            include_untracked: Include untracked files

        Returns:
            List of script file paths
        """
        scripts = self.get_all_tracked_scripts()

        if include_untracked:
            for filepath in self.repo.untracked_files:
                if self._is_supported_script(filepath):
                    full_path = self.git_root / filepath
                    try:
                        full_path.relative_to(self.scripts_dir)
                        scripts.append(full_path)
                    except ValueError:
                        pass

        return scripts

    def filter_by_workflow_scripts(
        self,
        changes: List[ScriptChange],
        workflow_scripts: Set[str],
    ) -> List[ScriptChange]:
        """Filter changes to only those referenced in workflow.

        Args:
            changes: List of script changes
            workflow_scripts: Set of script filenames from workflow

        Returns:
            Filtered list of changes
        """
        return [change for change in changes if change.filename in workflow_scripts]


def is_git_repository(path: Path) -> bool:
    """Check if a path is in a git repository.

    Args:
        path: Path to check

    Returns:
        True if path is in a git repository
    """
    try:
        Repo(path, search_parent_directories=True)
        return True
    except InvalidGitRepositoryError:
        return False
