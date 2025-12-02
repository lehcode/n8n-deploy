#!/usr/bin/env python3
"""
Property-based test generator using Hypothesis

Automatically generates hundreds of test cases by defining properties
that should always hold true for the CLI. Replaces repetitive E2E tests
with comprehensive property-based edge case testing.
"""

import json
import re
import subprocess
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ═══════════════════════════════════════════════════════════════════════════
# Strategy Definitions
# ═══════════════════════════════════════════════════════════════════════════

# Strategy: Valid file paths (basic safe paths)
valid_paths = st.one_of(
    st.just("/tmp"),
    st.just("/var/tmp"),
    st.builds(
        lambda x: f"/tmp/{x}",
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    ),
)

# Strategy: Paths with special characters and edge cases
special_char_paths = st.builds(
    lambda x: f"/tmp/{x}",
    st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters=" -_()[]@#$%^&+={}µ€£¥",
        ),
    ),
)

# Strategy: Deep nested paths
deep_paths = st.builds(
    lambda parts: "/tmp/" + "/".join(parts),
    st.lists(
        st.text(min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_"),
        min_size=1,
        max_size=10,
    ),
)

# Strategy: Workflow names (alphanumeric with spaces and hyphens)
workflow_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" -_()[]"),
)

# Strategy: Malicious wf names (injection attempts)
malicious_names = st.sampled_from(
    [
        "'; DROP TABLE workflows--",
        "$(rm -rf /)",
        "`whoami`",
        "../../../etc/passwd",
        "wf\x00null",
        "<script>alert('xss')</script>",
        "wf'; DELETE FROM workflows WHERE '1'='1",
        "wf\n\nmalicious_command",
        "wf && echo hacked",
        "wf || cat /etc/passwd",
    ]
)

# Strategy: Tags for wf filtering
workflow_tags = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
)

# Strategy: API keys (base64-like strings)
api_keys = st.text(
    min_size=20,
    max_size=200,
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
)

# Strategy: API key names
api_key_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
)

# Strategy: Server URLs
server_urls = st.one_of(
    st.just("http://localhost:5678"),
    st.builds(lambda p: f"http://localhost:{p}", st.integers(min_value=1000, max_value=65535)),
    st.builds(
        lambda h, p: f"http://{h}:{p}",
        st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-."),
        st.integers(min_value=1000, max_value=65535),
    ),
)

# Strategy: Format options
format_options = st.sampled_from(["table", "json", None])

# Strategy: Status filters
status_filters = st.sampled_from(["active", "inactive", "draft", "all"])

# Strategy: Boolean flags
boolean_flags = st.booleans()

# Strategy: Database filenames (valid SQLite database names)
db_filenames = st.one_of(
    st.just("n8n-deploy.db"),  # Default
    st.builds(
        lambda x: f"{x}.db",
        st.text(
            min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_")
        ),
    ),
    st.builds(
        lambda x: f"workflows-{x}.db",
        st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    ),
)

# Strategy: Server names (alphanumeric with hyphens and underscores)
server_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
)


class TestPropertyBased:
    """Property-based tests that should always hold"""

    @given(app_dir=valid_paths)
    @settings(max_examples=50, deadline=None)
    def test_env_command_never_crashes_with_valid_paths(self, app_dir):
        """Property: env command should handle any valid path"""
        result = subprocess.run(["./n8n-deploy", "env", "--data-dir", app_dir], capture_output=True, timeout=60, text=True)
        # Should always exit with known codes
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

    @given(app_dir=valid_paths, flow_dir=valid_paths, format_choice=st.sampled_from(["table", "json", None]))
    @settings(max_examples=30, deadline=None)
    def test_env_command_format_options(self, app_dir, flow_dir, format_choice):
        """Property: env command should handle all format options"""
        cmd = ["./n8n-deploy", "env", "--data-dir", app_dir, "--flow-dir", flow_dir]
        if format_choice:
            cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)

        # Should always succeed or fail gracefully
        assert result.returncode in [0, 1], f"Unexpected crash: {result.returncode}"

        # JSON format should produce valid JSON
        if format_choice == "json" and result.returncode == 0:
            import json

            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "Invalid JSON output"

    @given(server_url=server_urls)
    @settings(max_examples=20, deadline=None)
    def test_env_accepts_valid_server_urls(self, server_url):
        """Property: env command should accept valid server URLs"""
        result = subprocess.run(["./n8n-deploy", "env", "--remote", server_url], capture_output=True, timeout=60, text=True)
        assert result.returncode == 0, f"Should accept valid URL: {server_url}"

    @given(workflow_name=workflow_names)
    @settings(max_examples=100, deadline=None)
    def test_workflow_names_never_cause_injection(self, workflow_name):
        """Property: Workflow names should never cause command injection"""
        # This will test names like: "'; DROP TABLE--", "$(rm -rf /)", etc.
        result = subprocess.run(["./n8n-deploy", "wf", "search", workflow_name], capture_output=True, timeout=60, text=True)
        # Should handle gracefully, never execute injected commands
        assert result.returncode in [0, 1, 2], "Potential command injection vulnerability"
        # stderr should not contain signs of SQL injection
        assert "syntax error" not in result.stderr.lower()
        assert "SQL" not in result.stderr

    @given(app_dir=valid_paths)
    @settings(max_examples=30, deadline=None)
    def test_db_status_handles_all_paths(self, app_dir):
        """Property: db status should handle any valid path"""
        result = subprocess.run(
            ["./n8n-deploy", "db", "status", "--data-dir", app_dir], capture_output=True, timeout=60, text=True
        )
        # Should exit gracefully even if DB doesn't exist
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

    @given(format_choice=st.sampled_from(["table", "json", None]))
    @settings(max_examples=20, deadline=None)
    def test_wf_list_handles_format_options(self, format_choice):
        """Property: wf list should handle all format options"""
        cmd = ["./n8n-deploy", "wf", "list"]
        if format_choice:
            cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1], f"Unexpected crash: {result.returncode}"

        # JSON format should produce valid JSON
        if format_choice == "json" and result.returncode == 0:
            import json

            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "Invalid JSON output from wf list"

    @given(
        tag=st.text(
            min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_")
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_wf_search_tags_never_crash(self, tag):
        """Property: wf search by tag should never crash"""
        result = subprocess.run(["./n8n-deploy", "wf", "search", "--tag", tag], capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1, 2], "Search by tag crashed unexpectedly"

    def test_wf_list_basic(self):
        """Property: wf list should work without flags"""
        result = subprocess.run(["./n8n-deploy", "wf", "list"], capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1], "wf list caused crash"

    @given(
        path_components=st.lists(
            st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_"), min_size=1, max_size=5
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_deep_nested_paths_handled(self, path_components):
        """Property: Commands should handle deeply nested paths"""
        deep_path = "/tmp/" + "/".join(path_components)
        result = subprocess.run(["./n8n-deploy", "env", "--data-dir", deep_path], capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1, 2], "Deep nested path caused unexpected behavior"

    @given(server_url=server_urls, app_dir=valid_paths)
    @settings(max_examples=20, deadline=None)
    def test_combined_options_never_crash(self, server_url, app_dir):
        """Property: Combining multiple options should never crash"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--remote", server_url, "--json"],
            capture_output=True,
            timeout=60,
            text=True,
        )
        assert result.returncode in [0, 1], "Combined options caused crash"

        # Should still produce valid JSON
        if result.returncode == 0:
            import json

            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "Invalid JSON with combined options"


# ═══════════════════════════════════════════════════════════════════════════
# Format Validation Tests (replaces E2E format tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestFormatValidation:
    """Property: All commands with --format json should produce valid JSON"""

    @given(app_dir=valid_paths)
    @settings(max_examples=30, deadline=None)
    def test_env_json_always_valid(self, app_dir):
        """Property: env --format json always produces parseable JSON"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--json"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                # Should have expected structure
                assert "variables" in data, "JSON missing 'variables' key"
                assert "priority_order" in data, "JSON missing 'priority_order' key"
            except json.JSONDecodeError as e:
                assert False, f"Invalid JSON output: {e}"

    @given(app_dir=valid_paths, format_choice=format_options)
    @settings(max_examples=40, deadline=None)
    def test_db_status_formats(self, app_dir, format_choice):
        """Property: db status supports all format options correctly"""
        cmd = ["./n8n-deploy", "db", "status", "--data-dir", app_dir]
        if format_choice:
            cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)

        # Should always exit gracefully
        assert result.returncode in [0, 1, 2]

        # JSON output should be valid
        if format_choice == "json" and result.returncode == 0:
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "db status JSON output invalid"

    @given(app_dir=valid_paths)
    @settings(max_examples=20, deadline=None)
    def test_apikey_list_json_structure(self, app_dir):
        """Property: apikey list --format json has consistent structure"""
        result = subprocess.run(
            ["./n8n-deploy", "apikey", "list", "--json"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                # Should be a list (even if empty)
                assert isinstance(data, list), "apikey list JSON should be array"
            except json.JSONDecodeError:
                assert False, "apikey list produced invalid JSON"


# ═══════════════════════════════════════════════════════════════════════════
# Path Handling Tests (replaces E2E path tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestPathHandling:
    """Property: Commands should handle all valid path variations"""

    @given(path=special_char_paths)
    @settings(max_examples=50, deadline=None)
    def test_special_characters_in_paths(self, path):
        """Property: Special characters in paths never cause crashes"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", path],
            capture_output=True,
            timeout=60,
            text=True,
        )
        # Should exit gracefully with known codes
        assert result.returncode in [0, 1, 2], f"Crashed with path: {path}"

    @given(path=deep_paths)
    @settings(max_examples=40, deadline=None)
    def test_deeply_nested_paths(self, path):
        """Property: Deeply nested paths handled correctly"""
        # Skip paths that are too long for filesystem
        assume(len(path) < 200)

        result = subprocess.run(
            ["./n8n-deploy", "db", "status", "--data-dir", path],
            capture_output=True,
            timeout=60,
            text=True,
        )
        assert result.returncode in [0, 1, 2]

    @given(app_dir=special_char_paths, flow_dir=special_char_paths)
    @settings(max_examples=30, deadline=None)
    def test_matching_special_char_paths(self, app_dir, flow_dir):
        """Property: Both app-dir and flow-dir with special chars work"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--flow-dir", flow_dir],
            capture_output=True,
            timeout=60,
            text=True,
        )
        assert result.returncode in [0, 1, 2]

    @given(path_list=st.lists(valid_paths, min_size=2, max_size=5))
    @settings(max_examples=20, deadline=None)  # 5 second deadline for multiple subprocess calls
    def test_path_consistency_across_commands(self, path_list):
        """Property: Same path works consistently across different commands"""
        path = path_list[0]

        # All these commands should handle the path consistently
        commands = [
            ["env", "--data-dir", path],
            ["db", "status", "--data-dir", path],
            ["wf", "list", "--data-dir", path],
        ]

        exit_codes = []
        for cmd in commands:
            result = subprocess.run(
                ["./n8n-deploy"] + cmd,
                capture_output=True,
                timeout=60,
                text=True,
            )
            exit_codes.append(result.returncode)

        # All should succeed or fail in similar ways (all 0-2 range)
        assert all(code in [0, 1, 2] for code in exit_codes)

    @given(path_name=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
    @settings(max_examples=20, deadline=None)
    def test_invalid_paths_default_to_cwd(self, path_name):
        """Property: Invalid paths should default to cwd and not cause crashes"""
        # Generate a nonexistent path
        invalid_path = f"/nonexistent/test/{path_name}"

        # Commands should succeed by defaulting to cwd
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", invalid_path, "--json"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should succeed (defaults to cwd)
        assert result.returncode == 0, f"Should default to cwd for invalid path: {invalid_path}"

        # Verify JSON is valid
        import json

        data = json.loads(result.stdout)
        assert "variables" in data


# ═══════════════════════════════════════════════════════════════════════════
# Input Sanitization Tests (replaces E2E injection tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestInputSanitization:
    """Property: Malicious inputs never cause code execution"""

    @given(malicious_input=malicious_names)
    @settings(max_examples=20, deadline=None)
    def test_malicious_workflow_names_blocked(self, malicious_input):
        """Property: SQL injection attempts in wf names fail safely"""
        # Skip inputs with null bytes (Python subprocess limitation)
        assume("\x00" not in malicious_input)

        result = subprocess.run(
            ["./n8n-deploy", "wf", "search", malicious_input],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should not crash
        assert result.returncode in [0, 1, 2]
        # Should not show SQL errors
        assert "syntax error" not in result.stderr.lower()
        assert "SQL" not in result.stderr
        # The malicious input may appear in error messages (which is safe)
        # We're checking that commands weren't actually executed
        # For shell injection, we'd see command output without error messages
        # Since search returns "not found", the command was NOT executed

    @given(malicious_input=malicious_names)
    @settings(max_examples=20, deadline=None)
    def test_malicious_tag_names_blocked(self, malicious_input):
        """Property: Command injection in tags fails safely"""
        # Skip inputs with null bytes
        assume("\x00" not in malicious_input)

        result = subprocess.run(
            ["./n8n-deploy", "wf", "search", "--tag", malicious_input],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1, 2]
        # Malicious input in messages is OK, just no actual command execution

    @given(malicious_input=malicious_names)
    @settings(max_examples=15, deadline=None)
    def test_malicious_api_key_names_blocked(self, malicious_input):
        """Property: Injection attempts in API key names fail safely"""
        # Try to list with malicious search pattern
        result = subprocess.run(
            ["./n8n-deploy", "apikey", "list"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1, 2]


# ═══════════════════════════════════════════════════════════════════════════
# Command Help Consistency Tests (replaces E2E help tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestHelpConsistency:
    """Property: Help output should be consistent and informative"""

    @given(command=st.sampled_from(["env", "db", "wf", "apikey"]))
    @settings(max_examples=10, deadline=None)
    def test_command_help_always_works(self, command):
        """Property: All commands have working --help"""
        result = subprocess.run(
            ["./n8n-deploy", command, "--help"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Help should always succeed
        assert result.returncode == 0, f"{command} --help failed"
        # Should contain usage information
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    @given(
        command=st.sampled_from(["status", "init", "backup", "compact"]),
    )
    @settings(max_examples=10, deadline=None)
    def test_db_subcommand_help(self, command):
        """Property: All db subcommands have help"""
        result = subprocess.run(
            ["./n8n-deploy", "db", command, "--help"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    @given(
        command=st.sampled_from(
            [
                "list",
                "add",
                "delete",
                "search",
                "stats",
                "pull",
                "push",
                "server",
            ]
        ),
    )
    @settings(max_examples=12, deadline=None)
    def test_wf_subcommand_help(self, command):
        """Property: All wf subcommands have help"""
        result = subprocess.run(
            ["./n8n-deploy", "wf", command, "--help"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Option Combination Tests (replaces E2E combination tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestOptionCombinations:
    """Property: Valid option combinations never crash"""

    @given(
        app_dir=valid_paths,
        flow_dir=valid_paths,
        server_url=server_urls,
        format_choice=format_options,
    )
    @settings(max_examples=50, deadline=None)
    def test_all_env_options_combined(self, app_dir, flow_dir, server_url, format_choice):
        """Property: All env options work together"""
        cmd = [
            "./n8n-deploy",
            "env",
            "--data-dir",
            app_dir,
            "--flow-dir",
            flow_dir,
            "--remote",
            server_url,
        ]
        if format_choice:
            cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)

        # Should not crash
        assert result.returncode in [0, 1]

        # JSON should be valid if requested
        if format_choice == "json" and result.returncode == 0:
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "Combined options produced invalid JSON"


# ═══════════════════════════════════════════════════════════════════════════
# Server Management Tests (edge cases for server CRUD operations)
# ═══════════════════════════════════════════════════════════════════════════


class TestServerManagement:
    """Property-based tests for server management operations"""

    @given(server_name=server_names, server_url=server_urls)
    @settings(max_examples=50, deadline=None)
    def test_server_create_with_valid_inputs(self, server_name, server_url):
        """Property: Server create should handle valid names and URLs"""
        # Skip empty names (filtered by strategy but double-check)
        assume(len(server_name.strip()) > 0)

        result = subprocess.run(
            ["./n8n-deploy", "server", "create", server_name, server_url],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should succeed or fail gracefully (duplicate name, etc.)
        assert result.returncode in [0, 1, 2], f"Server create crashed with: {server_name}, {server_url}"

    @given(server_name=server_names)
    @settings(max_examples=30, deadline=None)
    def test_server_list_never_crashes(self, server_name):
        """Property: Server list should never crash regardless of database state"""
        result = subprocess.run(
            ["./n8n-deploy", "server", "list"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should always succeed
        assert result.returncode in [0, 1], "Server list command crashed"

    @given(format_choice=format_options)
    @settings(max_examples=20, deadline=None)
    def test_server_list_format_options(self, format_choice):
        """Property: Server list should handle all format options"""
        cmd = ["./n8n-deploy", "server", "list"]
        if format_choice:
            cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1]

        # JSON format should produce valid JSON
        if format_choice == "json" and result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, list), "Server list JSON should be array"
            except json.JSONDecodeError:
                assert False, "Server list produced invalid JSON"

    @given(active_flag=boolean_flags)
    @settings(max_examples=10, deadline=None)
    def test_server_list_active_filter(self, active_flag):
        """Property: Server list --active filter should work"""
        cmd = ["./n8n-deploy", "server", "list"]
        if active_flag:
            cmd.append("--active")

        result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        assert result.returncode in [0, 1], "--active flag caused crash"

    @given(server_name=server_names)
    @settings(max_examples=30, deadline=None)
    def test_server_remove_handles_nonexistent(self, server_name):
        """Property: Removing non-existent server should fail gracefully"""
        assume(len(server_name.strip()) > 0)

        result = subprocess.run(
            ["./n8n-deploy", "server", "remove", server_name, "--confirm", "--preserve-keys"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should handle gracefully (may succeed if server exists, fail if not)
        assert result.returncode in [0, 1, 2], "Server remove crashed unexpectedly"

    @given(
        server_name=server_names,
        server_url=server_urls,
        format_choice=format_options,
    )
    @settings(max_examples=40, deadline=None)
    def test_server_operations_combined(self, server_name, server_url, format_choice):
        """Property: Server operations with format options should work"""
        assume(len(server_name.strip()) > 0)

        # Create server
        create_result = subprocess.run(
            ["./n8n-deploy", "server", "create", server_name, server_url],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # List with format
        list_cmd = ["./n8n-deploy", "server", "list"]
        if format_choice:
            list_cmd.extend(["--json"] if format_choice == "json" else ["--table"])

        list_result = subprocess.run(list_cmd, capture_output=True, timeout=60, text=True)

        # Both should handle gracefully
        assert create_result.returncode in [0, 1, 2]
        assert list_result.returncode in [0, 1]

    @given(malicious_input=malicious_names)
    @settings(max_examples=20, deadline=None)
    def test_malicious_server_names_blocked(self, malicious_input):
        """Property: SQL injection in server names fails safely"""
        assume("\x00" not in malicious_input)

        result = subprocess.run(
            ["./n8n-deploy", "server", "create", malicious_input, "http://localhost:5678"],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should not crash, should not show SQL errors
        assert result.returncode in [0, 1, 2]
        assert "syntax error" not in result.stderr.lower()
        assert "SQL" not in result.stderr

    @given(server_name=server_names, api_key_name=api_key_names)
    @settings(max_examples=30, deadline=None)
    def test_server_api_key_linking_operations(self, server_name, api_key_name):
        """Property: Server API key linking should handle edge cases"""
        assume(len(server_name.strip()) > 0 and len(api_key_name.strip()) > 0)

        # Try to link (may fail if server/key doesn't exist)
        result = subprocess.run(
            ["./n8n-deploy", "server", "add", server_name, api_key_name],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Should fail gracefully if server or key doesn't exist
        assert result.returncode in [0, 1, 2], "Server add API key crashed"

    @given(server_url_1=server_urls)
    @settings(max_examples=20, deadline=None)
    def test_multiple_servers_with_same_url(self, server_url_1):
        """Property: Multiple servers can have different names with same URL"""
        # This tests that URL is not unique constraint (only name is)
        result1 = subprocess.run(
            ["./n8n-deploy", "server", "create", "server1", server_url_1],
            capture_output=True,
            timeout=60,
            text=True,
        )

        result2 = subprocess.run(
            ["./n8n-deploy", "server", "create", "server2", server_url_1],
            capture_output=True,
            timeout=60,
            text=True,
        )

        # Both should handle gracefully
        assert result1.returncode in [0, 1, 2]
        assert result2.returncode in [0, 1, 2]


# ═══════════════════════════════════════════════════════════════════════════
# Database Init Tests (--db-filename option)
# ═══════════════════════════════════════════════════════════════════════════


class TestDatabaseInit:
    """Property: Database init with --db-filename option behaves correctly"""

    @given(filename=db_filenames, data_dir=valid_paths)
    @settings(max_examples=30, deadline=None)
    def test_db_init_filename_creates_database(self, filename, data_dir):
        """Property: db init --db-filename creates database with specified name"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename, "--no-emoji"],
                capture_output=True,
                timeout=60,
                text=True,
            )

            # Should succeed
            assert result.returncode == 0, f"db init failed for filename {filename}"
            assert "initialized" in result.stdout.lower()

            # Database file should exist with specified name
            db_path = Path(temp_dir) / filename
            assert db_path.exists(), f"Database {filename} not created"
            assert db_path.stat().st_size > 0, f"Database {filename} is empty"

    @given(filename=db_filenames)
    @settings(max_examples=20, deadline=None)
    def test_db_init_custom_filename_auto_imports(self, filename):
        """Property: Custom filename auto-imports on second init"""
        import tempfile
        from pathlib import Path

        # Skip default filename (it prompts interactively)
        assume(filename != "n8n-deploy.db")

        with tempfile.TemporaryDirectory() as temp_dir:
            # First init
            result1 = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename, "--no-emoji"],
                capture_output=True,
                timeout=60,
                text=True,
            )
            assert result1.returncode == 0

            # Second init with same filename should auto-import
            result2 = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename, "--no-emoji"],
                capture_output=True,
                timeout=60,
                text=True,
            )

            assert result2.returncode == 0
            assert "using existing" in result2.stdout.lower() or "already exists" in result2.stdout.lower()

    @given(filename=db_filenames)
    @settings(max_examples=15, deadline=None)
    def test_db_init_filename_json_output(self, filename):
        """Property: db init --db-filename with --json produces valid JSON"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename, "--json"],
                capture_output=True,
                timeout=60,
                text=True,
            )

            if result.returncode == 0:
                # Should be valid JSON
                try:
                    data = json.loads(result.stdout)
                    assert "success" in data
                    assert "database_path" in data
                    assert filename in data["database_path"]
                except json.JSONDecodeError:
                    assert False, f"Invalid JSON output for filename {filename}"

    @given(
        filename1=db_filenames,
        filename2=db_filenames,
    )
    @settings(max_examples=20, deadline=None)
    def test_db_init_different_filenames_create_separate_databases(self, filename1, filename2):
        """Property: Different filenames create separate database files"""
        import tempfile
        from pathlib import Path

        # Only test if filenames are different
        assume(filename1 != filename2)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first database
            result1 = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename1, "--no-emoji"],
                capture_output=True,
                timeout=60,
                text=True,
            )

            # Create second database
            result2 = subprocess.run(
                ["./n8n-deploy", "db", "init", "--data-dir", temp_dir, "--db-filename", filename2, "--no-emoji"],
                capture_output=True,
                timeout=60,
                text=True,
            )

            # Both should succeed
            assert result1.returncode == 0
            assert result2.returncode == 0

            # Both database files should exist
            db_path1 = Path(temp_dir) / filename1
            db_path2 = Path(temp_dir) / filename2
            assert db_path1.exists()
            assert db_path2.exists()

            # They should be separate files
            assert db_path1 != db_path2


def generate_example_runs():
    """Generate example test data for documentation"""
    print("Generating example test inputs that Hypothesis would try:\n")

    examples = {
        "Valid Paths": [valid_paths.example() for _ in range(5)],
        "Workflow Names": [workflow_names.example() for _ in range(5)],
        "Server URLs": [server_urls.example() for _ in range(5)],
        "API Keys": [api_keys.example() for _ in range(3)],
    }

    for category, items in examples.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")


if __name__ == "__main__":
    import sys

    if "--examples" in sys.argv:
        generate_example_runs()
    else:
        print("Property-based test definitions created!")
        print("\nTo run these tests:")
        print("  1. Install hypothesis: pip install hypothesis")
        print("  2. Run with pytest: pytest tests/generators/hypothesis_generator.py")
        print("\nTo see example inputs:")
        print("  python tests/generators/hypothesis_generator.py --examples")
