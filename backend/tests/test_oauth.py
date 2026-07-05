"""Tests for Google OAuth helpers (app/auth/oauth.py) and the /auth/google* routes.

`build_authorization_url` is tested directly as a pure function. The async
network calls (`exchange_code_for_token`, `fetch_google_userinfo`) are tested
by monkeypatching `httpx.AsyncClient` with a fake async context manager so no
real network call is ever made. The router-level flow (state CSRF check,
success/failure redirects) is tested through the `client` TestClient fixture,
with `app.routers.auth.exchange_code_for_token` / `fetch_google_userinfo`
monkeypatched directly.
"""
from types import TracebackType
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth.oauth import GoogleOAuthError, build_authorization_url, exchange_code_for_token, fetch_google_userinfo
from app.config import settings


# --- build_authorization_url (pure function) ---------------------------------


def test_build_authorization_url_encodes_all_params(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    url = build_authorization_url("abc123state", "https://api.example.com/api/v1/auth/google/callback")

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert parsed.path == "/o/oauth2/v2/auth"

    query = parse_qs(parsed.query)
    assert query["client_id"] == [settings.GOOGLE_CLIENT_ID]
    assert query["redirect_uri"] == ["https://api.example.com/api/v1/auth/google/callback"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == ["abc123state"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["select_account"]


# --- Fake httpx.AsyncClient for exchange_code_for_token / fetch_google_userinfo ---


class _FakeResponse:
    def __init__(self, status_code: int, json_data: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._json_data


class _FakeAsyncClient:
    """Stand-in for httpx.AsyncClient supporting the `async with` pattern."""

    def __init__(self, response: _FakeResponse | None = None, raise_error: Exception | None = None) -> None:
        self._response = response
        self._raise_error = raise_error

    def __call__(self, *args: Any, **kwargs: Any) -> "_FakeAsyncClient":
        return self

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> bool:
        return False

    async def post(self, *args: Any, **kwargs: Any) -> _FakeResponse:
        if self._raise_error:
            raise self._raise_error
        assert self._response is not None
        return self._response

    async def get(self, *args: Any, **kwargs: Any) -> _FakeResponse:
        return await self.post(*args, **kwargs)


# --- exchange_code_for_token ---------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_code_for_token_raises_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")

    with pytest.raises(GoogleOAuthError, match="not configured"):
        await exchange_code_for_token("some-code", "https://example.com/callback")


@pytest.mark.asyncio
async def test_exchange_code_for_token_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "client-secret")
    fake_client = _FakeAsyncClient(raise_error=httpx.ConnectError("boom"))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    with pytest.raises(GoogleOAuthError, match="Failed to reach Google token endpoint"):
        await exchange_code_for_token("some-code", "https://example.com/callback")


@pytest.mark.asyncio
async def test_exchange_code_for_token_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "client-secret")
    fake_client = _FakeAsyncClient(response=_FakeResponse(400, text="invalid_grant"))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    with pytest.raises(GoogleOAuthError, match="rejected the authorization code"):
        await exchange_code_for_token("bad-code", "https://example.com/callback")


@pytest.mark.asyncio
async def test_exchange_code_for_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "client-secret")
    fake_client = _FakeAsyncClient(response=_FakeResponse(200, json_data={"access_token": "tok-123", "id_token": "id-1"}))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    result = await exchange_code_for_token("good-code", "https://example.com/callback")

    assert result == {"access_token": "tok-123", "id_token": "id-1"}


# --- fetch_google_userinfo -----------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_google_userinfo_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(raise_error=httpx.ConnectError("boom"))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    with pytest.raises(GoogleOAuthError, match="Failed to reach Google userinfo endpoint"):
        await fetch_google_userinfo("access-token")


@pytest.mark.asyncio
async def test_fetch_google_userinfo_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(response=_FakeResponse(401, text="invalid token"))
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    with pytest.raises(GoogleOAuthError, match="Failed to fetch Google user profile"):
        await fetch_google_userinfo("bad-access-token")


@pytest.mark.asyncio
async def test_fetch_google_userinfo_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeAsyncClient(
        response=_FakeResponse(200, json_data={"email": "user@example.com", "name": "User One"})
    )
    monkeypatch.setattr(httpx, "AsyncClient", fake_client)

    result = await fetch_google_userinfo("access-token")

    assert result == {"email": "user@example.com", "name": "User One"}


# --- /auth/google (router) ------------------------------------------------------


def test_google_login_redirects_to_google_and_sets_state_cookie(client: TestClient) -> None:
    response = client.get("/api/v1/auth/google", follow_redirects=False)

    assert response.status_code in (302, 307)
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "google_oauth_state" in response.cookies


# --- /auth/google/callback (router) ---------------------------------------------


def test_google_callback_rejects_missing_state_cookie(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "expected-state"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_google_callback_rejects_state_mismatch(client: TestClient) -> None:
    client.cookies.set("google_oauth_state", "cookie-state")
    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "different-state"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_google_callback_oauth_error_returns_401(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise_exchange(code: str, redirect_uri: str) -> dict[str, Any]:
        raise GoogleOAuthError("Google rejected the authorization code")

    monkeypatch.setattr("app.routers.auth.exchange_code_for_token", _raise_exchange)

    client.cookies.set("google_oauth_state", "matching-state")
    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "matching-state"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_google_callback_missing_email_returns_401(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_exchange(code: str, redirect_uri: str) -> dict[str, Any]:
        return {"access_token": "tok-123"}

    async def _fake_userinfo(access_token: str) -> dict[str, Any]:
        return {"name": "No Email User"}

    monkeypatch.setattr("app.routers.auth.exchange_code_for_token", _fake_exchange)
    monkeypatch.setattr("app.routers.auth.fetch_google_userinfo", _fake_userinfo)

    client.cookies.set("google_oauth_state", "matching-state")
    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "some-code", "state": "matching-state"},
        follow_redirects=False,
    )
    assert response.status_code == 401


def test_google_callback_success_creates_user_and_redirects_with_tokens(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _fake_exchange(code: str, redirect_uri: str) -> dict[str, Any]:
        assert code == "valid-code"
        return {"access_token": "google-access-tok"}

    async def _fake_userinfo(access_token: str) -> dict[str, Any]:
        assert access_token == "google-access-tok"
        return {"email": "new.oauth.user@example.com", "name": "New OAuth User"}

    monkeypatch.setattr("app.routers.auth.exchange_code_for_token", _fake_exchange)
    monkeypatch.setattr("app.routers.auth.fetch_google_userinfo", _fake_userinfo)

    client.cookies.set("google_oauth_state", "matching-state")
    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "valid-code", "state": "matching-state"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 307)
    location = response.headers["location"]
    # The redirect URL carries no tokens at all - they are set as cookies.
    assert location == f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback"
    assert "access_token" not in location
    assert "refresh_token" not in location

    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any(h.startswith("access_token=") and "HttpOnly" in h for h in set_cookie_headers)
    assert any(h.startswith("refresh_token=") and "HttpOnly" in h for h in set_cookie_headers)

    # The CSRF state cookie must be cleared after a successful callback.
    assert response.cookies.get("google_oauth_state") is None
