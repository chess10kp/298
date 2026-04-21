(function () {
  /**
   * Google Maps callback — Places Autocomplete + live map markers (A = pickup, B = drop-off).
   */
  window.initRiderHubPlaces = function () {
    if (!window.google || !google.maps || !google.maps.places) return;
    var mapEl = document.getElementById('rider-hub-map');
    var defaultCenter = { lat: 40.7128, lng: -74.006 };
    var map = null;
    var pickupMarker = null;
    var dropoffMarker = null;
    if (mapEl) {
      map = new google.maps.Map(mapEl, {
        center: defaultCenter,
        zoom: 11,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
      });
      pickupMarker = new google.maps.Marker({
        map: map,
        title: 'Pickup',
        label: 'A',
        visible: false,
      });
      dropoffMarker = new google.maps.Marker({
        map: map,
        title: 'Drop-off',
        label: 'B',
        visible: false,
      });
    }

    function refreshMapView() {
      if (!map || !pickupMarker || !dropoffMarker) return;
      var pa = pickupMarker.getPosition();
      var pb = dropoffMarker.getPosition();
      if (pa && pb) {
        var bounds = new google.maps.LatLngBounds();
        bounds.extend(pa);
        bounds.extend(pb);
        map.fitBounds(bounds, 48);
      } else if (pa) {
        map.setCenter(pa);
        map.setZoom(14);
      } else if (pb) {
        map.setCenter(pb);
        map.setZoom(14);
      }
    }

    var opts = {
      fields: ['geometry', 'formatted_address'],
      componentRestrictions: { country: 'us' },
    };
    function bindSearch(inputId, latId, lngId, marker) {
      var input = document.getElementById(inputId);
      var latEl = document.getElementById(latId);
      var lngEl = document.getElementById(lngId);
      if (!input || !latEl || !lngEl) return;
      var ac = new google.maps.places.Autocomplete(input, opts);
      ac.addListener('place_changed', function () {
        var place = ac.getPlace();
        if (!place.geometry || !place.geometry.location) {
          latEl.value = '';
          lngEl.value = '';
          if (marker) {
            marker.setVisible(false);
            refreshMapView();
          }
          return;
        }
        var loc = place.geometry.location;
        latEl.value = String(loc.lat());
        lngEl.value = String(loc.lng());
        if (marker && map) {
          marker.setPosition(loc);
          marker.setVisible(true);
          refreshMapView();
        }
      });
    }
    bindSearch('pickup_search', 'pickup_lat', 'pickup_lng', pickupMarker);
    bindSearch('dropoff_search', 'dropoff_lat', 'dropoff_lng', dropoffMarker);
  };

  let bidPollTimer = null;
  let bidPollRideId = null;

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
      const detail =
        typeof data === 'object' && data && data.detail !== undefined
          ? typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail)
          : r.statusText;
      throw new Error(detail);
    }
    return data;
  }

  function setMsg(el, text, ok) {
    el.textContent = text;
    el.classList.remove('ok', 'err');
    if (ok === true) el.classList.add('ok');
    if (ok === false) el.classList.add('err');
  }

  function coordKey(lat, lng) {
    return Number(lat).toFixed(5) + ',' + Number(lng).toFixed(5);
  }

  /** Server reverse geocode for coords missing pickup/dropoff labels (session cookie). */
  function rideStatusCell(status) {
    const s = String(status || '');
    const label = s.replace(/_/g, ' ');
    return (
      '<span class="ride-status ride-status--' +
      esc(s) +
      '">' +
      esc(label) +
      '</span>'
    );
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

  function reloadParent() {
    try {
      if (window.parent && window.parent !== window) window.parent.location.reload();
    } catch (_) {
      /* cross-origin parent */
    }
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

  function notifyBidsIframeRefresh() {
    try {
      if (window.parent === window) return;
      const parent = window.parent;
      const iframes = parent.document.querySelectorAll('iframe');
      iframes.forEach((f) => {
        try {
          if (f.src && f.src.indexOf('/embed/rider/bids') !== -1 && f.contentWindow) {
            f.contentWindow.postMessage({ type: 'fruger-refresh-bids' }, '*');
          }
        } catch (_) {}
      });
    } catch (_) {}
  }

  function stopBidPolling() {
    if (bidPollTimer) {
      clearInterval(bidPollTimer);
      bidPollTimer = null;
    }
    bidPollRideId = null;
  }

  function hideWaitingUi() {
    const w = document.getElementById('rider-waiting-panel');
    if (w) w.hidden = true;
  }

  function showWaitingUi(rideId) {
    const w = document.getElementById('rider-waiting-panel');
    const num = document.getElementById('rider-waiting-id');
    const inline = document.getElementById('rider-inline-bids');
    if (num) num.textContent = String(rideId);
    if (w) {
      w.hidden = false;
      try {
        w.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch (_) {}
    }
    if (inline) inline.hidden = false;
  }

  function renderInlineBids(bids, rideId) {
    const root = document.getElementById('rider-inline-bids-root');
    if (!root) return;
    if (bids.length === 0) {
      root.innerHTML =
        '<p class="body-sm muted" style="margin:0;">No offers yet — we’ll show each bid here as drivers respond.</p>';
      return;
    }
    root.innerHTML =
      '<ul class="bid-list-ds">' +
      bids
        .map(
          (b) =>
            `<li><strong>$${fmtFare(b.fare_cents)}</strong> — driver #${esc(b.driver_id)} · ` +
            `${esc(b.distance_to_pickup_m)} m · ${esc(b.status)} ` +
            `<button type="button" class="btn btn--secondary rider-inline-accept" data-ride="${rideId}" data-bid="${b.id}">Accept</button></li>`,
        )
        .join('') +
      '</ul>';
    root.querySelectorAll('.rider-inline-accept').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const rid = btn.getAttribute('data-ride');
        const bid = btn.getAttribute('data-bid');
        if (!confirm('Accept this bid and assign the driver?')) return;
        const msg = document.getElementById('rider-hub-msg');
        try {
          await api(`/api/v1/rides/${rid}/bids/${bid}/accept`, { method: 'POST', body: '{}' });
          stopBidPolling();
          hideWaitingUi();
          if (msg) setMsg(msg, `Bid accepted for ride #${rid}.`, true);
          notifyBidsIframeRefresh();
          reloadParent();
        } catch (err) {
          if (msg) setMsg(msg, String(err.message || err), false);
        }
      });
    });
  }

  function startBidPolling(rideId) {
    stopBidPolling();
    bidPollRideId = rideId;
    const msg = document.getElementById('rider-hub-msg');
    const tick = async () => {
      if (!bidPollRideId) return;
      try {
        const ride = await api(`/api/v1/rides/${rideId}`);
        const bids = await api(`/api/v1/rides/${rideId}/bids`);
        renderInlineBids(bids, rideId);
        notifyBidsIframeRefresh();

        if (ride.status !== 'bidding_open') {
          stopBidPolling();
          hideWaitingUi();
          if (msg) {
            if (ride.status === 'assigned' || ride.status === 'in_progress') {
              setMsg(msg, `Ride #${rideId} is assigned.`, true);
            } else if (ride.status === 'completed') {
              setMsg(msg, `Ride #${rideId} completed.`, true);
            } else if (ride.status === 'cancelled') {
              setMsg(msg, `Ride #${rideId} was cancelled.`, false);
            } else {
              setMsg(msg, `Ride #${rideId}: ${ride.status}.`, true);
            }
          }
          notifyBidsIframeRefresh();
          return;
        }
      } catch (e) {
        if (msg) setMsg(msg, String(e.message || e), false);
      }
    };
    tick();
    bidPollTimer = setInterval(tick, 2000);
  }

  function parseCoordForm(fd) {
    const pickup_lat = parseFloat(String(fd.get('pickup_lat') ?? '').trim());
    const pickup_lng = parseFloat(String(fd.get('pickup_lng') ?? '').trim());
    const dropoff_lat = parseFloat(String(fd.get('dropoff_lat') ?? '').trim());
    const dropoff_lng = parseFloat(String(fd.get('dropoff_lng') ?? '').trim());
    return { pickup_lat, pickup_lng, dropoff_lat, dropoff_lng };
  }

  const msg = document.getElementById('rider-hub-msg');

  const createForm = document.getElementById('create-ride-form');
  if (createForm) {
    createForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!msg) return;
      setMsg(msg, 'Sending your request…', null);
      const fd = new FormData(createForm);
      const body = parseCoordForm(fd);
      if (
        !Number.isFinite(body.pickup_lat) ||
        !Number.isFinite(body.pickup_lng) ||
        !Number.isFinite(body.dropoff_lat) ||
        !Number.isFinite(body.dropoff_lng)
      ) {
        setMsg(
          msg,
          document.getElementById('pickup_search')
            ? 'Choose pickup and drop-off from the search suggestions.'
            : 'Enter valid latitude and longitude for all four fields.',
          false,
        );
        return;
      }
      try {
        const ride = await api('/api/v1/rides', { method: 'POST', body: JSON.stringify(body) });
        setMsg(msg, `Ride #${ride.id} is open for bids.`, true);
        showWaitingUi(ride.id);
        renderInlineBids([], ride.id);
        startBidPolling(ride.id);
        notifyBidsIframeRefresh();
        // Refresh the rider's rides list so the new ride appears with its cancel button
        try { fetchAndRenderMyRides(); } catch (_) {}
      } catch (err) {
        setMsg(msg, String(err.message || err), false);
      }
    });
  }

  const cancelForm = document.getElementById('cancel-ride-form');
  if (cancelForm) {
    cancelForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!msg) return;
      const fd = new FormData(cancelForm);
      const id = String(fd.get('ride_id') || '').trim();
      if (!id) {
        setMsg(msg, 'Enter a ride ID.', false);
        return;
      }
      setMsg(msg, 'Cancelling…', null);
      try {
        stopBidPolling();
        hideWaitingUi();
        const ride = await api(`/api/v1/rides/${encodeURIComponent(id)}/cancel`, {
          method: 'POST',
          body: '{}',
        });
        setMsg(msg, `Ride #${ride.id} cancelled (${ride.status}).`, true);
        notifyBidsIframeRefresh();
        reloadParent();
      } catch (err) {
        setMsg(msg, String(err.message || err), false);
      }
    });
  }

  // Render rider's own rides and show a cancel button per row.
  async function fetchAndRenderMyRides() {
    const root = document.getElementById('my-rides-root');
    if (!root) return;
    root.innerHTML = 'Loading…';
    try {
      const rides = await api('/api/v1/rides/me');
      if (!rides || rides.length === 0) {
        root.innerHTML = '<p class="muted">No rides found.</p>';
        return;
      }
      const labels = await resolveAddressLabels(rides);
      const rows = rides
        .map((r) => {
          const pk = coordKey(r.pickup_lat, r.pickup_lng);
          const dk = coordKey(r.dropoff_lat, r.dropoff_lng);
          const pickupResolved = r.pickup_location || labels[pk];
          const dropResolved = r.dropoff_location || labels[dk];
          const pickup = pickupResolved
            ? `${esc(pickupResolved)} · ${esc(r.pickup_lat)}, ${esc(r.pickup_lng)}`
            : `${esc(r.pickup_lat)}, ${esc(r.pickup_lng)}`;
          const drop = dropResolved
            ? `${esc(dropResolved)} · ${esc(r.dropoff_lat)}, ${esc(r.dropoff_lng)}`
            : `${esc(r.dropoff_lat)}, ${esc(r.dropoff_lng)}`;
          let actions = '';
          if (r.status === 'bidding_open' || r.status === 'assigned') {
            actions =
              '<button type="button" class="btn btn--secondary rider-cancel" data-ride="' +
              esc(r.id) +
              '">Cancel</button>';
          } else if (r.status === 'in_progress') {
            let hint = '';
            if (r.driver_marked_complete_at && !r.rider_marked_complete_at) {
              hint =
                '<span class="muted body-sm" style="display:block;margin-top:0.35rem;">Driver finished — confirm drop-off.</span>';
            } else if (!r.driver_marked_complete_at && r.rider_marked_complete_at) {
              hint =
                '<span class="muted body-sm" style="display:block;margin-top:0.35rem;">Waiting for driver to confirm.</span>';
            }
            actions =
              '<button type="button" class="btn btn--primary rider-trip-done" data-ride="' +
              esc(r.id) +
              '">Confirm trip complete</button>' +
              hint;
          } else {
            actions = '<span class="muted">—</span>';
          }
          return (
            '<tr data-ride-id="' + esc(r.id) + '">' +
            '<td class="rides-table__id"><span class="rides-table__id-inner">#' +
            esc(r.id) +
            '</span></td>' +
            '<td>' +
            rideStatusCell(r.status) +
            '</td>' +
            '<td>' +
            pickup +
            '</td>' +
            '<td>' +
            drop +
            '</td>' +
            '<td>' +
            actions +
            '</td>' +
            '</tr>'
          );
        })
        .join('');
      root.innerHTML =
        '<div class="embed-table-wrap">' +
        '<table class="fruger-data-table" aria-label="Your rides">' +
        '<thead><tr>' +
        '<th>Ride</th><th>Status</th><th>Pickup</th><th>Dropoff</th><th></th>' +
        '</tr></thead><tbody>' +
        rows +
        '</tbody></table></div>';
      root.querySelectorAll('.rider-cancel').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const rid = btn.getAttribute('data-ride');
          if (!confirm('Cancel ride #' + rid + '?')) return;
          try {
            setMsg(msg, 'Cancelling…', null);
            stopBidPolling();
            hideWaitingUi();
            const ride = await api(`/api/v1/rides/${encodeURIComponent(rid)}/cancel`, {
              method: 'POST',
              body: '{}',
            });
            setMsg(msg, `Ride #${ride.id} cancelled (${ride.status}).`, true);
            notifyBidsIframeRefresh();
            fetchAndRenderMyRides();
            reloadParent();
          } catch (err) {
            setMsg(msg, String(err.message || err), false);
          }
        });
      });
      root.querySelectorAll('.rider-trip-done').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const rid = btn.getAttribute('data-ride');
          if (!confirm('Confirm trip #' + rid + ' is finished?')) return;
          try {
            setMsg(msg, 'Saving…', null);
            const ride = await api(`/api/v1/rides/${encodeURIComponent(rid)}/rider-complete`, {
              method: 'POST',
              body: '{}',
            });
            if (ride.status === 'completed') {
              setMsg(msg, `Ride #${ride.id} completed.`, true);
            } else {
              setMsg(
                msg,
                `Recorded — trip #${ride.id} finishes when the driver confirms too.`,
                true,
              );
            }
            notifyBidsIframeRefresh();
            fetchAndRenderMyRides();
            reloadParent();
          } catch (err) {
            setMsg(msg, String(err.message || err), false);
          }
        });
      });
    } catch (err) {
      root.innerHTML = '<p class="err">' + esc(String(err.message || err)) + '</p>';
    }
  }

  // Initial render of my rides and subscribe to events that should refresh.
  fetchAndRenderMyRides();

  const logoutBtn = document.getElementById('rider-hub-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      if (!msg) return;
      setMsg(msg, 'Signing out…', null);
      try {
        const r = await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });
        if (!r.ok) throw new Error(r.statusText);
        window.top.location.href = '/';
      } catch (err) {
        setMsg(msg, String(err.message || err), false);
      }
    });
  }
})();
