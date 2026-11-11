# Cloudflare Turnstile (`turnstile`)

Installable tool that requires a Cloudflare Turnstile token on anonymous auth.

| | |
|---|---|
| Addon ID | `turnstile` |
| Category | tool |
| Version | 1.0.0 |

This package is not a host built-in. Install it with **Admin → Addons** (ZIP or URL), or clone it into `app/addons/tools/turnstile/` for local development. Restart the app after install so discovery picks it up.

## Enable and configure

1. Create a Turnstile widget in the Cloudflare dashboard and copy the site key and secret key.
2. Open **Admin → Tools → Cloudflare Turnstile** at `/admin/tools/turnstile`.
3. Enable the addon, leave **Active** checked, and save both keys.

The challenge runs only when the addon is enabled, **Active** is on, and both keys are set. Rate limits stay in place.

Protected actions:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/forgot-password`
- `POST /admin/login`

Storefront clients read `auth.challenge` from `GET /api/v1/storefront/config` and send the token as the `X-Bot-Challenge` header. Admin login renders the widget and posts `bot_challenge`.

A missing token, a failed check, or a Cloudflare outage is rejected. Tokens are single-use.

## Configuration schema

| Field | Type | Description |
|-------|------|-------------|
| `is_active` | bool | Master toggle. Both keys must also be set. |
| `site_key` | string | Public widget site key |
| `secret_key` | secret | Siteverify secret |

Cloudflare dummy keys for local checks: site `1x00000000000000000000AA` (always pass), site `2x00000000000000000000AB` (always block), secret `1x0000000000000000000000000000000AA` (always pass).

## Storefront

When active, `auth.challenge` is:

```json
{
  "site_key": "...",
  "script_url": "https://challenges.cloudflare.com/turnstile/v0/api.js",
  "actions": ["register", "login", "forgot_password"]
}
```

See the frontend addon guide for the header contract.
