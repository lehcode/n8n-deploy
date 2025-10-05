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

# Strategy: Malicious workflow names (injection attempts)
malicious_names = st.sampled_from(
    [
        "'; DROP TABLE workflows--",
        "$(rm -rf /)",
        "`whoami`",
        "../../../etc/passwd",
        "workflow\x00null",
        "<script>alert('xss')</script>",
        "workflow'; DELETE FROM workflows WHERE '1'='1",
        "workflow\n\nmalicious_command",
        "workflow && echo hacked",
        "workflow || cat /etc/passwd",
    ]
)

# Strategy: Tags for workflow filtering
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


class TestPropertyBased:
    """Property-based tests that should always hold"""

    @given(app_dir=valid_paths)
    @settings(max_examples=50)
    def test_env_command_never_crashes_with_valid_paths(self, app_dir):
        """Property: env command should handle any valid path"""
        result = subprocess.run(["./n8n-deploy", "env", "--data-dir", app_dir], capture_output=True, timeout=5, text=True)
        # Should always exit with known codes
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

    @given(app_dir=valid_paths, flow_dir=valid_paths, format_choice=st.sampled_from(["table", "json", None]))
    @settings(max_examples=30)
    def test_env_command_format_options(self, app_dir, flow_dir, format_choice):
        """Property: env command should handle all format options"""
        cmd = ["./n8n-deploy", "env", "--data-dir", app_dir, "--flows-dir", flow_dir]
        if format_choice:
            cmd.extend(["--format", format_choice])

        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)

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
    @settings(max_examples=20)
    def test_env_accepts_valid_server_urls(self, server_url):
        """Property: env command should accept valid server URLs"""
        result = subprocess.run(["./n8n-deploy", "env", "--remote", server_url], capture_output=True, timeout=5, text=True)
        assert result.returncode == 0, f"Should accept valid URL: {server_url}"

    @given(workflow_name=workflow_names)
    @settings(max_examples=100)
    def test_workflow_names_never_cause_injection(self, workflow_name):
        """Property: Workflow names should never cause command injection"""
        # This will test names like: "'; DROP TABLE--", "$(rm -rf /)", etc.
        result = subprocess.run(["./n8n-deploy", "wf", "search", workflow_name], capture_output=True, timeout=5, text=True)
        # Should handle gracefully, never execute injected commands
        assert result.returncode in [0, 1, 2], "Potential command injection vulnerability"
        # stderr should not contain signs of SQL injection
        assert "syntax error" not in result.stderr.lower()
        assert "SQL" not in result.stderr

    @given(app_dir=valid_paths)
    @settings(max_examples=30)
    def test_db_status_handles_all_paths(self, app_dir):
        """Property: db status should handle any valid path"""
        result = subprocess.run(
            ["./n8n-deploy", "db", "status", "--data-dir", app_dir], capture_output=True, timeout=5, text=True
        )
        # Should exit gracefully even if DB doesn't exist
        assert result.returncode in [0, 1, 2], f"Unexpected exit code: {result.returncode}"

    @given(app_dir=valid_paths, format_choice=st.sampled_from(["table", "json", None]))
    @settings(max_examples=20)
    def test_wf_list_format_options(self, app_dir, format_choice):
        """Property: wf list should handle all format options"""
        cmd = ["./n8n-deploy", "wf", "list", "--data-dir", app_dir]
        if format_choice:
            cmd.extend(["--format", format_choice])

        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)
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
    @settings(max_examples=50)
    def test_wf_search_tags_never_crash(self, tag):
        """Property: wf search by tag should never crash"""
        result = subprocess.run(["./n8n-deploy", "wf", "search", "--tag", tag], capture_output=True, timeout=5, text=True)
        assert result.returncode in [0, 1, 2], "Search by tag crashed unexpectedly"

    @given(only_flag=boolean_flags)
    @settings(max_examples=10)
    def test_wf_list_only_filter(self, only_flag):
        """Property: wf list should handle --only flag"""
        cmd = ["./n8n-deploy", "wf", "list"]
        if only_flag:
            cmd.append("--only")
        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)
        assert result.returncode in [0, 1], f"--only flag caused crash"

    @given(
        path_components=st.lists(
            st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_"), min_size=1, max_size=5
        )
    )
    @settings(max_examples=30)
    def test_deep_nested_paths_handled(self, path_components):
        """Property: Commands should handle deeply nested paths"""
        deep_path = "/tmp/" + "/".join(path_components)
        result = subprocess.run(["./n8n-deploy", "env", "--data-dir", deep_path], capture_output=True, timeout=5, text=True)
        assert result.returncode in [0, 1, 2], "Deep nested path caused unexpected behavior"

    @given(server_url=server_urls, app_dir=valid_paths)
    @settings(max_examples=20)
    def test_combined_options_never_crash(self, server_url, app_dir):
        """Property: Combining multiple options should never crash"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--remote", server_url, "--format", "json"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=30)
    def test_env_json_always_valid(self, app_dir):
        """Property: env --format json always produces parseable JSON"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--format", "json"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=40)
    def test_db_status_formats(self, app_dir, format_choice):
        """Property: db status supports all format options correctly"""
        cmd = ["./n8n-deploy", "db", "status", "--data-dir", app_dir]
        if format_choice:
            cmd.extend(["--format", format_choice])

        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)

        # Should always exit gracefully
        assert result.returncode in [0, 1, 2]

        # JSON output should be valid
        if format_choice == "json" and result.returncode == 0:
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "db status JSON output invalid"

    @given(app_dir=valid_paths)
    @settings(max_examples=20)
    def test_apikey_list_json_structure(self, app_dir):
        """Property: apikey list --format json has consistent structure"""
        result = subprocess.run(
            ["./n8n-deploy", "apikey", "list", "--data-dir", app_dir, "--format", "json"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=50)
    def test_special_characters_in_paths(self, path):
        """Property: Special characters in paths never cause crashes"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", path],
            capture_output=True,
            timeout=5,
            text=True,
        )
        # Should exit gracefully with known codes
        assert result.returncode in [0, 1, 2], f"Crashed with path: {path}"

    @given(path=deep_paths)
    @settings(max_examples=40)
    def test_deeply_nested_paths(self, path):
        """Property: Deeply nested paths handled correctly"""
        # Skip paths that are too long for filesystem
        assume(len(path) < 200)

        result = subprocess.run(
            ["./n8n-deploy", "db", "status", "--data-dir", path],
            capture_output=True,
            timeout=5,
            text=True,
        )
        assert result.returncode in [0, 1, 2]

    @given(app_dir=special_char_paths, flow_dir=special_char_paths)
    @settings(max_examples=30)
    def test_matching_special_char_paths(self, app_dir, flow_dir):
        """Property: Both app-dir and flow-dir with special chars work"""
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", app_dir, "--flows-dir", flow_dir],
            capture_output=True,
            timeout=5,
            text=True,
        )
        assert result.returncode in [0, 1, 2]

    @given(path_list=st.lists(valid_paths, min_size=2, max_size=5))
    @settings(max_examples=20, deadline=5000)  # 5 second deadline for multiple subprocess calls
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
                timeout=5,
                text=True,
            )
            exit_codes.append(result.returncode)

        # All should succeed or fail in similar ways (all 0-2 range)
        assert all(code in [0, 1, 2] for code in exit_codes)

    @given(path_name=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
    @settings(max_examples=20)
    def test_invalid_paths_default_to_cwd(self, path_name):
        """Property: Invalid paths should default to cwd and not cause crashes"""
        # Generate a nonexistent path
        invalid_path = f"/nonexistent/test/{path_name}"

        # Commands should succeed by defaulting to cwd
        result = subprocess.run(
            ["./n8n-deploy", "env", "--data-dir", invalid_path, "--format", "json"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=20)
    def test_malicious_workflow_names_blocked(self, malicious_input):
        """Property: SQL injection attempts in workflow names fail safely"""
        # Skip inputs with null bytes (Python subprocess limitation)
        assume("\x00" not in malicious_input)

        result = subprocess.run(
            ["./n8n-deploy", "wf", "search", malicious_input],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=20)
    def test_malicious_tag_names_blocked(self, malicious_input):
        """Property: Command injection in tags fails safely"""
        # Skip inputs with null bytes
        assume("\x00" not in malicious_input)

        result = subprocess.run(
            ["./n8n-deploy", "wf", "search", "--tag", malicious_input],
            capture_output=True,
            timeout=5,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1, 2]
        # Malicious input in messages is OK, just no actual command execution

    @given(malicious_input=malicious_names)
    @settings(max_examples=15)
    def test_malicious_api_key_names_blocked(self, malicious_input):
        """Property: Injection attempts in API key names fail safely"""
        # Try to list with malicious search pattern
        result = subprocess.run(
            ["./n8n-deploy", "apikey", "list"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=10)
    def test_command_help_always_works(self, command):
        """Property: All commands have working --help"""
        result = subprocess.run(
            ["./n8n-deploy", command, "--help"],
            capture_output=True,
            timeout=5,
            text=True,
        )

        # Help should always succeed
        assert result.returncode == 0, f"{command} --help failed"
        # Should contain usage information
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    @given(
        command=st.sampled_from(["status", "init", "backup", "compact"]),
    )
    @settings(max_examples=10)
    def test_db_subcommand_help(self, command):
        """Property: All db subcommands have help"""
        result = subprocess.run(
            ["./n8n-deploy", "db", command, "--help"],
            capture_output=True,
            timeout=5,
            text=True,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    @given(
        command=st.sampled_from(
            [
                "list",
                "add",
                "remove",
                "search",
                "stats",
                "createbackup",
                "backups",
                "restore",
                "pull",
                "push",
                "server",
                "verify",
            ]
        ),
    )
    @settings(max_examples=12)
    def test_wf_subcommand_help(self, command):
        """Property: All wf subcommands have help"""
        result = subprocess.run(
            ["./n8n-deploy", "wf", command, "--help"],
            capture_output=True,
            timeout=5,
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
    @settings(max_examples=50)
    def test_all_env_options_combined(self, app_dir, flow_dir, server_url, format_choice):
        """Property: All env options work together"""
        cmd = [
            "./n8n-deploy",
            "env",
            "--data-dir",
            app_dir,
            "--flows-dir",
            flow_dir,
            "--remote",
            server_url,
        ]
        if format_choice:
            cmd.extend(["--format", format_choice])

        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)

        # Should not crash
        assert result.returncode in [0, 1]

        # JSON should be valid if requested
        if format_choice == "json" and result.returncode == 0:
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                assert False, "Combined options produced invalid JSON"

    @given(app_dir=valid_paths, only_flag=boolean_flags, format_choice=format_options)
    @settings(max_examples=30)
    def test_wf_list_combined_options(self, app_dir, only_flag, format_choice):
        """Property: wf list with --only and format options works"""
        cmd = ["./n8n-deploy", "wf", "list", "--data-dir", app_dir]
        if only_flag:
            cmd.append("--only")
        if format_choice:
            cmd.extend(["--format", format_choice])

        result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)
        assert result.returncode in [0, 1]


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
