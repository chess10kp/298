(function () {
  // No map needed for the bids list view — render list-only UI.

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

  function fmtFare(cents) {
    return (Number(cents) / 100).toFixed(2);
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/"/g, '&quot;');
  }

  function coordKey(lat, lng) {
    return Number(lat).toFixed(5) + ',' + Number(lng).toFixed(5);
  }

  async function resolveAddressLabels(rides) {
    const points = [];
    for (const r of rides) {
      if (!r.pickup_location) points.push({ lat: r.pickup_lat, lng: r.pickup_lng });
      if (!r.dropoff_location) points.push({ lat: r.dropoff_lat, lng: r.dropoff_lng });
    }
    if (points.length === 0) return {};
    try {
      const res = await api('/api/v1/geocode/reverse-batch', {
        method: 'POST',
        body: JSON.stringify({ points }),
      });
      return res && typeof res.labels === 'object' ? res.labels : {};
    } catch (_) {
      return {};
    }
  }

  async function refresh(silent) {
    const root = document.getElementById('bids-root');
    if (!silent) root.innerHTML = '<p>Loading…</p>';
    try {
      const rides = await api('/api/v1/rides/me');
      const open = rides.filter((r) => r.status === 'bidding_open');
      if (open.length === 0) {
        root.innerHTML = '<p>No rides in <code>bidding_open</code> status.</p>';
        return;
      }
      const labels = await resolveAddressLabels(open);
      const parts = [];
      for (const ride of open) {
        const bids = await api(`/api/v1/rides/${ride.id}/bids`);
        let bidHtml = '';
        if (bids.length === 0) {
          bidHtml = '<p class="muted">No bids yet.</p>';
        } else {
          bidHtml =
            '<ul class="bid-list-ds">' +
            bids
              .map(
                (b) =>
                  `<li><strong>$${fmtFare(b.fare_cents)}</strong> — driver #${esc(b.driver_id)} · ` +
                  `${esc(b.distance_to_pickup_m)} m · ${esc(b.status)} ` +
                  `<button type="button" class="btn btn--secondary accept-btn" data-ride="${ride.id}" data-bid="${b.id}">Accept</button></li>`,
              )
              .join('') +
            '</ul>';
        }
        const pk = coordKey(ride.pickup_lat, ride.pickup_lng);
        const dk = coordKey(ride.dropoff_lat, ride.dropoff_lng);
        const pickupResolved = ride.pickup_location || labels[pk];
        const dropResolved = ride.dropoff_location || labels[dk];
        parts.push(
          `<section class="ride-card-ds"><h2>Ride #${esc(ride.id)}</h2>` +
            `<p class="muted">Pickup: ${
              pickupResolved
                ? esc(pickupResolved) + ' · ' + esc(ride.pickup_lat) + ', ' + esc(ride.pickup_lng)
                : esc(ride.pickup_lat) + ', ' + esc(ride.pickup_lng)
            } · Dropoff: ${
              dropResolved
                ? esc(dropResolved) + ' · ' + esc(ride.dropoff_lat) + ', ' + esc(ride.dropoff_lng)
                : esc(ride.dropoff_lat) + ', ' + esc(ride.dropoff_lng)
            }</p>` +
            bidHtml +
            `</section>`,
        );
      }
      root.innerHTML = parts.join('');
      root.querySelectorAll('.accept-btn').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const rideId = btn.getAttribute('data-ride');
          const bidId = btn.getAttribute('data-bid');
          if (!confirm('Accept this bid and assign the driver?')) return;
          try {
            await api(`/api/v1/rides/${rideId}/bids/${bidId}/accept`, { method: 'POST', body: '{}' });
            await refresh(true);
          } catch (e) {
            alert(e.message);
          }
        });
      });
      // no map to update in list-only view
    } catch (e) {
      root.innerHTML = '<p class="err">Error: ' + esc(e.message) + '</p>';
    }
  }

  // no maps init — list-only

  window.addEventListener('message', function (ev) {
    if (ev.data && ev.data.type === 'fruger-refresh-bids') refresh(true);
  });

  document.getElementById('btn-refresh').addEventListener('click', function () {
    refresh(false);
  });
  refresh(false);

  setInterval(function () {
    if (document.visibilityState === 'visible') refresh(true);
  }, 4000);
})();
