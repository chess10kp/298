(function () {
  let map = null;
  const markers = [];

  async function api(path, opts) {
    const r = await fetch(path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(opts && opts.headers) },
      ...opts,
    });
    const text = await r.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      data = text;
    }
    if (!r.ok) {
      throw new Error(
        typeof data === 'object' && data && data.detail
          ? JSON.stringify(data.detail)
          : r.statusText,
      );
    }
    return data;
  }

  function clearMarkers() {
    markers.forEach((m) => m.setMap(null));
    markers.length = 0;
  }

  async function refreshLocations() {
    const el = document.getElementById('fleet-out');
    try {
      const locs = await api('/api/v1/admin/driver-locations');
      el.textContent = JSON.stringify(locs, null, 2);

      if (!map || !window.google || !google.maps) return;

      clearMarkers();
      const bounds = new google.maps.LatLngBounds();
      locs.forEach((loc) => {
        const pos = { lat: loc.lat, lng: loc.lng };
        const m = new google.maps.Marker({
          position: pos,
          map,
          title: `${loc.email} (#${loc.driver_id})`,
        });
        m.addListener('click', () => {
          if (!window._fleetInfo) window._fleetInfo = new google.maps.InfoWindow();
          window._fleetInfo.setContent(
            `<div style="font-family:system-ui,sans-serif"><strong>${loc.email}</strong><br>` +
              `Driver #${loc.driver_id}<br>Updated: ${loc.updated_at}</div>`,
          );
          window._fleetInfo.open(map, m);
        });
        markers.push(m);
        bounds.extend(pos);
      });
      if (locs.length > 0) map.fitBounds(bounds);
    } catch (e) {
      el.textContent = 'Could not load locations: ' + e.message;
    }
  }

  window.initAdminMap = function () {
    const el = document.getElementById('admin-map');
    if (!window.google || !google.maps) {
      el.textContent = 'Maps failed to load.';
      return;
    }
    map = new google.maps.Map(el, {
      center: { lat: 40.7128, lng: -74.006 },
      zoom: 11,
    });
    setInterval(refreshLocations, 10000);
    refreshLocations();
  };

  if (!document.querySelector('script[src*="maps.googleapis.com"]')) {
    setInterval(refreshLocations, 10000);
    refreshLocations();
  }
})();
