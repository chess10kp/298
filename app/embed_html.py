"""Minimal full-page HTML for map/tool UIs embedded in iframes (no Jinja)."""

from __future__ import annotations

import html


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


def driver_embed(maps_key: str) -> str:
    src = _maps_js_src(maps_key, "window.initDriverMap")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Driver — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Partner</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Driver map</h1>
  <p class="muted">Session-backed location updates. Open rides appear as numbered pickup markers.</p>
  <p class="muted" style="margin-top: var(--space-3);">Select a ride ID from a marker, then <strong>Route to pickup</strong> or place a bid.</p>

  <div id="map" class="tool-map"></div>

  <div class="tool-controls">
    <label>Ride ID <input id="ride-id" type="number" min="1" style="width:6rem"></label>
    <label>Fare (USD) <input id="fare-usd" type="number" step="0.01" min="0.01" value="12.00" style="width:5rem"></label>
    <button id="btn-bid" type="button" class="btn btn--primary">Place bid</button>
    <button id="btn-route" type="button" class="btn btn--ghost">Route to pickup</button>
    <button id="btn-start" type="button" class="btn btn--ghost">Start ride</button>
    <button id="btn-done" type="button" class="btn btn--secondary">Complete ride</button>
  </div>

  <h2>Open rides (raw)</h2>
  <pre id="rides-out" class="tool-pre">Loading…</pre>
  <script src="/static/driver.js"></script>
  <script async defer src="{src}"></script>
</body>
</html>
"""


def driver_embed_no_key() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Driver — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Partner</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Driver map</h1>
  <p class="warn">Set <code>GOOGLE_MAPS_API_KEY</code> to enable the map. Bids and ride APIs still work.</p>
  <p class="muted">Session-backed location updates. Open rides appear as numbered pickup markers.</p>
  <p class="muted" style="margin-top: var(--space-3);">Select a ride ID from a marker, then <strong>Route to pickup</strong> or place a bid.</p>
  <div id="map" class="tool-map"></div>
  <div class="tool-controls">
    <label>Ride ID <input id="ride-id" type="number" min="1" style="width:6rem"></label>
    <label>Fare (USD) <input id="fare-usd" type="number" step="0.01" min="0.01" value="12.00" style="width:5rem"></label>
    <button id="btn-bid" type="button" class="btn btn--primary">Place bid</button>
    <button id="btn-route" type="button" class="btn btn--ghost">Route to pickup</button>
    <button id="btn-start" type="button" class="btn btn--ghost">Start ride</button>
    <button id="btn-done" type="button" class="btn btn--secondary">Complete ride</button>
  </div>
  <h2>Open rides (raw)</h2>
  <pre id="rides-out" class="tool-pre">Loading…</pre>
  <script src="/static/driver.js"></script>
  <script>window.initDriverMap = function () { console.warn('No maps key'); };</script>
</body>
</html>
"""


def admin_map_embed(maps_key: str) -> str:
    src = _maps_js_src(maps_key, "window.initAdminMap")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fleet map — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Fleet</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Partner map</h1>
  <p class="muted">Last reported driver GPS from <code>driver_locations</code>. Polls every 10s.</p>
  <p><a href="/admin/dashboard">Admin console</a></p>
  <div id="admin-map" class="tool-map tool-map--tall"></div>
  <h2>Driver locations (raw)</h2>
  <pre id="fleet-out" class="tool-pre">Loading…</pre>
  <script src="/static/admin_map.js"></script>
  <script async defer src="{src}"></script>
</body>
</html>
"""


def admin_map_embed_no_key() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fleet map — Fruger</title>
  <link rel="stylesheet" href="/static/theme.css">
</head>
<body class="tool-page">
  <p class="label-md" style="margin: 0 0 var(--space-2);">Fleet</p>
  <h1 class="headline-md" style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.03em;">Partner map</h1>
  <p class="warn">Set <code>GOOGLE_MAPS_API_KEY</code> for the map. JSON still loads below.</p>
  <p class="muted">Last reported driver GPS from <code>driver_locations</code>. Polls every 10s.</p>
  <p><a href="/admin/dashboard">Admin console</a></p>
  <div id="admin-map" class="tool-map tool-map--tall"></div>
  <h2>Driver locations (raw)</h2>
  <pre id="fleet-out" class="tool-pre">Loading…</pre>
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

  <form id="cancel-ride-form" class="tool-controls" style="flex-wrap: wrap; align-items: flex-end; margin-top: var(--space-3);">
    <fieldset style="border: 1px solid var(--border-subtle, #e5e5e5); border-radius: 8px; padding: var(--space-3); margin: 0; flex: 1 1 12rem;">
      <legend class="body-sm" style="font-weight: 600; padding: 0 0.25rem;">Cancel a ride</legend>
      <label>Ride ID <input name="ride_id" type="number" min="1" step="1" required style="width: 6rem;"></label>
      <button type="submit" class="btn btn--secondary" style="margin-left: var(--space-2);">Cancel ride</button>
    </fieldset>
  </form>

  <div class="tool-controls" style="margin-top: var(--space-3);">
    <button type="button" id="rider-hub-logout" class="btn btn--ghost">Log out</button>
  </div>

  <p id="rider-hub-msg" class="body-sm" style="margin-top: var(--space-2); min-height: 1.25rem;" aria-live="polite"></p>
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

  <form id="cancel-ride-form" class="tool-controls" style="flex-wrap: wrap; align-items: flex-end; margin-top: var(--space-3);">
    <fieldset style="border: 1px solid var(--border-subtle, #e5e5e5); border-radius: 8px; padding: var(--space-3); margin: 0; flex: 1 1 12rem;">
      <legend class="body-sm" style="font-weight: 600; padding: 0 0.25rem;">Cancel a ride</legend>
      <label>Ride ID <input name="ride_id" type="number" min="1" step="1" required style="width: 6rem;"></label>
      <button type="submit" class="btn btn--secondary" style="margin-left: var(--space-2);">Cancel ride</button>
    </fieldset>
  </form>

  <div class="tool-controls" style="margin-top: var(--space-3);">
    <button type="button" id="rider-hub-logout" class="btn btn--ghost">Log out</button>
  </div>

  <p id="rider-hub-msg" class="body-sm" style="margin-top: var(--space-2); min-height: 1.25rem;" aria-live="polite"></p>
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
  <div id="rider-map" class="tool-map" style="height: 360px;"></div>
  <div class="tool-controls" style="margin-top: var(--space-2);">
    <a href="/">Rider hub</a>
    <button type="button" id="btn-refresh" class="btn btn--primary">Refresh</button>
  </div>
  <div id="bids-root"></div>
  <script src="/static/rider_bids.js"></script>
  <script async defer src="{src}"></script>
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
  <div id="rider-map" class="tool-map" style="height: 360px;"></div>
  <div class="tool-controls" style="margin-top: var(--space-2);">
    <a href="/">Rider hub</a>
    <button type="button" id="btn-refresh" class="btn btn--primary">Refresh</button>
  </div>
  <div id="bids-root"></div>
  <script src="/static/rider_bids.js"></script>
  <script>window.initRiderMap = function () { console.warn('No maps key'); };</script>
</body>
</html>
"""
