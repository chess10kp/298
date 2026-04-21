(function () {
  console.log('[Driver] Loading driver.js v7');
  let watchPosId = null;

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

  function cents(usd) {
    return Math.round(Number(usd) * 100);
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fmtTime(iso) {
    try {
      return new Date(iso).toLocaleTimeString();
    } catch (_) {
      return iso;
    }
  }

  function locCell(lat, lng, label) {
    const coords =
      esc(Number(lat).toFixed(5)) + ', ' + esc(Number(lng).toFixed(5));
    if (label) {
      return (
        '<span class="rides-table__place">' +
        esc(label) +
        '</span><br><span class="muted rides-table__coords">' +
        coords +
        '</span>'
      );
    }
    return '<span class="rides-table__mono">' + coords + '</span>';
  }

  // Simple in-memory cache for reverse-geocoding results to avoid repeated
  // network calls while the page is open. Key is "lat,lng" with 5-decimal
  // precision to match how coordinates are displayed.
  const geocodeCache = {};

  async function reverseGeocode(lat, lng) {
    const key = Number(lat).toFixed(5) + ',' + Number(lng).toFixed(5);
    if (Object.prototype.hasOwnProperty.call(geocodeCache, key)) {
      return geocodeCache[key];
    }
    try {
      // Use OpenStreetMap Nominatim reverse geocoding (no API key required).
      // This is suitable for demo/demo-seed usage. For production, use a
      // server-side geocoder or an API key with usage limits.
      const url =
        'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=' +
        encodeURIComponent(lat) +
        '&lon=' +
        encodeURIComponent(lng);
      const r = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!r.ok) throw new Error('Geocode failed');
      const data = await r.json();
      const name = data && data.display_name ? data.display_name : null;
      geocodeCache[key] = name;
      return name;
    } catch (e) {
      // On failure, cache null to avoid repeated failing requests
      geocodeCache[key] = null;
      return null;
    }
  }

  async function placeBid(rideId, fareInput) {
    const fareUsd = fareInput.value.trim();
    if (!fareUsd) return alert('Enter a fare amount first.');
    try {
      await api(`/api/v1/rides/${rideId}/bids`, {
        method: 'POST',
        body: JSON.stringify({ fare_cents: cents(fareUsd) }),
      });
      alert('Bid placed!');
    } catch (e) {
      alert(e.message);
    }
  }

  async function enrichRidePlaceLabels(rides) {
    if (!rides || rides.length === 0) return;
    const toResolve = [];
    rides.forEach(function (ride) {
      try {
        if (!ride.pickup_location && ride.pickup_lat != null && ride.pickup_lng != null) {
          const key = Number(ride.pickup_lat).toFixed(5) + ',' + Number(ride.pickup_lng).toFixed(5);
          if (!Object.prototype.hasOwnProperty.call(geocodeCache, key)) toResolve.push({ lat: ride.pickup_lat, lng: ride.pickup_lng });
        }
        if (!ride.dropoff_location && ride.dropoff_lat != null && ride.dropoff_lng != null) {
          const key = Number(ride.dropoff_lat).toFixed(5) + ',' + Number(ride.dropoff_lng).toFixed(5);
          if (!Object.prototype.hasOwnProperty.call(geocodeCache, key)) toResolve.push({ lat: ride.dropoff_lat, lng: ride.dropoff_lng });
        }
      } catch (_) {}
    });
    const unique = {};
    toResolve.forEach(function (p) {
      unique[Number(p.lat).toFixed(5) + ',' + Number(p.lng).toFixed(5)] = p;
    });
    await Promise.all(
      Object.keys(unique).map(function (k) {
        const p = unique[k];
        return reverseGeocode(p.lat, p.lng);
      }),
    );
  }

  async function buildTable(rides) {
    if (!rides || rides.length === 0) {
      return '<p class="rides-table__empty">No rides available right now.</p>';
    }
    await enrichRidePlaceLabels(rides);

    const rows = rides.map(function (ride) {
      return (
        '<tr data-ride-id="' + esc(ride.id) + '" style="cursor:pointer;">' +
        '<td class="rides-table__id"><span class="rides-table__id-inner">' +
        esc(ride.id) +
        '</span></td>' +
        '<td>' +
        locCell(ride.pickup_lat, ride.pickup_lng, ride.pickup_location || geocodeCache[Number(ride.pickup_lat).toFixed(5) + ',' + Number(ride.pickup_lng).toFixed(5)]) +
        '</td>' +
        '<td>' +
        locCell(ride.dropoff_lat, ride.dropoff_lng, ride.dropoff_location || geocodeCache[Number(ride.dropoff_lat).toFixed(5) + ',' + Number(ride.dropoff_lng).toFixed(5)]) +
        '</td>' +
        '<td class="rides-table__time rides-table__mono">' +
        esc(fmtTime(ride.created_at)) +
        '</td>' +
        '<td>' +
        '<div style="display:flex;gap:0.5rem;align-items:center;">' +
        '<input type="number" step="0.01" min="0.01" value="12.00" ' +
        'style="width:5rem;font-size:0.875rem;padding:0.25rem 0.5rem;border:1px solid var(--outline-variant,#e5e5e5);border-radius:0.25rem;" ' +
        'data-ride-id="' +
        esc(ride.id) +
        '">' +
        '<button type="button" class="btn btn--primary btn--sm" ' +
        'onclick="event.stopPropagation();window.__driverPlaceBid(' +
        esc(ride.id) +
        ', this.previousElementSibling)">' +
        'Bid' +
        '</button>' +
        '</div>' +
        '</td>' +
        '</tr>'
      );
    });
    return (
      '<table class="rides-table">' +
      '<thead><tr>' +
      '<th>ID</th>' +
      '<th>Pickup</th>' +
      '<th>Dropoff</th>' +
      '<th>Created</th>' +
      '<th>Your bid</th>' +
      '</tr></thead>' +
      '<tbody>' +
      rows.join('') +
      '</tbody>' +
      '</table>'
    );
  }

  async function buildActiveTable(rides) {
    if (!rides || rides.length === 0) {
      return '<p class="rides-table__empty muted">No active trips. After a rider accepts your bid, the ride appears here.</p>';
    }
    await enrichRidePlaceLabels(rides);
    const rows = rides.map(function (ride) {
      let actions = '';
      if (ride.status === 'assigned') {
        actions =
          '<button type="button" class="btn btn--secondary btn--sm" onclick="event.stopPropagation();window.__driverStartTrip(' +
          esc(ride.id) +
          ')">Start ride</button>';
      } else if (ride.status === 'in_progress') {
        let waitNote = '';
        if (ride.driver_marked_complete_at) {
          waitNote =
            '<span class="muted body-sm" style="display:block;margin-top:0.35rem;">You marked complete — waiting for rider.</span>';
        }
        actions =
          '<button type="button" class="btn btn--primary btn--sm" onclick="event.stopPropagation();window.__driverMarkTripComplete(' +
          esc(ride.id) +
          ')">Complete ride</button>' +
          waitNote;
      }
      return (
        '<tr data-ride-id="' +
        esc(ride.id) +
        '" data-active-trip="1" style="cursor:pointer;">' +
        '<td class="rides-table__id"><span class="rides-table__id-inner">' +
        esc(ride.id) +
        '</span></td>' +
        '<td>' +
        locCell(ride.pickup_lat, ride.pickup_lng, ride.pickup_location || geocodeCache[Number(ride.pickup_lat).toFixed(5) + ',' + Number(ride.pickup_lng).toFixed(5)]) +
        '</td>' +
        '<td>' +
        locCell(ride.dropoff_lat, ride.dropoff_lng, ride.dropoff_location || geocodeCache[Number(ride.dropoff_lat).toFixed(5) + ',' + Number(ride.dropoff_lng).toFixed(5)]) +
        '</td>' +
        '<td class="rides-table__mono">' +
        esc(ride.status) +
        '</td>' +
        '<td>' +
        actions +
        '</td>' +
        '</tr>'
      );
    });
    return (
      '<table class="rides-table">' +
      '<thead><tr>' +
      '<th>ID</th>' +
      '<th>Pickup</th>' +
      '<th>Dropoff</th>' +
      '<th>Status</th>' +
      '<th>Actions</th>' +
      '</tr></thead>' +
      '<tbody>' +
      rows.join('') +
      '</tbody></table>'
    );
  }

  function wireRowSelect(container) {
    if (!container) return;
    container.querySelectorAll('tbody tr[data-ride-id]').forEach(function (row) {
      row.onclick = function () {
        document.querySelectorAll('tbody tr[data-ride-id]').forEach(function (r) {
          r.style.backgroundColor = '';
        });
        row.style.backgroundColor = '#e3f2fd';
        const rid = document.getElementById('ride-id');
        if (rid) rid.value = row.dataset.rideId;
      };
    });
  }

  async function refreshRides() {
    const el = document.getElementById('rides-out');
    const activeEl = document.getElementById('rides-active-out');
    if (!el) return;
    try {
      const [rides, active] = await Promise.all([
        api('/api/v1/rides/open'),
        api('/api/v1/rides/driver/active'),
      ]);
      window.__lastOpenRides = rides;
      window.__lastActiveRides = active;
      console.log('[Driver] Fetched', rides.length, 'open rides,', active.length, 'active trips');
      el.innerHTML = await buildTable(rides);
      wireRowSelect(el);
      if (activeEl) {
        activeEl.innerHTML = await buildActiveTable(active);
        wireRowSelect(activeEl);
      }
    } catch (e) {
      el.innerHTML =
        '<p class="err">Could not load rides: ' + esc(e.message) + '</p>';
      if (activeEl) activeEl.innerHTML = '';
    }
  }

  window.__driverPlaceBid = function (rideId, fareInput) {
    placeBid(rideId, fareInput).then(refreshRides);
  };

  window.__driverStartTrip = function (rideId) {
    api('/api/v1/rides/' + rideId + '/start', { method: 'POST', body: '{}' })
      .then(function () {
        alert('Ride started.');
        return refreshRides();
      })
      .catch(function (e) {
        alert(e.message);
      });
  };

  window.__driverMarkTripComplete = function (rideId) {
    api('/api/v1/rides/' + rideId + '/complete', { method: 'POST', body: '{}' })
      .then(function (ride) {
        if (ride.status === 'completed') {
          alert('Ride completed (rider confirmed too).');
        } else if (ride.status === 'in_progress') {
          alert('You marked this ride complete. Waiting for the rider to confirm.');
        } else {
          alert('Updated: ' + ride.status);
        }
        return refreshRides();
      })
      .catch(function (e) {
        alert(e.message);
      });
  };

  function startGpsTracking() {
    if (!navigator.geolocation) return;
    watchPosId = navigator.geolocation.watchPosition(
      function (pos) {
        api('/api/v1/driver/location', {
          method: 'POST',
          body: JSON.stringify({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          }),
        }).catch(function () {});
      },
      function () {},
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 },
    );
  }

  function attachControls() {
    const startBtn = document.getElementById('btn-start');
    if (!startBtn || startBtn.dataset.wired === '1') return;
    startBtn.dataset.wired = '1';

    // Seed button removed — demo data is inserted automatically on fresh DB startup.

    startBtn.onclick = async function () {
      const id = document.getElementById('ride-id').value;
      if (!id) return alert('Enter a ride ID first.');
      try {
        await api('/api/v1/rides/' + id + '/start', { method: 'POST', body: '{}' });
        alert('Ride started.');
        await refreshRides();
      } catch (e) {
        alert(e.message);
      }
    };

    document.getElementById('btn-done').onclick = async function () {
      const id = document.getElementById('ride-id').value;
      if (!id) return alert('Enter a ride ID first.');
      try {
        const ride = await api('/api/v1/rides/' + id + '/complete', { method: 'POST', body: '{}' });
        if (ride.status === 'completed') {
          alert('Ride completed (rider confirmed too).');
        } else if (ride.status === 'in_progress') {
          alert('You marked this ride complete. Waiting for the rider to confirm.');
        } else {
          alert('Updated: ' + ride.status);
        }
        await refreshRides();
      } catch (e) {
        alert(e.message);
      }
    };
  }

  function init() {
    startGpsTracking();
    setInterval(refreshRides, 8000);
    refreshRides();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', attachControls);
    } else {
      attachControls();
    }
  }

  window.initDriverMap = function () {
    startGpsTracking();
    init();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
