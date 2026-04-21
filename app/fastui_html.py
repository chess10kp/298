"""FastUI HTML shell with Tailwind CSS for ``class_name`` / ``className`` utilities.

Upstream :func:`fastui.prebuilt_html` does not allow extra ``<link>`` or ``<script>`` tags.
This module duplicates that template and injects the Tailwind Play CDN so components can use
Tailwind classes (see components' ``class_name`` field, serialized as ``className`` in JSON).

Keep ``_FASTUI_PREBUILT_VERSION`` in sync with ``fastui``'s internal prebuilt bundle
(``fastui.__init__`` → ``_PREBUILT_VERSION``).
"""

from __future__ import annotations

import typing as _t

# Sync with installed fastui package (site-packages/fastui/__init__.py).
_FASTUI_PREBUILT_VERSION = "0.0.26"
_PREBUILT_CDN_URL = (
    f"https://cdn.jsdelivr.net/npm/@pydantic/fastui-prebuilt@{_FASTUI_PREBUILT_VERSION}/dist/assets"
)

_TAILWIND_PLAY = "https://cdn.tailwindcss.com"


def fruger_prebuilt_html(
    *,
    title: str = "",
    api_root_url: str | None = "/api",
    api_path_mode: _t.Literal["append", "query"] | None = None,
    api_path_strip: str | None = None,
) -> str:
    """
    Same contract as :func:`fastui.prebuilt_html`, plus Tailwind Play CDN in ``<head>``.

    Use Tailwind utility strings on FastUI components (default page shell is full viewport width).

    ``api_root_url`` defaults to ``/api`` so the client always fetches FastUI JSON from ``/api/...``,
    even when the shell is opened at ``/api`` (avoids broken ``/api/api/`` requests).
    Pass ``None`` to omit the meta tag (upstream FastUI behavior).
    """
    meta_extra = []
    if api_root_url is not None:
        meta_extra.append(f'<meta name="fastui:APIRootUrl" content="{api_root_url}" />')
    if api_path_mode is not None:
        meta_extra.append(f'<meta name="fastui:APIPathMode" content="{api_path_mode}" />')
    if api_path_strip is not None:
        meta_extra.append(f'<meta name="fastui:APIPathStrip" content="{api_path_strip}" />')
    meta_extra_str = "\n    ".join(meta_extra)

    # Tailwind after FastUI CSS so utilities can override defaults when needed.
    # Tokens align with app/static/theme.css (DESIGN.md — Architectural Monolith).
    tailwind_boot = f"""\
    <script src="{_TAILWIND_PLAY}"></script>
    <script>
      tailwind.config = {{
        theme: {{
          extend: {{
            fontFamily: {{
              sans: ['Inter', 'Plus Jakarta Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
              display: ['Plus Jakarta Sans', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
            }},
            boxShadow: {{
              'fruger-float': '0 24px 64px rgba(26, 28, 28, 0.04)',
            }},
            colors: {{
              fruger: {{
                DEFAULT: '#000000',
                surface: '#f9f9f9',
                surfaceLow: '#f3f3f4',
                panel: '#ffffff',
                container: '#eeeeee',
                muted: '#4c4546',
                on: '#1a1c1c',
                accent: '#0054cb',
                dark: '#1b1b1b',
              }},
            }},
          }},
        }},
      }};
    </script>"""

    return f"""\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet" />
    <script type="module" crossorigin src="{_PREBUILT_CDN_URL}/index.js"></script>
    <link rel="stylesheet" crossorigin href="{_PREBUILT_CDN_URL}/index.css">
{tailwind_boot}
    <link rel="stylesheet" href="/static/theme.css" />
    {meta_extra_str}
  </head>
  <body class="ds-body">
    <div id="root"></div>
    <script>
      // Dismissible onboarding banner persistence (localStorage)
      (function () {{
        try {{
          const dismissed = localStorage.getItem('fruger_onboarding_dismissed');
          if (dismissed === '1') {{
            document.documentElement.classList.add('fruger-onboarding-dismissed');
          }}
          document.addEventListener('click', function (e) {{
            const tgt = e.target || e.srcElement;
            if (tgt && tgt.closest && tgt.closest('.fruger-onboarding-dismiss')) {{
              localStorage.setItem('fruger_onboarding_dismissed', '1');
              document.documentElement.classList.add('fruger-onboarding-dismissed');
            }}
          }}, {{capture: true}});
        }} catch (err) {{
          // ignore
        }}
      }})();
    </script>
  </body>
</html>
"""
