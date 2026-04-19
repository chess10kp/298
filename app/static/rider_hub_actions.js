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

  function reloadParent() {
    try {
      if (window.parent && window.parent !== window) window.parent.location.reload();
    } catch (_) {
      /* cross-origin parent */
    }
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
      setMsg(msg, 'Creating…', null);
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
        const ride = await api('/api/rides', { method: 'POST', body: JSON.stringify(body) });
        setMsg(msg, `Ride #${ride.id} created.`, true);
        reloadParent();
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
        const ride = await api(`/api/rides/${encodeURIComponent(id)}/cancel`, {
          method: 'POST',
          body: '{}',
        });
        setMsg(msg, `Ride #${ride.id} cancelled (${ride.status}).`, true);
        reloadParent();
      } catch (err) {
        setMsg(msg, String(err.message || err), false);
      }
    });
  }

  const logoutBtn = document.getElementById('rider-hub-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      if (!msg) return;
      setMsg(msg, 'Signing out…', null);
      try {
        const r = await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
        if (!r.ok) throw new Error(r.statusText);
        window.top.location.href = '/login';
      } catch (err) {
        setMsg(msg, String(err.message || err), false);
      }
    });
  }
})();
