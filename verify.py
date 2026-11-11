"""Cloudflare Turnstile siteverify client."""

from __future__ import annotations

from typing import Any

import httpx

from app.addons.log import warning
from app.core.exceptions import ValidationError

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
SCRIPT_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js"
_DUMMY_TOKEN = "dummy-invalid-token"


def _error_codes(body: dict[str, Any]) -> list[str]:
    codes = body.get("error-codes") or []
    if not isinstance(codes, list):
        return []
    return [str(code) for code in codes]


async def siteverify(secret: str, token: str, remote_ip: str | None) -> dict[str, Any]:
    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(SITEVERIFY_URL, data=data)
        response.raise_for_status()
        body = response.json()
    if not isinstance(body, dict):
        raise ValidationError(message="Bot challenge could not be verified")
    return body


async def validate_secret(secret: str) -> None:
    """Accept a secret that Cloudflare recognizes.

    A real secret rejects the dummy token with ``invalid-input-response``.
    A bad secret returns ``invalid-input-secret``. Test secrets that always
    pass return ``success: true``.
    """
    if not secret.strip():
        raise ValidationError(message="Turnstile secret key is required")
    try:
        body = await siteverify(secret, _DUMMY_TOKEN, None)
    except httpx.HTTPError as exc:
        warning("Turnstile", "Secret check could not reach Cloudflare")
        raise ValidationError(
            message="Could not reach Cloudflare Turnstile to verify the secret key"
        ) from exc
    if body.get("success") is True:
        return
    codes = _error_codes(body)
    if "invalid-input-secret" in codes:
        raise ValidationError(message="Turnstile secret key was rejected")
    if "invalid-input-response" in codes:
        return
    raise ValidationError(message="Turnstile secret key could not be verified")


async def verify_token(secret: str, token: str | None, remote_ip: str | None) -> None:
    if not token:
        raise ValidationError(message="Bot challenge is required")
    try:
        body = await siteverify(secret, token, remote_ip)
    except httpx.HTTPError as exc:
        warning("Turnstile", "siteverify request failed")
        raise ValidationError(message="Bot challenge could not be verified") from exc
    if body.get("success") is not True:
        raise ValidationError(message="Bot challenge failed")
