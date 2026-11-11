# Cloudflare Turnstile (`turnstile`) — AGENTS

## Role

Installable bot-challenge tool. Verifies Cloudflare Turnstile tokens for anonymous auth actions the host already calls. Addon ID: `turnstile`.

## File map

- `README.md`
- `__init__.py`
- `addon.py`
- `config.py`
- `verify.py`
- `routes.py`
- `templates/`
- `tests/`
- `oshkelosh-addon.json`

## Package specifics

**Category ceiling:** Many tools may be active. The host uses the first tool that protects a given action.
**Config fields:** `is_active` (bool), `site_key` (string), `secret_key` (secret)
- Dual enable: addon enabled in Admin → Addons **and** config `is_active`, with both keys set

## Invariants

- Implement the matching category ABC; do not patch host `app/services/*.py` with provider branches
- Credentials and enable flags live in `addon_configs` (admin UI), not host `.env`
- Use `app/addons/log.py` for structured logging
- Admin mutating forms need CSRF; use `render_addon_admin_page` correctly (do not pass `flash` via `**_common_ctx`)
- Nested `.git` (if present): this package is its own repo; the host gitignores this directory

## Prefer / Avoid

- Prefer: siteverify and widget markup stay in this package
- Avoid: editing host `app/services/` for Turnstile; putting secrets in host `.env`

## See also

- [README.md](README.md) — package how-to
- [../../AGENTS.md](../../AGENTS.md) — host addon boundary
- [../../README.md](../../README.md) — plugin development
- [../../../../AGENTS.md](../../../../AGENTS.md), [../../../../DESIGN.md](../../../../DESIGN.md)
