"""Cloudflare Turnstile bot-challenge tool addon."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.addons.config_serialization import dump_addon_config
from app.addons.log import info
from app.addons.tools.base import ToolAddon
from app.addons.tools.turnstile.config import TurnstileConfig
from app.addons.tools.turnstile.verify import SCRIPT_URL, validate_secret, verify_token

STOREFRONT_ACTIONS = ("register", "login", "forgot_password")
_ACTIONS = (*STOREFRONT_ACTIONS, "admin_login")


class TurnstileToolAddon(ToolAddon):
    """Verify Cloudflare Turnstile tokens on anonymous auth actions."""

    addon_id: str = "turnstile"
    addon_name: str = "Cloudflare Turnstile"
    addon_description: str = (
        "Require a Cloudflare Turnstile token on registration, login, "
        "password reset requests, and admin login."
    )
    addon_category: str = "tool"
    version: str = "1.0.0"
    log_label: str = "Turnstile"

    _config: dict[str, Any] | None = None
    _site_key: str = ""
    _secret_key: str = ""
    _ready: bool = False

    @classmethod
    def config_schema(cls) -> type[TurnstileConfig]:
        return TurnstileConfig

    def _apply(self, config: dict[str, Any]) -> None:
        validated = self.config_schema()(**config)
        stored = dump_addon_config(validated)
        self._config = stored
        self._site_key = str(stored.get("site_key") or "").strip()
        self._secret_key = str(stored.get("secret_key") or "")
        self._ready = bool(validated.is_active and self._site_key and self._secret_key)
        self.is_enabled = self._ready

    async def initialize(self, config: dict[str, Any]) -> None:
        self._apply(config)
        info("Turnstile", "Initialized (active={})", self._ready)

    async def validate_config(self, config: dict[str, Any]) -> None:
        validated = self.config_schema()(**config)
        await validate_secret(validated.secret_key.get_secret_value())

    async def shutdown(self) -> None:
        self._config = None
        self._site_key = ""
        self._secret_key = ""
        self._ready = False
        self.is_enabled = False

    def protects_challenge(self, action: str) -> bool:
        return self._ready and action in _ACTIONS

    def challenge_public_config(self) -> dict[str, Any] | None:
        if not self._ready:
            return None
        return {
            "site_key": self._site_key,
            "script_url": SCRIPT_URL,
            "actions": list(STOREFRONT_ACTIONS),
        }

    def admin_challenge_widget_html(self) -> str:
        if not self._ready:
            return ""
        site_key = html.escape(self._site_key, quote=True)
        return (
            f'<script src="{SCRIPT_URL}" async defer></script>'
            f'<div class="cf-turnstile" data-sitekey="{site_key}" '
            'data-callback="oshkeloshBotChallenge"></div>'
            "<script>function oshkeloshBotChallenge(token){"
            "var el=document.querySelector('input[name=bot_challenge]');"
            "if(el)el.value=token;}</script>"
        )

    async def verify_bot_challenge(
        self,
        token: str | None,
        remote_ip: str | None,
        action: str,
    ) -> None:
        if not self.protects_challenge(action):
            return
        await verify_token(self._secret_key, token, remote_ip)

    def get_admin_routes(self) -> list[APIRouter]:
        from app.addons.tools.turnstile.routes import admin_router

        return [admin_router]

    def get_admin_templates(self) -> str:
        return str(Path(__file__).resolve().parent / "templates")
