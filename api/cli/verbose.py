#!/usr/bin/env python3
"""
Verbose HTTP logging utilities for n8n-deploy CLI

Provides structured HTTP request/response logging to stderr when verbose mode
is enabled. Masks sensitive data (API keys) in output.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import click


@dataclass
class VerboseConfig:
    """Configuration for verbose output

    Supports multiple verbosity levels:
    - 0: Disabled (default)
    - 1: Basic verbose (-v) - method, URL, headers, status, timing
    - 2: Extended verbose (-vv) - includes response body
    """

    level: int = 0


# Global verbose state (set by CLI callback)
_verbose_config = VerboseConfig()


def set_verbose(level: int) -> None:
    """Set global verbose level

    Args:
        level: Verbosity level (0=off, 1=-v, 2=-vv)
    """
    _verbose_config.level = level


def is_verbose() -> bool:
    """Check if verbose mode is enabled (any level)

    Returns:
        True if verbosity level is 1 or higher
    """
    return _verbose_config.level >= 1


def get_verbose_level() -> int:
    """Get current verbosity level

    Returns:
        Current verbosity level (0=off, 1=-v, 2=-vv)
    """
    return _verbose_config.level


def mask_api_key(value: str) -> str:
    """Mask API key for display, showing first 4 and last 4 characters

    Args:
        value: The API key value

    Returns:
        Masked string like "eyJh...5imE" or "****" if too short
    """
    if len(value) <= 12:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def mask_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Create a copy of headers with API key masked

    Args:
        headers: Original headers dict

    Returns:
        New dict with X-N8N-API-KEY value masked
    """
    masked = headers.copy()
    if "X-N8N-API-KEY" in masked:
        masked["X-N8N-API-KEY"] = mask_api_key(masked["X-N8N-API-KEY"])
    return masked


def log_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[Dict[str, Any]] = None,
) -> float:
    """Log HTTP request details to stderr

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        headers: Request headers (will be masked)
        data: Optional request body

    Returns:
        Start time for duration calculation
    """
    start_time = time.perf_counter()

    if _verbose_config.level < 1:
        return start_time

    click.echo(f"[VERBOSE] --> {method.upper()} {url}", err=True)

    masked_headers = mask_headers(headers)
    for key, value in masked_headers.items():
        click.echo(f"[VERBOSE]     {key}: {value}", err=True)

    if data:
        import json

        data_str = json.dumps(data)
        if len(data_str) > 500:
            data_str = data_str[:500] + "... (truncated)"
        click.echo(f"[VERBOSE]     Body: {data_str}", err=True)

    return start_time


def log_response(
    status_code: int,
    headers: Dict[str, str],
    start_time: float,
    response_body: Optional[str] = None,
) -> None:
    """Log HTTP response details to stderr

    Args:
        status_code: HTTP response status code
        headers: Response headers
        start_time: Request start time for duration calculation
        response_body: Optional response body (shown at -vv level)
    """
    if _verbose_config.level < 1:
        return

    duration_ms = (time.perf_counter() - start_time) * 1000

    click.echo(f"[VERBOSE] <-- {status_code} ({duration_ms:.0f}ms)", err=True)

    # Log select response headers
    interesting_headers = ["Content-Type", "Content-Length", "X-RateLimit-Remaining"]
    for key in interesting_headers:
        if key in headers:
            click.echo(f"[VERBOSE]     {key}: {headers[key]}", err=True)

    # At -vv level, show response body
    if _verbose_config.level >= 2 and response_body:
        body_display = response_body
        if len(response_body) > 1000:
            body_display = response_body[:1000] + "... (truncated)"
        click.echo(f"[VERBOSE]     Response: {body_display}", err=True)


def log_error(error_type: str, message: str) -> None:
    """Log error details to stderr

    Args:
        error_type: Type of error (TIMEOUT, CONNECTION, etc.)
        message: Error message
    """
    if _verbose_config.level < 1:
        return

    click.echo(f"[VERBOSE] !!! {error_type}: {message}", err=True)
