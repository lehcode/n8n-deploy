#!/usr/bin/env python3
"""
HTTP client for n8n API requests

Provides a unified HTTP layer for making authenticated requests to n8n servers.
Extracted from n8n_api.py to reduce complexity and improve testability.
"""

import warnings
from typing import Any, Dict, Optional

import requests
from urllib3.exceptions import InsecureRequestWarning

from .types import N8nApiErrorType, N8nApiResult


class N8nHttpClient:
    """HTTP client for n8n API requests

    Handles all HTTP communication with n8n servers, including:
    - Request construction and execution
    - SSL verification control
    - Error handling and categorization
    - Response parsing
    """

    DEFAULT_TIMEOUT = 10

    def __init__(self, skip_ssl_verify: bool = False) -> None:
        """Initialize HTTP client

        Args:
            skip_ssl_verify: If True, disable SSL certificate verification
        """
        self.skip_ssl_verify = skip_ssl_verify

        # Suppress InsecureRequestWarning when SSL verification is disabled
        if skip_ssl_verify:
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
        silent: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> N8nApiResult:
        """Make HTTP request with typed result

        Returns N8nApiResult with detailed error information, allowing callers
        to distinguish between different error types (404 vs network errors, etc.).

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL to request
            headers: Request headers (including authentication)
            data: Optional request payload for POST/PUT
            silent: If True, suppress error messages
            timeout: Request timeout in seconds

        Returns:
            N8nApiResult with success status and either data or error details
        """
        try:
            response = self._execute_request(method, url, headers, data, timeout)
            return self._handle_response(response, silent)

        except requests.exceptions.Timeout:
            if not silent:
                print(f"❌ n8n API request timed out after {timeout} seconds")
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.TIMEOUT,
                error_message=f"Request timed out after {timeout} seconds",
            )
        except requests.exceptions.ConnectionError as e:
            if not silent:
                print(f"❌ n8n API connection error: {e}")
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.NETWORK_ERROR,
                error_message=str(e),
            )
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"❌ n8n API request failed: {e}")
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.UNKNOWN,
                error_message=str(e),
            )

    def request_dict(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
        silent: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request returning dict or None

        Convenience wrapper around request() for backwards compatibility.
        Returns the response data dict on success, None on failure.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL to request
            headers: Request headers (including authentication)
            data: Optional request payload for POST/PUT
            silent: If True, suppress error messages
            timeout: Request timeout in seconds

        Returns:
            Response data dict on success, None on failure
        """
        result = self.request(method, url, headers, data, silent, timeout)
        return result.data if result.success else None

    def _execute_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]],
        timeout: int,
    ) -> requests.Response:
        """Execute the HTTP request

        Args:
            method: HTTP method
            url: Full URL
            headers: Request headers
            data: Optional payload
            timeout: Request timeout

        Returns:
            requests.Response object

        Raises:
            ValueError: For unsupported HTTP methods
            requests.exceptions.*: For network/request errors
        """
        method_upper = method.upper()
        verify = not self.skip_ssl_verify

        if method_upper == "GET":
            return requests.get(url, headers=headers, verify=verify, timeout=timeout)
        elif method_upper == "POST":
            return requests.post(url, headers=headers, json=data, verify=verify, timeout=timeout)
        elif method_upper == "PUT":
            return requests.put(url, headers=headers, json=data, verify=verify, timeout=timeout)
        elif method_upper == "DELETE":
            return requests.delete(url, headers=headers, verify=verify, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _handle_response(self, response: requests.Response, silent: bool) -> N8nApiResult:
        """Handle HTTP response and convert to N8nApiResult

        Args:
            response: The HTTP response
            silent: If True, suppress error messages

        Returns:
            N8nApiResult with appropriate status and data/error
        """
        # Handle specific status codes BEFORE raise_for_status()
        if response.status_code == 404:
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.NOT_FOUND,
                error_message="Resource not found on server",
                status_code=404,
            )

        if response.status_code in (401, 403):
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.AUTH_FAILURE,
                error_message="Authentication/authorization failed",
                status_code=response.status_code,
            )

        if response.status_code >= 500:
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.SERVER_ERROR,
                error_message=f"Server error: {response.status_code}",
                status_code=response.status_code,
            )

        # Raise for any other error status codes
        response.raise_for_status()

        # Parse JSON response
        try:
            result = response.json()
            return N8nApiResult(
                success=True,
                data=result if isinstance(result, dict) else None,
                status_code=response.status_code,
            )
        except ValueError:
            # Response is not JSON (e.g., 204 No Content)
            return N8nApiResult(
                success=True,
                data=None,
                status_code=response.status_code,
            )

    def delete_workflow(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Delete a workflow from n8n server

        Special handling for DELETE requests that may return 204 No Content.

        Args:
            url: Full URL to the workflow endpoint
            headers: Request headers (including authentication)
            timeout: Request timeout in seconds

        Returns:
            True if deletion successful (including 404 - already deleted)
        """
        try:
            response = requests.delete(
                url,
                headers=headers,
                verify=not self.skip_ssl_verify,
                timeout=timeout,
            )
            response.raise_for_status()
            return True

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                # Consider 404 as success - workflow is gone
                return True
            print(f"❌ Failed to delete workflow: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to delete workflow: {e}")
            return False
