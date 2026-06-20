"""Google OAuth helpers: code exchange + userinfo fetch.

If `settings.GOOGLE_CLIENT_ID` is empty, Google OAuth is considered
disabled. The calling router (app/routers/auth.py) is responsible for
checking that and returning 503 before invoking these helpers.
"""
import httpx

from app.config import settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def get_google_tokens(code: str) -> dict:
    """Exchange an authorization `code` for Google access/id/refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.FRONTEND_URL}/auth/callback",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_google_user(access_token: str) -> dict:
    """Fetch the Google userinfo profile for the given access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
