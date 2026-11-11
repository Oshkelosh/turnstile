"""Pydantic configuration for the Turnstile tool addon."""

from __future__ import annotations

from pydantic import Field, SecretStr

from app.addons.base import AddonConfig


class TurnstileConfig(AddonConfig):
    is_active: bool = True
    site_key: str = Field(default="", max_length=256)
    secret_key: SecretStr = Field(default=SecretStr(""), max_length=256)
