"""Standalone login HTML (no Jinja)."""

from __future__ import annotations

import html
import json
from urllib.parse import urlencode

import app.config as app_config


def render_landing_page() -> str:
    """Full HTML document for the public landing page at ``/``."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fruger — Ridesharing, reimagined</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="ds-body">
  <header class="landing-header">
    <div class="landing-header__inner">
      <a class="masthead__brand" href="/">Fruger</a>
      <nav class="landing-header__nav" style="display: flex; gap: 0.75rem; align-items: center;">
        <a class="btn btn--ghost" href="/login">Sign in</a>
        <a class="btn btn--primary" href="/register">Register</a>
      </nav>
    </div>
  </header>

  <main class="landing-main">
    <section class="landing-hero">
      <p class="label-md landing-hero__eyebrow">Ridesharing, reimagined</p>
      <h1 class="landing-hero__title">Your ride,<br>your price.</h1>
      <p class="landing-hero__lede">
        Fruger is a bidding-based ridesharing platform. Drivers compete for your trip
        with real-time bids — so you always get a fair fare. No surge pricing, no black boxes.
      </p>
      <div class="landing-hero__actions">
        <a class="btn btn--primary btn--lg" href="/register">Get started</a>
        <a class="btn btn--ghost btn--lg" href="#how-it-works">See how it works</a>
      </div>
    </section>

    <section class="landing-section" id="how-it-works">
      <p class="label-md section-label">How it works</p>
      <div class="grid-cards">
        <div class="card-editorial">
          <p class="card-editorial__title">1. Request a ride</p>
          <p class="card-editorial__text">
            Enter your pickup and dropoff locations. Your request goes live to
            nearby drivers instantly.
          </p>
        </div>
        <div class="card-editorial">
          <p class="card-editorial__title">2. Drivers bid</p>
          <p class="card-editorial__text">
            Multiple drivers see your request and submit bids with their own fare,
            ETA, and distance. Competition keeps prices honest.
          </p>
        </div>
        <div class="card-editorial">
          <p class="card-editorial__title">3. You choose</p>
          <p class="card-editorial__text">
            Compare bids side-by-side and accept the one that works best for you.
            Your driver is confirmed instantly.
          </p>
        </div>
      </div>
    </section>

    <section class="landing-section">
      <p class="label-md section-label">Why Fruger?</p>
      <div class="grid-cards">
        <div class="card-editorial">
          <p class="card-editorial__title">Transparent pricing</p>
          <p class="card-editorial__text">
            No opaque algorithms. You see every bid and pick the fare you're
            comfortable with.
          </p>
        </div>
        <div class="card-editorial">
          <p class="card-editorial__title">Driver autonomy</p>
          <p class="card-editorial__text">
            Drivers set their own rates. Earn what you deserve — no more
            platform-dictated pay cuts.
          </p>
        </div>
        <div class="card-editorial">
          <p class="card-editorial__title">Real-time matching</p>
          <p class="card-editorial__text">
            Bids arrive in seconds. No waiting around. Unaccepted bids expire
            automatically after 10 minutes.
          </p>
        </div>
      </div>
    </section>

    <section class="landing-cta">
      <h2 class="landing-cta__title">Ready to ride?</h2>
      <p class="body-md" style="margin-bottom: var(--space-4);">
        Sign up as a rider or driver and experience ridesharing the way it should be.
      </p>
      <div style="display: flex; gap: var(--space-3); flex-wrap: wrap; justify-content: center;">
        <a class="btn btn--primary btn--lg" href="/register">Create account</a>
        <a class="btn btn--ghost btn--lg" href="/login">Sign in</a>
      </div>
    </section>
  </main>

  <footer class="landing-footer">
    <p class="body-sm">&copy; 2026 Fruger. Built with real NYC TLC data.</p>
  </footer>
</body>
</html>
"""


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
        # Default shortcut shown for non-riders. Riders get a role-specific "Rider hub" link
        # and don't need the generic "Dashboard" label which can be confusing.
        if rv == "admin":
            extra_nav = """
          <a class="login-shortcuts__link" href="/admin/dashboard">Admin</a>"""
            main_shortcut = '<a class="login-shortcuts__link" href="/">Dashboard</a>'
        elif rv == "driver":
            extra_nav = """
          <a class="login-shortcuts__link" href="/driver">Driver</a>"""
            main_shortcut = '<a class="login-shortcuts__link" href="/">Dashboard</a>'
        elif rv == "rider":
            extra_nav = """
          <a class="login-shortcuts__link" href="/">Rider hub</a>"""
            # Hide the generic Dashboard link for riders to avoid confusion
            main_shortcut = ""
        else:
            main_shortcut = '<a class="login-shortcuts__link" href="/">Dashboard</a>'
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
          {main_shortcut}{extra_nav}
        </nav>
      </div>
      <button type="button" class="btn btn--ghost" id="logout-btn">Log out</button>
    </div>
    <script>
      document.getElementById('logout-btn').addEventListener('click', async () => {{
        await fetch('/api/v1/auth/logout', {{ method: 'POST', credentials: 'include' }});
        window.location.href = '/';
      }});
    </script>
  </div>
</body>
</html>
"""

    # Signed-out: inject role shortcuts via minimal duplication from template
    # Remove default-account hint UI (avoid exposing seeded credentials in the login page)
    hints = ""
    fill_scripts = ""
    register_href = html.escape("/register?" + urlencode({"next": next_url}))

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
      <p class="body-sm" style="margin-top: var(--space-3); text-align: center;">
        New here?
        <a href="{register_href}">Create an account</a>
      </p>
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


def render_register_page(
    *,
    user: object | None,
    next_url: str,
) -> str:
    """Full HTML document for ``GET /register``."""
    if user is not None:
        return render_login_page(user=user, next_url=next_url)

    next_json = json.dumps(next_url)
    login_href = html.escape("/login?" + urlencode({"next": next_url}))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Create account — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="ds-body">
  <div class="login-canvas">
    <div class="login-canvas__panel">
      <h1 class="display-lg" style="font-size: 2.25rem;">Create account</h1>
      <p class="body-sm muted" style="margin: 0 0 var(--space-3);">Rider or driver — admins are invited separately.</p>
      <form id="register-form">
        <div class="field">
          <label for="reg-email">Email</label>
          <input name="email" id="reg-email" type="email" autocomplete="email" required>
        </div>
        <div class="field">
          <label for="reg-password">Password</label>
          <input name="password" id="reg-password" type="password" autocomplete="new-password" minlength="8" required>
        </div>
        <div class="field">
          <label for="reg-password2">Confirm password</label>
          <input name="password2" id="reg-password2" type="password" autocomplete="new-password" minlength="8" required>
        </div>
        <div class="field">
          <label for="reg-role">Account type</label>
          <select name="role" id="reg-role" required>
            <option value="rider" selected>Rider</option>
            <option value="driver">Driver</option>
          </select>
        </div>
        <button type="submit" class="btn btn--primary" style="margin-top: var(--space-4); width: 100%;">Create account</button>
      </form>
      <p class="body-sm" style="margin-top: var(--space-3); text-align: center;">
        Already have an account?
        <a href="{login_href}">Sign in</a>
      </p>
    </div>
    <script>
      (function () {{
        const nextUrl = {next_json};
        function parseDetail(res, data) {{
          if (data && typeof data.detail === 'string') return data.detail;
          if (Array.isArray(data && data.detail)) {{
            try {{ return data.detail.map(function (d) {{ return d.msg || JSON.stringify(d); }}).join(' '); }} catch (e) {{}}
          }}
          return res.statusText || 'Request failed';
        }}
        document.getElementById('register-form').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const fd = new FormData(e.target);
          const password = String(fd.get('password') || '');
          const password2 = String(fd.get('password2') || '');
          if (password !== password2) {{
            alert('Passwords do not match.');
            return;
          }}
          const regBody = {{
            email: String(fd.get('email') || '').trim(),
            password: password,
            role: String(fd.get('role') || 'rider'),
          }};
          const reg = await fetch('/api/v1/auth/register', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            credentials: 'include',
            body: JSON.stringify(regBody),
          }});
          let regData = null;
          try {{ regData = await reg.json(); }} catch (err) {{}}
          if (!reg.ok) {{
            alert(parseDetail(reg, regData));
            return;
          }}
          const sess = await fetch('/api/v1/auth/session', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            credentials: 'include',
            body: JSON.stringify({{ email: regBody.email, password: regBody.password }}),
          }});
          let sessData = null;
          try {{ sessData = await sess.json(); }} catch (err2) {{}}
          if (!sess.ok) {{
            alert('Account created, but sign-in failed: ' + parseDetail(sess, sessData));
            window.location.href = '/login?' + new URLSearchParams({{ next: nextUrl }}).toString();
            return;
          }}
          window.location.href = (sessData && sessData.redirect) || nextUrl;
        }});
      }})();
    </script>
  </div>
</body>
</html>
"""
