"""Minimal full-page HTML for map/tool UIs embedded in iframes (no Jinja)."""

from __future__ import annotations

import html

import app.config as app_config


def _maps_js_src(api_key: str, callback: str) -> str:
    """Loader URL for https://developers.google.com/maps/documentation/javascript/load-maps-js-api"""
    k = html.escape(api_key, quote=True)
    cb = html.escape(callback, quote=True)
    return (
        f"https://maps.googleapis.com/maps/api/js?key={k}&callback={cb}&loading=async"
    )


def _maps_places_js_src(api_key: str, callback: str) -> str:
    """Maps JS + Places library (Places Autocomplete)."""
    k = html.escape(api_key, quote=True)
    cb = html.escape(callback, quote=True)
    return f"https://maps.googleapis.com/maps/api/js?key={k}&libraries=places&callback={cb}&loading=async"


# Standalone / iframe document: no FastUI shell, so mirror the main app navbar here.
_EMBED_DRIVER_NAV_HTML = """
  <header class="embed-navbar" role="navigation" aria-label="Fruger">
    <div class="embed-navbar__inner">
      <a class="embed-navbar__brand" href="/" target="_top">Fruger</a>
      <nav class="embed-navbar__links" aria-label="Account">
        <a class="embed-navbar__link" href="/driver" target="_top">Dashboard</a>
        <button type="button" class="embed-navbar__link embed-navbar__btn" id="embed-nav-logout">Log out</button>
      </nav>
    </div>
  </header>
  <script>
    (function () {
      if (window.self !== window.top) {
        document.documentElement.classList.add('driver-embed--framed');
      }
      var b = document.getElementById('embed-nav-logout');
      if (!b) return;
      b.addEventListener('click', function () {
        fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' }).finally(function () {
          window.top.location.href = '/login';
        });
      });
    })();
  </script>
"""


def driver_hub_document_html() -> str:
    """Full HTML document for the driver hub (same markup as ``GET /embed/driver``)."""
    k = (app_config.GOOGLE_MAPS_API_KEY or "").strip()
    return driver_embed(k) if k else driver_embed_no_key()


def driver_embed(maps_key: str) -> str:
    src = _maps_js_src(maps_key, "window.initDriverMap")
    return f"""<!DOCTYPE html>
<html lang="en" class="driver-embed">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Driver — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css?v=8">
</head>
<body class="tool-page driver-layout">
{_EMBED_DRIVER_NAV_HTML}
  <p class="label-md" style="margin: 0 0 var(--space-2);">Partner</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Driver hub</h1>
  <p class="muted">Session-backed location updates. Browse available rides and place bids.</p>

  <div class="tool-controls" style="margin-bottom: var(--space-3);">
    <button id="btn-seed-demo" type="button" class="btn btn--secondary" title="Inserts demo riders and open rides (dev)">Seed demo data</button>
    <label>Ride ID <input id="ride-id" type="number" min="1" style="width:6rem"></label>
    <button id="btn-start" type="button" class="btn btn--ghost">Start ride</button>
    <button id="btn-done" type="button" class="btn btn--secondary">Complete ride</button>
  </div>

  <h2>Available rides</h2>
  <div class="rides-panel">
    <div id="rides-out">Loading…</div>
  </div>
  <script src="/static/driver.js?v=5"></script>
  <script async defer src="{src}"></script>
</body>
</html>
"""


def driver_embed_no_key() -> str:
    return (
        """<!DOCTYPE html>
<html lang="en" class="driver-embed">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Driver — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css?v=8">
</head>
<body class="tool-page driver-layout">
"""
        + _EMBED_DRIVER_NAV_HTML
        + """
  <p class="label-md" style="margin: 0 0 var(--space-2);">Partner</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Driver hub</h1>
  <p class="muted">Session-backed location updates. Browse available rides and place bids.</p>

  <div class="tool-controls" style="margin-bottom: var(--space-3);">
    <button id="btn-seed-demo" type="button" class="btn btn--secondary" title="Inserts demo riders and open rides (dev)">Seed demo data</button>
    <label>Ride ID <input id="ride-id" type="number" min="1" style="width:6rem"></label>
    <button id="btn-start" type="button" class="btn btn--ghost">Start ride</button>
    <button id="btn-done" type="button" class="btn btn--secondary">Complete ride</button>
  </div>

  <h2>Available rides</h2>
  <div class="rides-panel">
    <div id="rides-out">Loading…</div>
  </div>
  <script src="/static/driver.js?v=5"></script>
  <script>window.initDriverMap = function () { console.warn('No maps key'); };</script>
</body>
</html>
"""
    )


def admin_map_embed(maps_key: str) -> str:
    src = _maps_js_src(maps_key, "window.initAdminMap")
    return f"""<!DOCTYPE html>
<html lang="en" class="admin-map-embed-root">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fleet map — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page admin-map-embed">
  <div class="admin-map-embed__chrome">
    <p class="label-md" style="margin: 0 0 var(--space-2);">Fleet</p>
    <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Partner map</h1>
    <p><a href="/admin/dashboard">Admin console</a></p>
  </div>
  <div id="admin-map" class="tool-map admin-map-embed__map"></div>
  <script src="/static/admin_map.js"></script>
  <script async defer src="{src}"></script>
</body>
</html>
"""


def admin_map_embed_no_key() -> str:
    return """<!DOCTYPE html>
<html lang="en" class="admin-map-embed-root">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fleet map — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page admin-map-embed">
  <div class="admin-map-embed__chrome">
    <p class="label-md" style="margin: 0 0 var(--space-2);">Fleet</p>
    <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Partner map</h1>
    <p class="warn">Set <code>GOOGLE_MAPS_API_KEY</code> for the map.</p>
    <p><a href="/admin/dashboard">Admin console</a></p>
  </div>
  <div id="admin-map" class="tool-map admin-map-embed__map"></div>
  <script src="/static/admin_map.js"></script>
  <script>window.initAdminMap = function () { console.warn('No maps key'); };</script>
</body>
</html>
"""


def rider_hub_actions_embed(maps_key: str) -> str:
    """Rider tools with Google Places search for pickup/drop-off (requires API key + Places enabled)."""
    src = _maps_places_js_src(maps_key, "window.initRiderHubPlaces")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rider actions — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
  <style>
    #rider-hub-msg.ok {{ color: #047857; }}
    #rider-hub-msg.err {{ color: #b91c1c; }}
    .rider-hub-grid {{ display: grid; gap: var(--space-3); width: 100%; max-width: none; }}
    .pac-container {{ z-index: 10000; }}
    .rider-waiting {{
      margin-top: var(--space-3);
      padding: var(--space-4);
      border-radius: 12px;
      background: linear-gradient(145deg, rgba(0, 84, 203, 0.07), rgba(26, 28, 28, 0.04));
      border: 1px solid var(--outline-variant);
      animation: rider-waiting-breathe 2.5s ease-in-out infinite;
    }}
    @keyframes rider-waiting-breathe {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.88; }}
    }}
    .rider-waiting__row {{ display: flex; gap: var(--space-4); align-items: flex-start; }}
    .rider-waiting__spinner {{
      width: 42px; height: 42px; border-radius: 50%;
      border: 3px solid rgba(0, 84, 203, 0.2);
      border-top-color: #0054cb;
      animation: rider-spin 0.8s linear infinite;
      flex-shrink: 0;
    }}
    @keyframes rider-spin {{ to {{ transform: rotate(360deg); }} }}
    .rider-inline-bids {{ margin-top: var(--space-4); }}
    .rider-inline-bids h3 {{ margin: 0 0 var(--space-2); }}
  </style>
</head>
<body class="tool-page" style="padding-bottom: var(--space-4);">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Rider</p>
  <h2 class="headline-md" style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 var(--space-2);">
    Request &amp; manage rides
  </h2>
  <p class="muted" style="margin: 0 0 var(--space-3);">Uses your signed-in session. Search addresses, then request the ride.</p>

  <form id="create-ride-form" class="rider-hub-grid">
    <fieldset style="border: 1px solid var(--border-subtle, #e5e5e5); border-radius: 8px; padding: var(--space-3); margin: 0;">
      <legend class="body-sm" style="font-weight: 600; padding: 0 0.25rem;">New ride</legend>
      <p class="body-sm muted" style="margin: 0 0 var(--space-2);">Pick a place from the suggestions for each stop.</p>
      <div class="rider-hub-grid">
        <div class="field" style="margin: 0;">
          <label for="pickup_search">Pickup location</label>
          <input id="pickup_search" type="text" placeholder="Search for a pickup address" autocomplete="off" />
          <input type="hidden" id="pickup_lat" name="pickup_lat" value="" />
          <input type="hidden" id="pickup_lng" name="pickup_lng" value="" />
        </div>
        <div class="field" style="margin: 0;">
          <label for="dropoff_search">Drop-off location</label>
          <input id="dropoff_search" type="text" placeholder="Search for a drop-off address" autocomplete="off" />
          <input type="hidden" id="dropoff_lat" name="dropoff_lat" value="" />
          <input type="hidden" id="dropoff_lng" name="dropoff_lng" value="" />
        </div>
      </div>
      <div id="rider-hub-map" class="tool-map" style="height: 280px; margin-top: 0;"></div>
      <button type="submit" class="btn btn--primary" style="margin-top: var(--space-3);">Request ride</button>
    </fieldset>
  </form>

  <!-- Replaced free-form cancel by ride ID with a per-ride cancel button list -->
  <section id="my-rides" style="margin-top: var(--space-3);">
    <h3 class="body-sm" style="margin: 0 0 var(--space-2); font-weight: 600;">Your rides</h3>
    <div id="my-rides-root">Loading…</div>
  </section>

  <div class="tool-controls" style="margin-top: var(--space-3);">
    <button type="button" id="rider-hub-logout" class="btn btn--ghost">Log out</button>
  </div>

  <p id="rider-hub-msg" class="body-sm" style="margin-top: var(--space-2); min-height: 1.25rem;" aria-live="polite"></p>

  <section id="rider-waiting-panel" class="rider-waiting" hidden aria-live="polite">
    <div class="rider-waiting__row">
      <div class="rider-waiting__spinner" aria-hidden="true"></div>
      <div>
        <p class="body-md" style="font-weight: 700; margin: 0;">Waiting for drivers</p>
        <p class="body-sm muted" style="margin: 0.35rem 0 0;">
          Your ride is open for bids. Offers will appear below as drivers respond.
        </p>
        <p class="body-sm muted" style="margin: 0.35rem 0 0;">Ride #<span id="rider-waiting-id"></span></p>
      </div>
    </div>
  </section>

  <section id="rider-inline-bids" class="rider-inline-bids" hidden>
    <h3 class="headline-md" style="font-size: 1.1rem;">Driver offers</h3>
    <div id="rider-inline-bids-root"></div>
  </section>

  <script src="/static/rider_hub_actions.js"></script>
  <script async defer src="{src}"></script>
</body>
</html>
"""


def rider_hub_actions_embed_no_key() -> str:
    """Same as :func:`rider_hub_actions_embed` but raw lat/lng (no ``GOOGLE_MAPS_API_KEY``)."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rider actions — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
  <style>
    #rider-hub-msg.ok { color: #047857; }
    #rider-hub-msg.err { color: #b91c1c; }
    .rider-hub-grid { display: grid; gap: var(--space-3); width: 100%; max-width: none; }
    @media (min-width: 640px) {
      .rider-hub-grid--coords { grid-template-columns: 1fr 1fr; }
    }
    .rider-waiting {
      margin-top: var(--space-3);
      padding: var(--space-4);
      border-radius: 12px;
      background: linear-gradient(145deg, rgba(0, 84, 203, 0.07), rgba(26, 28, 28, 0.04));
      border: 1px solid var(--outline-variant);
      animation: rider-waiting-breathe 2.5s ease-in-out infinite;
    }
    @keyframes rider-waiting-breathe {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.88; }
    }
    .rider-waiting__row { display: flex; gap: var(--space-4); align-items: flex-start; }
    .rider-waiting__spinner {
      width: 42px; height: 42px; border-radius: 50%;
      border: 3px solid rgba(0, 84, 203, 0.2);
      border-top-color: #0054cb;
      animation: rider-spin 0.8s linear infinite;
      flex-shrink: 0;
    }
    @keyframes rider-spin { to { transform: rotate(360deg); } }
    .rider-inline-bids { margin-top: var(--space-4); }
    .rider-inline-bids h3 { margin: 0 0 var(--space-2); }
  </style>
</head>
<body class="tool-page" style="padding-bottom: var(--space-4);">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Rider</p>
  <h2 class="headline-md" style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 var(--space-2);">
    Request &amp; manage rides
  </h2>
  <p class="muted" style="margin: 0 0 var(--space-3);">Uses your signed-in session.</p>
  <p class="warn" style="margin: 0 0 var(--space-2);">Set <code>GOOGLE_MAPS_API_KEY</code> for address search. Until then, enter coordinates (decimal degrees).</p>

  <form id="create-ride-form" class="rider-hub-grid">
    <fieldset style="border: 1px solid var(--border-subtle, #e5e5e5); border-radius: 8px; padding: var(--space-3); margin: 0;">
      <legend class="body-sm" style="font-weight: 600; padding: 0 0.25rem;">New ride</legend>
      <p class="body-sm muted" style="margin: 0 0 var(--space-2);">Pickup and drop-off coordinates (decimal degrees).</p>
      <div class="rider-hub-grid rider-hub-grid--coords">
        <div class="field" style="margin: 0;">
          <label for="pickup_lat">Pickup latitude</label>
          <input id="pickup_lat" name="pickup_lat" type="number" step="any" required value="40.758">
        </div>
        <div class="field" style="margin: 0;">
          <label for="pickup_lng">Pickup longitude</label>
          <input id="pickup_lng" name="pickup_lng" type="number" step="any" required value="-73.9855">
        </div>
        <div class="field" style="margin: 0;">
          <label for="dropoff_lat">Drop-off latitude</label>
          <input id="dropoff_lat" name="dropoff_lat" type="number" step="any" required value="40.7484">
        </div>
        <div class="field" style="margin: 0;">
          <label for="dropoff_lng">Drop-off longitude</label>
          <input id="dropoff_lng" name="dropoff_lng" type="number" step="any" required value="-73.9857">
        </div>
      </div>
      <button type="submit" class="btn btn--primary" style="margin-top: var(--space-3);">Request ride</button>
    </fieldset>
  </form>

  <!-- Replaced free-form cancel by ride ID with a per-ride cancel button list -->
  <section id="my-rides" style="margin-top: var(--space-3);">
    <h3 class="body-sm" style="margin: 0 0 var(--space-2); font-weight: 600;">Your rides</h3>
    <div id="my-rides-root">Loading…</div>
  </section>

  <div class="tool-controls" style="margin-top: var(--space-3);">
    <button type="button" id="rider-hub-logout" class="btn btn--ghost">Log out</button>
  </div>

  <p id="rider-hub-msg" class="body-sm" style="margin-top: var(--space-2); min-height: 1.25rem;" aria-live="polite"></p>

  <section id="rider-waiting-panel" class="rider-waiting" hidden aria-live="polite">
    <div class="rider-waiting__row">
      <div class="rider-waiting__spinner" aria-hidden="true"></div>
      <div>
        <p class="body-md" style="font-weight: 700; margin: 0;">Waiting for drivers</p>
        <p class="body-sm muted" style="margin: 0.35rem 0 0;">
          Your ride is open for bids. Offers will appear below as drivers respond.
        </p>
        <p class="body-sm muted" style="margin: 0.35rem 0 0;">Ride #<span id="rider-waiting-id"></span></p>
      </div>
    </div>
  </section>

  <section id="rider-inline-bids" class="rider-inline-bids" hidden>
    <h3 class="headline-md" style="font-size: 1.1rem;">Driver offers</h3>
    <div id="rider-inline-bids-root"></div>
  </section>

  <script src="/static/rider_hub_actions.js"></script>
</body>
</html>
"""


def rider_bids_embed(maps_key: str) -> str:
    src = _maps_js_src(maps_key, "window.initRiderMap")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bids — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Rider</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Bids on your rides</h1>
  <p class="muted">Open rides only. Accepting assigns the driver and closes competing bids.</p>
  <!-- Map removed: list-only view of bids is sufficient -->
  <div class="tool-controls" style="margin-top: var(--space-2);">
    <a href="/">Rider hub</a>
    <button type="button" id="btn-refresh" class="btn btn--primary">Refresh</button>
  </div>
  <div id="bids-root"></div>
  <script src="/static/rider_bids.js"></script>
</body>
</html>
"""


def rider_bids_embed_no_key() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bids — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Rider</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Bids on your rides</h1>
  <p class="warn">Set <code>GOOGLE_MAPS_API_KEY</code> for the map. The list still works.</p>
  <p class="muted">Open rides only. Accepting assigns the driver and closes competing bids.</p>
  <!-- Map removed: list-only view of bids is sufficient -->
  <div class="tool-controls" style="margin-top: var(--space-2);">
    <a href="/">Rider hub</a>
    <button type="button" id="btn-refresh" class="btn btn--primary">Refresh</button>
  </div>
  <div id="bids-root"></div>
  <script src="/static/rider_bids.js"></script>
</body>
</html>
"""
