"""Unit tests for api/workflow/script_git.py module

Tests for GitScriptDetector class methods using GitPython mocks.
"""

from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from assertpy import assert_that
from git import InvalidGitRepositoryError

from api.workflow.script_git import (
    GitScriptDetector,
    ScriptChange,
    ScriptChangeStatus,
    is_git_repository,
)


@pytest.fixture
def mock_git_repo(temp_dir: Path) -> GitScriptDetector:
    """Create a GitScriptDetector with mocked git repository."""
    with patch("api.workflow.script_git.Repo") as MockRepo:
        mock_repo = MagicMock()
        mock_repo.working_dir = str(temp_dir)
        MockRepo.return_value = mock_repo
        detector = GitScriptDetector(temp_dir)
        # Store the mock repo for test access
        detector._repo = mock_repo
        detector._git_root = temp_dir
    return detector


class TestGitScriptDetector:
    """Tests for GitScriptDetector class"""

    def test_init(self, temp_dir: Path) -> None:
        """Test GitScriptDetector initialization"""
        with patch("api.workflow.script_git.Repo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.working_dir = str(temp_dir)
            MockRepo.return_value = mock_repo
            detector = GitScriptDetector(temp_dir)
            assert_that(detector.scripts_dir).is_equal_to(temp_dir)

    def test_git_root_property(self, temp_dir: Path) -> None:
        """Test git_root property returns correct path"""
        with patch("api.workflow.script_git.Repo") as MockRepo:
            mock_repo = MagicMock()
            mock_repo.working_dir = str(temp_dir)
            MockRepo.return_value = mock_repo
            detector = GitScriptDetector(temp_dir)
            assert_that(detector.git_root).is_equal_to(temp_dir)

    def test_init_non_git_directory_raises(self, temp_dir: Path) -> None:
        """Test initialization fails for non-git directory"""
        with patch("api.workflow.script_git.Repo") as MockRepo:
            MockRepo.side_effect = InvalidGitRepositoryError(str(temp_dir))
            with pytest.raises(ValueError, match="not in a git repository"):
                GitScriptDetector(temp_dir)

    def test_get_modified_scripts_staged(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test detecting staged modified scripts"""
        # Create mock diffs
        mock_diff_modified = MagicMock()
        mock_diff_modified.a_path = "modified.py"
        mock_diff_modified.b_path = "modified.py"
        mock_diff_modified.deleted_file = False
        mock_diff_modified.new_file = False

        mock_diff_added = MagicMock()
        mock_diff_added.a_path = None
        mock_diff_added.b_path = "added.js"
        mock_diff_added.deleted_file = False
        mock_diff_added.new_file = True

        mock_git_repo._repo.index.diff.return_value = [
            mock_diff_modified,
            mock_diff_added,
        ]
        mock_git_repo._repo.untracked_files = []

        changes = mock_git_repo.get_modified_scripts(
            include_staged=True,
            include_unstaged=False,
            include_untracked=False,
        )

        assert_that(changes).is_length(2)
        modified = [c for c in changes if c.status == ScriptChangeStatus.MODIFIED]
        added = [c for c in changes if c.status == ScriptChangeStatus.ADDED]
        assert_that(modified).is_length(1)
        assert_that(added).is_length(1)

    def test_get_modified_scripts_unstaged(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test detecting unstaged modified scripts"""
        mock_diff = MagicMock()
        mock_diff.a_path = "changed.py"
        mock_diff.b_path = "changed.py"
        mock_diff.deleted_file = False
        mock_diff.new_file = False

        # Mock index.diff(None) for unstaged changes
        # When include_staged=False, only diff(None) is called
        mock_git_repo._repo.index.diff.return_value = [mock_diff]
        mock_git_repo._repo.untracked_files = []

        changes = mock_git_repo.get_modified_scripts(
            include_staged=False,
            include_unstaged=True,
            include_untracked=False,
        )

        assert_that(changes).is_length(1)
        assert_that(changes[0].filename).is_equal_to("changed.py")
        assert_that(changes[0].status).is_equal_to(ScriptChangeStatus.MODIFIED)

    def test_get_modified_scripts_untracked(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test detecting untracked script files"""
        mock_git_repo._repo.index.diff.return_value = []
        mock_git_repo._repo.untracked_files = ["new_script.py", "another.js"]

        changes = mock_git_repo.get_modified_scripts(
            include_staged=False,
            include_unstaged=False,
            include_untracked=True,
        )

        assert_that(changes).is_length(2)
        assert_that(changes[0].status).is_equal_to(ScriptChangeStatus.UNTRACKED)
        assert_that(changes[1].status).is_equal_to(ScriptChangeStatus.UNTRACKED)

    def test_get_modified_scripts_filters_extensions(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test that non-script files are filtered out"""
        # Mix of script and non-script files
        mock_diffs = []
        for filename in ["test.py", "readme.md", "helper.js", "config.yaml"]:
            diff = MagicMock()
            diff.a_path = filename
            diff.b_path = filename
            diff.deleted_file = False
            diff.new_file = False
            mock_diffs.append(diff)

        mock_git_repo._repo.index.diff.return_value = mock_diffs
        mock_git_repo._repo.untracked_files = []

        changes = mock_git_repo.get_modified_scripts(
            include_staged=True,
            include_unstaged=False,
            include_untracked=False,
        )

        # Only .py and .js should be included
        assert_that(changes).is_length(2)
        filenames = [c.filename for c in changes]
        assert_that(filenames).contains("test.py", "helper.js")
        assert_that(filenames).does_not_contain("readme.md", "config.yaml")

    def test_get_modified_scripts_deleted(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test detecting deleted scripts"""
        mock_diff = MagicMock()
        mock_diff.a_path = "removed.py"
        mock_diff.b_path = None
        mock_diff.deleted_file = True
        mock_diff.new_file = False

        mock_git_repo._repo.index.diff.return_value = [mock_diff]
        mock_git_repo._repo.untracked_files = []

        changes = mock_git_repo.get_modified_scripts(
            include_staged=True,
            include_unstaged=False,
            include_untracked=False,
        )

        assert_that(changes).is_length(1)
        assert_that(changes[0].status).is_equal_to(ScriptChangeStatus.DELETED)
        assert_that(changes[0].needs_deletion).is_true()
        assert_that(changes[0].needs_upload).is_false()

    def test_get_modified_scripts_empty_output(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test returns empty list when no changes"""
        mock_git_repo._repo.index.diff.return_value = []
        mock_git_repo._repo.untracked_files = []

        changes = mock_git_repo.get_modified_scripts(
            include_staged=True,
            include_unstaged=False,
            include_untracked=False,
        )

        assert_that(changes).is_empty()

    def test_filter_by_workflow_scripts(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test filtering changes by workflow script filenames"""
        all_changes = [
            ScriptChange(
                path=temp_dir / "scripts" / "needed.py",
                filename="needed.py",
                status=ScriptChangeStatus.MODIFIED,
            ),
            ScriptChange(
                path=temp_dir / "scripts" / "not_used.py",
                filename="not_used.py",
                status=ScriptChangeStatus.MODIFIED,
            ),
            ScriptChange(
                path=temp_dir / "scripts" / "also_needed.js",
                filename="also_needed.js",
                status=ScriptChangeStatus.ADDED,
            ),
        ]

        workflow_scripts = {"needed.py", "also_needed.js", "other.py"}

        filtered = mock_git_repo.filter_by_workflow_scripts(all_changes, workflow_scripts)

        assert_that(filtered).is_length(2)
        filenames = [c.filename for c in filtered]
        assert_that(filenames).contains("needed.py", "also_needed.js")
        assert_that(filenames).does_not_contain("not_used.py")

    def test_get_all_tracked_scripts(self, temp_dir: Path, mock_git_repo: GitScriptDetector) -> None:
        """Test getting all tracked script files"""
        # Mock index.entries as dict-like with (path, stage) keys
        mock_git_repo._repo.index.entries = {
            ("a.py", 0): MagicMock(),
            ("b.js", 0): MagicMock(),
            ("c.cjs", 0): MagicMock(),
            ("readme.md", 0): MagicMock(),
        }

        scripts = mock_git_repo.get_all_tracked_scripts()

        # Returns List[Path], filter only .py/.js/.cjs extensions
        assert_that(scripts).is_length(3)
        filenames = [s.name for s in scripts]
        assert_that(filenames).contains("a.py", "b.js", "c.cjs")


class TestIsGitRepository:
    """Tests for is_git_repository function"""

    def test_is_git_repository_true(self, temp_dir: Path) -> None:
        """Test returns True for valid git repo"""
        with patch("api.workflow.script_git.Repo") as MockRepo:
            MockRepo.return_value = MagicMock()
            assert_that(is_git_repository(temp_dir)).is_true()

    def test_is_git_repository_false(self, temp_dir: Path) -> None:
        """Test returns False for non-git directory"""
        with patch("api.workflow.script_git.Repo") as MockRepo:
            MockRepo.side_effect = InvalidGitRepositoryError(str(temp_dir))
            assert_that(is_git_repository(temp_dir)).is_false()


class TestScriptChange:
    """Tests for ScriptChange dataclass"""

    def test_script_change_creation(self, temp_dir: Path) -> None:
        """Test ScriptChange dataclass creation"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.MODIFIED,
        )
        assert_that(change.filename).is_equal_to("test.py")
        assert_that(change.status).is_equal_to(ScriptChangeStatus.MODIFIED)

    def test_needs_upload_for_modified(self, temp_dir: Path) -> None:
        """Test needs_upload returns True for MODIFIED status"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.MODIFIED,
        )
        assert_that(change.needs_upload).is_true()
        assert_that(change.needs_deletion).is_false()

    def test_needs_upload_for_added(self, temp_dir: Path) -> None:
        """Test needs_upload returns True for ADDED status"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.ADDED,
        )
        assert_that(change.needs_upload).is_true()

    def test_needs_upload_for_untracked(self, temp_dir: Path) -> None:
        """Test needs_upload returns True for UNTRACKED status"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.UNTRACKED,
        )
        assert_that(change.needs_upload).is_true()

    def test_needs_deletion_for_deleted(self, temp_dir: Path) -> None:
        """Test needs_deletion returns True for DELETED status"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.DELETED,
        )
        assert_that(change.needs_deletion).is_true()
        assert_that(change.needs_upload).is_false()

    def test_unchanged_status(self, temp_dir: Path) -> None:
        """Test UNCHANGED status has no upload or deletion needed"""
        change = ScriptChange(
            path=temp_dir / "test.py",
            filename="test.py",
            status=ScriptChangeStatus.UNCHANGED,
        )
        assert_that(change.needs_upload).is_false()
        assert_that(change.needs_deletion).is_false()


class TestScriptChangeStatus:
    """Tests for ScriptChangeStatus enum"""

    def test_all_status_values(self) -> None:
        """Test all ScriptChangeStatus values exist"""
        assert_that(ScriptChangeStatus.MODIFIED.value).is_equal_to("modified")
        assert_that(ScriptChangeStatus.ADDED.value).is_equal_to("added")
        assert_that(ScriptChangeStatus.DELETED.value).is_equal_to("deleted")
        assert_that(ScriptChangeStatus.UNTRACKED.value).is_equal_to("untracked")
        assert_that(ScriptChangeStatus.UNCHANGED.value).is_equal_to("unchanged")
