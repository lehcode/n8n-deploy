"""Unit tests for N8nApiResult dataclass and its properties."""

from assertpy import assert_that

from api.workflow.types import N8nApiErrorType, N8nApiResult


class TestN8nApiResult:
    """Tests for N8nApiResult dataclass and its properties"""

    def test_is_not_found_true_for_404(self) -> None:
        """Test is_not_found returns True for NOT_FOUND error type"""
        result = N8nApiResult(success=False, error_type=N8nApiErrorType.NOT_FOUND)
        assert_that(result.is_not_found).is_true()
        assert_that(result.is_network_error).is_false()
        assert_that(result.is_auth_error).is_false()
        assert_that(result.is_server_error).is_false()

    def test_is_network_error_true_for_connection_errors(self) -> None:
        """Test is_network_error returns True for network-related errors"""
        result = N8nApiResult(success=False, error_type=N8nApiErrorType.NETWORK_ERROR)
        assert_that(result.is_network_error).is_true()
        assert_that(result.is_not_found).is_false()

    def test_is_network_error_true_for_timeout(self) -> None:
        """Test is_network_error returns True for timeout errors"""
        result = N8nApiResult(success=False, error_type=N8nApiErrorType.TIMEOUT)
        assert_that(result.is_network_error).is_true()

    def test_is_auth_error_true_for_auth_failure(self) -> None:
        """Test is_auth_error returns True for auth failures"""
        result = N8nApiResult(success=False, error_type=N8nApiErrorType.AUTH_FAILURE)
        assert_that(result.is_auth_error).is_true()
        assert_that(result.is_not_found).is_false()

    def test_is_server_error_true_for_5xx(self) -> None:
        """Test is_server_error returns True for server errors"""
        result = N8nApiResult(success=False, error_type=N8nApiErrorType.SERVER_ERROR)
        assert_that(result.is_server_error).is_true()

    def test_successful_result_all_checks_false(self) -> None:
        """Test successful result has all error checks returning False"""
        result = N8nApiResult(success=True, data={"id": "test"})
        assert_that(result.is_not_found).is_false()
        assert_that(result.is_network_error).is_false()
        assert_that(result.is_auth_error).is_false()
        assert_that(result.is_server_error).is_false()
