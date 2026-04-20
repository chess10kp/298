(function () {
  console.log('[Driver] Loading driver.js v2');
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

  function buildTable(rides) {
    if (!rides || rides.length === 0) {
      return '<p class="rides-table__empty">No rides available right now.</p>';
    }
    const rows = rides.map(function (ride) {
      return (
        '<tr data-ride-id="' + esc(ride.id) + '" style="cursor:pointer;">' +
        '<td class="rides-table__id"><span class="rides-table__id-inner">' +
        esc(ride.id) +
        '</span></td>' +
        '<td class="rides-table__mono">' +
        esc(ride.pickup_lat.toFixed(5)) +
        ', ' +
        esc(ride.pickup_lng.toFixed(5)) +
        '</td>' +
        '<td class="rides-table__mono">' +
        esc(ride.dropoff_lat.toFixed(5)) +
        ', ' +
        esc(ride.dropoff_lng.toFixed(5)) +
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

  async function refreshRides() {
    const el = document.getElementById('rides-out');
    if (!el) return;
    try {
      const rides = await api('/api/v1/rides/open');
      window.__lastOpenRides = rides;
      console.log('[Driver] Fetched', rides.length, 'open rides');
      el.innerHTML = buildTable(rides);
      el.querySelectorAll('tbody tr[data-ride-id]').forEach(function (row) {
        row.onclick = function () {
          document.querySelectorAll('tbody tr').forEach(function (r) {
            r.style.backgroundColor = '';
          });
          row.style.backgroundColor = '#e3f2fd';
          document.getElementById('ride-id').value = row.dataset.rideId;
        };
      });
    } catch (e) {
      el.innerHTML =
        '<p class="err">Could not load rides: ' + esc(e.message) + '</p>';
    }
  }

  window.__driverPlaceBid = function (rideId, fareInput) {
    placeBid(rideId, fareInput).then(refreshRides);
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
        await api('/api/v1/rides/' + id + '/complete', { method: 'POST', body: '{}' });
        alert('Ride completed.');
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
