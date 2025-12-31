#!/usr/bin/env python3
"""
SSL utilities for n8n API clients

Provides shared SSL warning management to avoid duplicate warnings
across multiple HTTP client modules.
"""

from typing import Optional

import urllib3
from requests import Session


# Track if SSL warning has been shown (module-level to show only once)
_ssl_warning_shown = False


def configure_ssl_verification(
    skip_verify: bool,
    session: Optional[Session] = None,
) -> None:
    """Configure SSL verification and show warning once.

    Suppresses urllib3 InsecureRequestWarning and optionally configures
    a requests Session to skip SSL verification.

    Args:
        skip_verify: If True, disable SSL certificate verification
        session: Optional requests Session to configure
    """
    global _ssl_warning_shown

    if not skip_verify:
        return

    # Suppress urllib3 warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Configure session if provided
    if session is not None:
        session.verify = False

    # Show custom warning once
    if not _ssl_warning_shown:
        print("⚠️  SSL verification disabled - using insecure connection")
        _ssl_warning_shown = True


def reset_ssl_warning_state() -> None:
    """Reset the SSL warning shown state (for testing purposes)."""
    global _ssl_warning_shown
    _ssl_warning_shown = False
