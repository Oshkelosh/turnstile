"""Turnstile tool addon admin routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.addons.admin_helpers import (
    make_addon_jinja_env,
    render_addon_admin_page,
    require_addon_csrf,
    save_addon_from_form,
)
from app.addons.registry import addon_registry
from app.admin.routes import require_admin_session

_CONFIGURE_URL = "/admin/tools/turnstile"
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

jinja_env = make_addon_jinja_env(_TEMPLATES_DIR)
admin_router = APIRouter()


def _current_config() -> dict[str, Any]:
    return dict(addon_registry.get_config("turnstile") or {})


def _page(
    request: Request,
    *,
    flash: str | None = None,
    flash_type: str = "info",
) -> HTMLResponse:
    return HTMLResponse(
        content=render_addon_admin_page(
            jinja_env,
            request,
            "turnstile_settings.html",
            "Cloudflare Turnstile",
            flash=flash,
            flash_type=flash_type,
            addon=addon_registry.get("turnstile"),
            config=_current_config(),
        )
    )


@admin_router.get("")
async def turnstile_settings_page(
    request: Request,
    db: Any = Depends(require_admin_session),
) -> HTMLResponse:
    return _page(request)


@admin_router.get("/", include_in_schema=False)
async def turnstile_trailing_slash_redirect() -> RedirectResponse:
    return RedirectResponse(url=_CONFIGURE_URL, status_code=307)


@admin_router.post("/settings", response_model=None)
async def turnstile_save_settings(
    request: Request,
    csrf_token: str = Form(""),
    is_enabled: str = Form(""),
    is_active: str = Form(""),
    site_key: str = Form(""),
    secret_key: str = Form(""),
    db: Any = Depends(require_admin_session),
) -> HTMLResponse | RedirectResponse:
    require_addon_csrf(request, csrf_token)
    try:
        return await save_addon_from_form(
            db,
            "turnstile",
            {
                "is_active": is_active == "on",
                "site_key": site_key.strip(),
                "secret_key": secret_key,
            },
            enabled=is_enabled == "on",
            redirect_url=_CONFIGURE_URL,
            flash_message="Turnstile settings saved",
        )
    except Exception as exc:
        return _page(request, flash=f"Error saving settings: {exc}", flash_type="error")
