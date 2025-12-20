#!/usr/bin/env python3
"""
Unit tests for verbose HTTP logging utilities

Tests the verbose mode functionality including API key masking, header masking,
state management, and logging functions.
"""

import os
import sys
import time
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli.verbose import (
    get_verbose_level,
    is_verbose,
    log_error,
    log_request,
    log_response,
    mask_api_key,
    mask_headers,
    set_verbose,
)


class TestMaskApiKey:
    """Tests for API key masking"""

    def test_mask_long_key(self) -> None:
        """Long API key shows first 4 and last 4 characters"""
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123"
        result = mask_api_key(key)
        assert result == "eyJh...c123"

    def test_mask_short_key(self) -> None:
        """Short keys are fully masked"""
        assert mask_api_key("short") == "****"
        assert mask_api_key("12chars12345") == "****"

    def test_mask_exact_boundary_12_chars(self) -> None:
        """Test 12 character boundary (still masked)"""
        key = "123456789012"  # 12 chars
        result = mask_api_key(key)
        assert result == "****"

    def test_mask_exact_boundary_13_chars(self) -> None:
        """Test 13 character boundary (first visible)"""
        key = "1234567890123"  # 13 chars
        result = mask_api_key(key)
        assert result == "1234...0123"

    def test_mask_empty_key(self) -> None:
        """Empty key returns masked value"""
        assert mask_api_key("") == "****"

    def test_mask_typical_jwt(self) -> None:
        """Typical JWT token is properly masked"""
        # Use a clearly fake test token (not a real JWT)
        fake_jwt = "test_fake_jwt_token_for_unit_testing_purposes_only_1234567890abcdef"
        result = mask_api_key(fake_jwt)
        assert result == "test...cdef"
        assert len(result) == 11  # 4 + 3 (dots) + 4


class TestMaskHeaders:
    """Tests for header masking"""

    def test_masks_api_key_header(self) -> None:
        """X-N8N-API-KEY header is masked"""
        headers = {
            "X-N8N-API-KEY": "very_long_secret_api_key_here",
            "Content-Type": "application/json",
        }
        result = mask_headers(headers)
        assert result["X-N8N-API-KEY"] == "very...here"
        assert result["Content-Type"] == "application/json"

    def test_original_unchanged(self) -> None:
        """Original headers dict is not modified"""
        headers = {"X-N8N-API-KEY": "secret_key_12345678"}
        mask_headers(headers)
        assert headers["X-N8N-API-KEY"] == "secret_key_12345678"

    def test_headers_without_api_key(self) -> None:
        """Headers without API key are returned unchanged"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        result = mask_headers(headers)
        assert result == headers
        assert result is not headers  # Should be a copy

    def test_empty_headers(self) -> None:
        """Empty headers dict returns empty dict"""
        result = mask_headers({})
        assert result == {}


class TestVerboseState:
    """Tests for verbose mode state management"""

    def setup_method(self) -> None:
        """Reset verbose state before each test"""
        set_verbose(0)

    def teardown_method(self) -> None:
        """Reset verbose state after each test"""
        set_verbose(0)

    def test_default_disabled(self) -> None:
        """Verbose mode is disabled by default after reset"""
        set_verbose(0)  # Explicit reset
        assert is_verbose() is False

    def test_enable_verbose(self) -> None:
        """Verbose mode can be enabled"""
        set_verbose(1)
        assert is_verbose() is True

    def test_disable_verbose(self) -> None:
        """Verbose mode can be disabled"""
        set_verbose(1)
        set_verbose(0)
        assert is_verbose() is False

    def test_toggle_verbose(self) -> None:
        """Verbose mode can be toggled multiple times"""
        assert is_verbose() is False
        set_verbose(1)
        assert is_verbose() is True
        set_verbose(0)
        assert is_verbose() is False
        set_verbose(1)
        assert is_verbose() is True


class TestLogRequest:
    """Tests for log_request function"""

    def setup_method(self) -> None:
        """Enable verbose for logging tests"""
        set_verbose(1)

    def teardown_method(self) -> None:
        """Reset verbose state"""
        set_verbose(0)

    def test_log_request_returns_start_time(self) -> None:
        """log_request returns start time for duration calculation"""
        before = time.perf_counter()
        start = log_request("GET", "http://example.com", {})
        after = time.perf_counter()

        assert before <= start <= after

    def test_log_request_returns_time_when_disabled(self) -> None:
        """log_request returns time even when verbose is disabled"""
        set_verbose(0)
        before = time.perf_counter()
        start = log_request("GET", "http://example.com", {})
        after = time.perf_counter()

        assert before <= start <= after

    def test_log_request_outputs_to_stderr(self) -> None:
        """log_request outputs to stderr"""
        with patch("click.echo") as mock_echo:
            log_request("GET", "http://example.com/api", {"Content-Type": "application/json"})

            # Verify stderr output (err=True)
            assert mock_echo.called
            calls = mock_echo.call_args_list
            # All calls should have err=True
            for call in calls:
                assert call.kwargs.get("err") is True

    def test_log_request_shows_method_and_url(self) -> None:
        """log_request shows HTTP method and URL"""
        with patch("click.echo") as mock_echo:
            log_request("POST", "http://example.com/api/workflows", {})

            output = str(mock_echo.call_args_list)
            assert "POST" in output
            assert "example.com" in output

    def test_log_request_masks_api_key(self) -> None:
        """log_request masks API key in output"""
        with patch("click.echo") as mock_echo:
            log_request("GET", "http://example.com", {"X-N8N-API-KEY": "very_long_secret_api_key_value"})

            output = str(mock_echo.call_args_list)
            assert "very_long_secret_api_key_value" not in output
            assert "very...alue" in output

    def test_log_request_shows_headers(self) -> None:
        """log_request shows request headers"""
        with patch("click.echo") as mock_echo:
            log_request(
                "GET",
                "http://example.com",
                {"Content-Type": "application/json", "Accept": "application/json"},
            )

            output = str(mock_echo.call_args_list)
            assert "Content-Type" in output
            assert "application/json" in output

    def test_log_request_shows_body_when_provided(self) -> None:
        """log_request shows request body when data is provided"""
        with patch("click.echo") as mock_echo:
            log_request(
                "POST",
                "http://example.com",
                {},
                data={"name": "test-workflow", "nodes": []},
            )

            output = str(mock_echo.call_args_list)
            assert "Body" in output
            assert "test-workflow" in output

    def test_log_request_truncates_large_body(self) -> None:
        """log_request truncates large request bodies"""
        with patch("click.echo") as mock_echo:
            large_data = {"data": "x" * 1000}
            log_request("POST", "http://example.com", {}, data=large_data)

            output = str(mock_echo.call_args_list)
            assert "truncated" in output

    def test_log_request_no_output_when_disabled(self) -> None:
        """No output when verbose mode is disabled"""
        set_verbose(0)

        with patch("click.echo") as mock_echo:
            log_request("GET", "http://example.com", {"X-N8N-API-KEY": "secret"})
            mock_echo.assert_not_called()


class TestLogResponse:
    """Tests for log_response function"""

    def setup_method(self) -> None:
        """Enable verbose for logging tests"""
        set_verbose(1)

    def teardown_method(self) -> None:
        """Reset verbose state"""
        set_verbose(0)

    def test_log_response_shows_status_code(self) -> None:
        """log_response shows HTTP status code"""
        with patch("click.echo") as mock_echo:
            log_response(200, {}, time.perf_counter())

            output = str(mock_echo.call_args_list)
            assert "200" in output

    def test_log_response_shows_duration(self) -> None:
        """log_response shows request duration in ms"""
        with patch("click.echo") as mock_echo:
            start = time.perf_counter() - 0.5  # Simulate 500ms request
            log_response(200, {}, start)

            output = str(mock_echo.call_args_list)
            assert "ms" in output

    def test_log_response_outputs_to_stderr(self) -> None:
        """log_response outputs to stderr"""
        with patch("click.echo") as mock_echo:
            log_response(200, {}, time.perf_counter())

            assert mock_echo.called
            for call in mock_echo.call_args_list:
                assert call.kwargs.get("err") is True

    def test_log_response_shows_interesting_headers(self) -> None:
        """log_response shows select response headers"""
        with patch("click.echo") as mock_echo:
            log_response(
                200,
                {"Content-Type": "application/json", "Content-Length": "1234"},
                time.perf_counter(),
            )

            output = str(mock_echo.call_args_list)
            assert "Content-Type" in output
            assert "application/json" in output

    def test_log_response_no_output_when_disabled(self) -> None:
        """No output when verbose mode is disabled"""
        set_verbose(0)

        with patch("click.echo") as mock_echo:
            log_response(200, {"Content-Type": "application/json"}, time.perf_counter())
            mock_echo.assert_not_called()


class TestLogError:
    """Tests for log_error function"""

    def setup_method(self) -> None:
        """Enable verbose for logging tests"""
        set_verbose(1)

    def teardown_method(self) -> None:
        """Reset verbose state"""
        set_verbose(0)

    def test_log_error_shows_error_type(self) -> None:
        """log_error shows error type"""
        with patch("click.echo") as mock_echo:
            log_error("TIMEOUT", "Connection timed out")

            output = str(mock_echo.call_args_list)
            assert "TIMEOUT" in output

    def test_log_error_shows_message(self) -> None:
        """log_error shows error message"""
        with patch("click.echo") as mock_echo:
            log_error("CONNECTION", "Connection refused")

            output = str(mock_echo.call_args_list)
            assert "Connection refused" in output

    def test_log_error_outputs_to_stderr(self) -> None:
        """log_error outputs to stderr"""
        with patch("click.echo") as mock_echo:
            log_error("TEST", "Test error")

            assert mock_echo.called
            for call in mock_echo.call_args_list:
                assert call.kwargs.get("err") is True

    def test_log_error_no_output_when_disabled(self) -> None:
        """No output when verbose mode is disabled"""
        set_verbose(0)

        with patch("click.echo") as mock_echo:
            log_error("TEST", "Test error")
            mock_echo.assert_not_called()

    def test_log_error_prefix_format(self) -> None:
        """log_error uses !!! prefix for visibility"""
        with patch("click.echo") as mock_echo:
            log_error("NETWORK", "Host unreachable")

            output = str(mock_echo.call_args_list)
            assert "!!!" in output


class TestVerboseLevels:
    """Tests for verbosity levels"""

    def setup_method(self) -> None:
        """Reset verbose state before each test"""
        set_verbose(0)

    def teardown_method(self) -> None:
        """Reset verbose state after each test"""
        set_verbose(0)

    def test_level_0_is_not_verbose(self) -> None:
        """Level 0 means verbose is disabled"""
        set_verbose(0)
        assert is_verbose() is False
        assert get_verbose_level() == 0

    def test_level_1_is_verbose(self) -> None:
        """Level 1 (-v) means verbose is enabled"""
        set_verbose(1)
        assert is_verbose() is True
        assert get_verbose_level() == 1

    def test_level_2_is_verbose(self) -> None:
        """Level 2 (-vv) means extended verbose is enabled"""
        set_verbose(2)
        assert is_verbose() is True
        assert get_verbose_level() == 2

    def test_higher_levels_are_verbose(self) -> None:
        """Any level > 0 is verbose"""
        set_verbose(5)
        assert is_verbose() is True
        assert get_verbose_level() == 5


class TestLogResponseBody:
    """Tests for response body logging at -vv"""

    def setup_method(self) -> None:
        """Enable extended verbose (-vv) for tests"""
        set_verbose(2)

    def teardown_method(self) -> None:
        """Reset verbose state"""
        set_verbose(0)

    def test_response_body_shown_at_level_2(self) -> None:
        """Response body is shown at -vv level"""
        with patch("click.echo") as mock_echo:
            log_response(400, {}, time.perf_counter(), '{"error": "Bad Request"}')

            output = str(mock_echo.call_args_list)
            assert "Response:" in output
            assert "Bad Request" in output

    def test_response_body_hidden_at_level_1(self) -> None:
        """Response body is NOT shown at -v level"""
        set_verbose(1)

        with patch("click.echo") as mock_echo:
            log_response(400, {}, time.perf_counter(), '{"error": "Bad Request"}')

            output = str(mock_echo.call_args_list)
            assert "Response:" not in output

    def test_response_body_hidden_at_level_0(self) -> None:
        """Response body is NOT shown when disabled"""
        set_verbose(0)

        with patch("click.echo") as mock_echo:
            log_response(400, {}, time.perf_counter(), '{"error": "Bad Request"}')
            mock_echo.assert_not_called()

    def test_response_body_truncated(self) -> None:
        """Long response body is truncated"""
        with patch("click.echo") as mock_echo:
            large_body = "x" * 2000
            log_response(200, {}, time.perf_counter(), large_body)

            output = str(mock_echo.call_args_list)
            assert "truncated" in output

    def test_response_body_none_not_shown(self) -> None:
        """None response body is not logged"""
        with patch("click.echo") as mock_echo:
            log_response(200, {}, time.perf_counter(), None)

            output = str(mock_echo.call_args_list)
            assert "Response:" not in output

    def test_response_body_empty_string_not_shown(self) -> None:
        """Empty string response body is not logged"""
        with patch("click.echo") as mock_echo:
            log_response(200, {}, time.perf_counter(), "")

            output = str(mock_echo.call_args_list)
            assert "Response:" not in output


class TestVerboseCLIIntegration:
    """Tests for verbose option at CLI subcommand level"""

    def setup_method(self) -> None:
        """Reset verbose state before each test"""
        set_verbose(0)

    def teardown_method(self) -> None:
        """Reset verbose state after each test"""
        set_verbose(0)

    def test_wf_group_has_verbose_option(self) -> None:
        """wf command group has -v/--verbose option"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["wf", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output
        assert "Verbosity level" in result.output

    def test_db_group_has_verbose_option(self) -> None:
        """db command group has -v/--verbose option"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output

    def test_server_group_has_verbose_option(self) -> None:
        """server command group has -v/--verbose option"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["server", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output

    def test_apikey_group_has_verbose_option(self) -> None:
        """apikey command group has -v/--verbose option"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["apikey", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output

    def test_folder_group_has_verbose_option(self) -> None:
        """folder command group has -v/--verbose option"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["folder", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output

    def test_verbose_at_subcommand_level_accepted(self) -> None:
        """Verbose flag at subcommand level is accepted (no error)"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        # -v before help should not cause "No such option" error
        result = runner.invoke(cli, ["wf", "-v", "--help"])

        assert result.exit_code == 0
        assert "No such option" not in result.output

    def test_double_verbose_at_subcommand_level_accepted(self) -> None:
        """Double verbose (-vv) at subcommand level is accepted"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "-vv", "--help"])

        assert result.exit_code == 0
        assert "No such option" not in result.output

    def test_verbose_flag_long_form_at_subcommand(self) -> None:
        """--verbose long form works at subcommand level"""
        from click.testing import CliRunner
        from api.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["server", "--verbose", "--help"])

        assert result.exit_code == 0
        assert "No such option" not in result.output
