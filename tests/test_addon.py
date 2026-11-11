"""Unit tests for the Turnstile tool addon."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.addons.tools.turnstile.addon import TurnstileToolAddon
from app.addons.tools.turnstile.verify import SCRIPT_URL, validate_secret, verify_token
from app.core.exceptions import ValidationError

CONFIG = {
    "is_active": True,
    "site_key": 'site"key',
    "secret_key": "secret-key",
}


def _client(body: dict):
    request = httpx.Request("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify")
    response = httpx.Response(200, json=body, request=request)
    instance = AsyncMock()
    instance.post = AsyncMock(return_value=response)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    return instance


class TestTurnstileToolAddon:
    @pytest.mark.asyncio
    async def test_inactive_without_keys(self):
        addon = TurnstileToolAddon()
        await addon.initialize({"is_active": True, "site_key": "", "secret_key": ""})
        assert addon.protects_challenge("login") is False
        assert addon.challenge_public_config() is None
        assert addon.admin_challenge_widget_html() == ""

    @pytest.mark.asyncio
    async def test_public_config_and_widget_escape_site_key(self):
        addon = TurnstileToolAddon()
        await addon.initialize(CONFIG)
        assert addon.challenge_public_config() == {
            "site_key": 'site"key',
            "script_url": SCRIPT_URL,
            "actions": ["register", "login", "forgot_password"],
        }
        html = addon.admin_challenge_widget_html()
        assert "site&quot;key" in html
        assert 'site"key' not in html

    @pytest.mark.asyncio
    async def test_verify_requires_token(self):
        addon = TurnstileToolAddon()
        await addon.initialize(CONFIG)
        with pytest.raises(ValidationError, match="required"):
            await addon.verify_bot_challenge(None, None, "login")

    @pytest.mark.asyncio
    async def test_verify_success_and_rejection(self):
        addon = TurnstileToolAddon()
        await addon.initialize(CONFIG)
        with patch(
            "app.addons.tools.turnstile.verify.httpx.AsyncClient",
            return_value=_client({"success": True}),
        ):
            await addon.verify_bot_challenge("token", "127.0.0.1", "register")
        with patch(
            "app.addons.tools.turnstile.verify.httpx.AsyncClient",
            return_value=_client({"success": False, "error-codes": ["invalid-input-response"]}),
        ):
            with pytest.raises(ValidationError, match="failed"):
                await addon.verify_bot_challenge("token", None, "forgot_password")

    @pytest.mark.asyncio
    async def test_verify_fails_closed_when_cloudflare_is_down(self):
        with patch(
            "app.addons.tools.turnstile.verify.httpx.AsyncClient",
            side_effect=httpx.ConnectError("down"),
        ):
            with pytest.raises(ValidationError, match="could not be verified"):
                await verify_token("secret", "token", None)

    @pytest.mark.asyncio
    async def test_validate_secret_accepts_known_rejection_and_rejects_bad_secret(self):
        with patch(
            "app.addons.tools.turnstile.verify.httpx.AsyncClient",
            return_value=_client({"success": False, "error-codes": ["invalid-input-response"]}),
        ):
            await validate_secret("real-secret")
        with patch(
            "app.addons.tools.turnstile.verify.httpx.AsyncClient",
            return_value=_client({"success": False, "error-codes": ["invalid-input-secret"]}),
        ):
            with pytest.raises(ValidationError, match="rejected"):
                await validate_secret("bad-secret")
