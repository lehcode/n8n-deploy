#!/usr/bin/env python3
"""
JWT utility functions for n8n-deploy

Provides functions to decode and validate JWT tokens, particularly for
checking API key expiration.
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, cast


def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token payload without verification.

    Args:
        token: JWT token string

    Returns:
        Decoded payload as dictionary, or None if decoding fails
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (second part)
        # Add padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = base64.urlsafe_b64decode(payload)
        return cast(Dict[str, Any], json.loads(decoded))
    except Exception:
        return None


def check_jwt_expiration(token: str) -> Tuple[bool, Optional[datetime], Optional[str]]:
    """
    Check if JWT token is expired or expiring soon.

    Args:
        token: JWT token string

    Returns:
        Tuple of (is_expired, expiration_datetime, warning_message)
        - is_expired: True if token is expired
        - expiration_datetime: When the token expires (or None if can't decode)
        - warning_message: Human-readable warning message (or None if not expired)
    """
    payload = decode_jwt_payload(token)
    if not payload or "exp" not in payload:
        return False, None, None

    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    now = datetime.now()

    # Check if expired
    if exp_datetime < now:
        days_ago = (now - exp_datetime).days
        if days_ago == 0:
            msg = "⚠️  API key expired today"
        elif days_ago == 1:
            msg = "⚠️  API key expired yesterday"
        else:
            msg = f"⚠️  API key expired {days_ago} days ago"
        return True, exp_datetime, msg

    # Check if expiring soon (within 7 days)
    time_until_expiry = exp_datetime - now
    if time_until_expiry < timedelta(days=7):
        days_left = time_until_expiry.days
        hours_left = time_until_expiry.seconds // 3600

        if days_left == 0:
            if hours_left <= 1:
                msg = f"⚠️  API key expires in {hours_left} hour(s)"
            else:
                msg = f"⚠️  API key expires in {hours_left} hour(s)"
        elif days_left == 1:
            msg = "⚠️  API key expires tomorrow"
        else:
            msg = f"⚠️  API key expires in {days_left} days"

        return False, exp_datetime, msg

    # Not expired and not expiring soon
    return False, exp_datetime, None


def format_expiration_date(exp_datetime: Optional[datetime]) -> str:
    """
    Format expiration datetime for display.

    Args:
        exp_datetime: Expiration datetime

    Returns:
        Formatted date string
    """
    if not exp_datetime:
        return "Unknown"
    return exp_datetime.strftime("%Y-%m-%d %H:%M")


def get_jwt_issued_at(token: str) -> Optional[datetime]:
    """
    Extract the issued-at (iat) timestamp from JWT token.

    Args:
        token: JWT token string

    Returns:
        Datetime when the token was issued, or None if can't decode
    """
    payload = decode_jwt_payload(token)
    if not payload or "iat" not in payload:
        return None

    iat_timestamp = payload["iat"]
    return datetime.fromtimestamp(iat_timestamp)


def get_days_until_expiry(token: str) -> Optional[int]:
    """
    Get number of days until token expires.

    Args:
        token: JWT token string

    Returns:
        Number of days until expiry (negative if expired), or None if can't decode
    """
    payload = decode_jwt_payload(token)
    if not payload or "exp" not in payload:
        return None

    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    now = datetime.now()

    delta = exp_datetime - now
    return delta.days
