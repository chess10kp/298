"""Standalone login HTML (no Jinja)."""

from __future__ import annotations

import html
import json

import app.config as app_config


def render_login_page(
    *,
    user: object | None,
    next_url: str,
) -> str:
    """Full HTML document for ``GET /login``."""
    next_json = json.dumps(next_url)
    cfg = app_config
    nu = html.escape(next_url)

    if user is not None:
        email = html.escape(getattr(user, "email", ""))
        role = html.escape(getattr(user.role, "value", str(getattr(user, "role", ""))))
        rv = getattr(user.role, "value", "")
        extra_nav = ""
        if rv == "admin":
            extra_nav = """
          <a class="login-shortcuts__link" href="/admin/dashboard">Admin</a>"""
        elif rv == "driver":
            extra_nav = """
          <a class="login-shortcuts__link" href="/driver">Driver</a>"""
        elif rv == "rider":
            extra_nav = """
          <a class="login-shortcuts__link" href="/">Rider hub</a>"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Account — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="ds-body">
  <div class="login-canvas">
    <div class="login-canvas__panel">
      <p class="label-md" style="margin: 0 0 var(--space-2);">Session</p>
      <h1 class="display-lg" style="font-size: 2rem;">Signed in</h1>
      <p class="body-md" style="margin: var(--space-3) 0;">Cookie is active. You can continue without signing in again.</p>
      <p class="headline-md" style="font-size: 1rem; font-weight: 600;">{email}</p>
      <p class="body-sm" style="margin: var(--space-1) 0 var(--space-3);">Role: {role}</p>
      <div class="stack-low login-shortcuts-wrap">
        <p class="body-sm login-shortcuts-wrap__label">Shortcuts</p>
        <nav class="login-shortcuts" aria-label="Application shortcuts">
          <a class="login-shortcuts__link" href="/">Dashboard</a>{extra_nav}
        </nav>
      </div>
      <button type="button" class="btn btn--ghost" id="logout-btn">Log out</button>
    </div>
    <script>
      document.getElementById('logout-btn').addEventListener('click', async () => {{
        await fetch('/api/v1/auth/logout', {{ method: 'POST', credentials: 'include' }});
        window.location.href = '/login';
      }});
    </script>
  </div>
</body>
</html>
"""

    # Signed-out: inject role shortcuts via minimal duplication from template
    hints = ""
    fill_scripts = ""
    if cfg.SHOW_DEFAULT_ACCOUNT_HINTS:
        re = html.escape(cfg.DEFAULT_RIDER_EMAIL)
        rp = html.escape(cfg.DEFAULT_RIDER_PASSWORD)
        ae = html.escape(cfg.DEFAULT_ADMIN_EMAIL)
        ap = html.escape(cfg.DEFAULT_ADMIN_PASSWORD)
        de = html.escape(cfg.DEFAULT_DRIVER_EMAIL)
        dp = html.escape(cfg.DEFAULT_DRIVER_PASSWORD)
        re_j = json.dumps(cfg.DEFAULT_RIDER_EMAIL)
        rp_j = json.dumps(cfg.DEFAULT_RIDER_PASSWORD)
        ae_j = json.dumps(cfg.DEFAULT_ADMIN_EMAIL)
        ap_j = json.dumps(cfg.DEFAULT_ADMIN_PASSWORD)
        de_j = json.dumps(cfg.DEFAULT_DRIVER_EMAIL)
        dp_j = json.dumps(cfg.DEFAULT_DRIVER_PASSWORD)
        hints = f"""
      <section class="defaults-block" aria-label="Default database accounts">
        <h2>Default accounts</h2>
        <ul>
          <li>
            <strong>Rider</strong> — <code>{re}</code> / <code>{rp}</code>
            <div class="tool-controls" style="margin-top: var(--space-2);">
              <button type="button" class="btn btn--ghost" id="fill-rider">Fill rider</button>
              <a href="/login?next=/" class="btn btn--ghost">Rider redirect</a>
            </div>
          </li>
          <li>
            <strong>Admin</strong> — <code>{ae}</code> / <code>{ap}</code>
            <div class="tool-controls" style="margin-top: var(--space-2);">
              <button type="button" class="btn btn--ghost" id="fill-admin">Fill admin</button>
              <a href="/login?next=/admin/dashboard" class="btn btn--ghost">Admin redirect</a>
            </div>
          </li>
          <li>
            <strong>Driver</strong> — <code>{de}</code> / <code>{dp}</code>
            <div class="tool-controls" style="margin-top: var(--space-2);">
              <button type="button" class="btn btn--ghost" id="fill-driver">Fill driver</button>
              <a href="/login?next=/driver" class="btn btn--ghost">Driver redirect</a>
            </div>
          </li>
        </ul>
      </section>
"""
        fill_scripts = f"""
        document.getElementById('fill-rider').addEventListener('click', () => {{
          document.getElementById('field-email').value = {re_j};
          document.getElementById('field-password').value = {rp_j};
        }});
        document.getElementById('fill-admin').addEventListener('click', () => {{
          document.getElementById('field-email').value = {ae_j};
          document.getElementById('field-password').value = {ap_j};
        }});
        document.getElementById('fill-driver').addEventListener('click', () => {{
          document.getElementById('field-email').value = {de_j};
          document.getElementById('field-password').value = {dp_j};
        }});
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign in — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="ds-body">
  <div class="login-canvas">
    <div class="login-canvas__panel">
      <h1 class="display-lg" style="font-size: 2.25rem;">Sign in</h1>
      <form id="login-form">
        <div class="field">
          <label for="field-email">Email</label>
          <input name="email" id="field-email" type="email" autocomplete="username" required>
        </div>
        <div class="field">
          <label for="field-password">Password</label>
          <input name="password" id="field-password" type="password" autocomplete="current-password" required>
        </div>
        <button type="submit" class="btn btn--primary" style="margin-top: var(--space-4); width: 100%;">Sign in</button>
      </form>
{hints}
    </div>
    <script>
      (function () {{
        const nextUrl = {next_json};
        document.getElementById('login-form').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const body = {{ email: fd.get('email'), password: fd.get('password') }};
          const r = await fetch('/api/v1/auth/session', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            credentials: 'include',
            body: JSON.stringify(body),
          }});
          if (r.ok) {{
            const data = await r.json();
            window.location.href = data.redirect || nextUrl;
          }} else {{
            alert('Login failed');
          }}
        }});
{fill_scripts}
      }})();
    </script>
  </div>
</body>
</html>
"""
