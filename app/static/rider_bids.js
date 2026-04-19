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

  function fmtFare(cents) {
    return (Number(cents) / 100).toFixed(2);
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/"/g, '&quot;');
  }

  function clearMapMarkers() {
    markers.forEach((m) => m.setMap(null));
    markers.length = 0;
  }

  async function updateMap(openRides) {
    if (!map || !window.google || !google.maps) return;
    clearMapMarkers();
    const bounds = new google.maps.LatLngBounds();
    let has = false;

    for (const ride of openRides) {
      const pickup = { lat: Number(ride.pickup_lat), lng: Number(ride.pickup_lng) };
      const dropoff = { lat: Number(ride.dropoff_lat), lng: Number(ride.dropoff_lng) };

      const pickupM = new google.maps.Marker({
        position: pickup,
        map,
        label: `P${ride.id}`,
        title: `Ride #${ride.id} pickup`,
      });
      markers.push(pickupM);
      bounds.extend(pickup);
      has = true;

      const dropM = new google.maps.Marker({
        position: dropoff,
        map,
        label: `D${ride.id}`,
        title: `Ride #${ride.id} dropoff`,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: '#b91c1c',
          fillOpacity: 0.9,
          strokeWeight: 1,
          strokeColor: '#fff',
        },
      });
      markers.push(dropM);
      bounds.extend(dropoff);
      has = true;

      try {
        const bidders = await api(`/api/rides/${ride.id}/bidder-locations`);
        bidders.forEach((b) => {
          const pos = { lat: b.lat, lng: b.lng };
          const m = new google.maps.Marker({
            position: pos,
            map,
            title: `Driver #${b.driver_id} (bidder)`,
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 7,
              fillColor: '#2563eb',
              fillOpacity: 0.95,
              strokeWeight: 1,
              strokeColor: '#fff',
            },
          });
          markers.push(m);
          bounds.extend(pos);
          has = true;
        });
      } catch (_) {
        /* ignore map pin errors */
      }
    }

    if (has) map.fitBounds(bounds);
  }

  async function refresh() {
    const root = document.getElementById('bids-root');
    root.innerHTML = '<p>Loading…</p>';
    try {
      const rides = await api('/api/rides/me');
      const open = rides.filter((r) => r.status === 'bidding_open');
      if (open.length === 0) {
        root.innerHTML = '<p>No rides in <code>bidding_open</code> status.</p>';
        clearMapMarkers();
        return;
      }
      const parts = [];
      for (const ride of open) {
        const bids = await api(`/api/rides/${ride.id}/bids`);
        let bidHtml = '';
        if (bids.length === 0) {
          bidHtml = '<p class="muted">No bids yet.</p>';
        } else {
          bidHtml =
            '<ul class="bid-list">' +
            bids
              .map(
                (b) =>
                  `<li><strong>$${fmtFare(b.fare_cents)}</strong> — driver #${esc(b.driver_id)} · ` +
                  `${esc(b.distance_to_pickup_m)} m · ${esc(b.status)} ` +
                  `<button type="button" class="accept-btn" data-ride="${ride.id}" data-bid="${b.id}">Accept</button></li>`,
              )
              .join('') +
            '</ul>';
        }
        parts.push(
          `<section class="ride-card"><h2>Ride #${esc(ride.id)}</h2>` +
            `<p class="muted">Pickup: ${esc(ride.pickup_lat)}, ${esc(ride.pickup_lng)} · ` +
            `Dropoff: ${esc(ride.dropoff_lat)}, ${esc(ride.dropoff_lng)}</p>` +
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
            await api(`/api/rides/${rideId}/bids/${bidId}/accept`, { method: 'POST', body: '{}' });
            await refresh();
          } catch (e) {
            alert(e.message);
          }
        });
      });
      await updateMap(open);
    } catch (e) {
      root.innerHTML = '<p class="err">Error: ' + esc(e.message) + '</p>';
    }
  }

  window.initRiderMap = function () {
    const el = document.getElementById('rider-map');
    if (!window.google || !google.maps) {
      el.textContent = 'Maps failed to load.';
      return;
    }
    map = new google.maps.Map(el, {
      center: { lat: 40.7128, lng: -74.006 },
      zoom: 11,
    });
    refresh();
  };

  document.getElementById('btn-refresh').addEventListener('click', refresh);
  refresh();
})();
