"""Google OAuth 2.0 authorization-code flow helpers.

This module is import-safe even when GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are
unset or placeholder values (as in local dev) - it will only fail at runtime,
when an actual request to Google is attempted, not at import time.
"""
import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthError(Exception):
    """Raised when the Google OAuth flow fails (network error, bad response, etc.)."""


def build_authorization_url(state: str, redirect_uri: str) -> str:
    """Build the URL to redirect the browser to for Google's consent screen.

    `state` is an opaque, unguessable value the caller must persist (e.g. in a
    signed cookie or server-side store) and verify on callback to prevent CSRF.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


async def exchange_code_for_token(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange an OAuth authorization code for Google access/id tokens."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise GoogleOAuthError("Google OAuth is not configured on this server")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
        except httpx.HTTPError as exc:
            logger.warning("Google token exchange request failed: %s", exc)
            raise GoogleOAuthError("Failed to reach Google token endpoint") from exc

    if response.status_code != 200:
        logger.warning("Google token exchange returned %s: %s", response.status_code, response.text)
        raise GoogleOAuthError("Google rejected the authorization code")

    return response.json()


async def fetch_google_userinfo(access_token: str) -> dict[str, Any]:
    """Fetch the authenticated Google user's profile (id, email, name, ...)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as exc:
            logger.warning("Google userinfo request failed: %s", exc)
            raise GoogleOAuthError("Failed to reach Google userinfo endpoint") from exc

    if response.status_code != 200:
        logger.warning("Google userinfo returned %s: %s", response.status_code, response.text)
        raise GoogleOAuthError("Failed to fetch Google user profile")

    return response.json()
