(function () {
  let map = null;
  let marker = null;
  let directionsService = null;
  let directionsRenderer = null;

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
      throw new Error(typeof data === 'object' && data && data.detail ? JSON.stringify(data.detail) : r.statusText);
    }
    return data;
  }

  function cents(usd) {
    return Math.round(Number(usd) * 100);
  }

  async function refreshRides() {
    const el = document.getElementById('rides-out');
    try {
      const rides = await api('/api/rides/open');
      el.textContent = JSON.stringify(rides, null, 2);
    } catch (e) {
      el.textContent = 'Could not load open rides (are you logged in as a driver?): ' + e.message;
    }
  }

  window.initDriverMap = function () {
    const el = document.getElementById('map');
    if (!window.google || !google.maps) {
      el.textContent = 'Maps failed to load.';
      return;
    }
    map = new google.maps.Map(el, {
      center: { lat: 40.7128, lng: -74.006 },
      zoom: 12,
    });
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({ map });
    marker = new google.maps.Marker({ map, title: 'You' });

    if (navigator.geolocation) {
      navigator.geolocation.watchPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          const loc = { lat, lng };
          marker.setPosition(loc);
          map.panTo(loc);
          api('/api/driver/location', {
            method: 'POST',
            body: JSON.stringify({ lat, lng }),
          }).catch(() => {});
        },
        () => {},
        { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 },
      );
    }

    document.getElementById('btn-bid').onclick = async () => {
      const id = document.getElementById('ride-id').value;
      const fareUsd = document.getElementById('fare-usd').value;
      if (!id) return alert('Ride ID');
      try {
        await api(`/api/rides/${id}/bids`, {
          method: 'POST',
          body: JSON.stringify({ fare_cents: cents(fareUsd) }),
        });
        await refreshRides();
        alert('Bid placed');
      } catch (e) {
        alert(e.message);
      }
    };

    document.getElementById('btn-start').onclick = async () => {
      const id = document.getElementById('ride-id').value;
      if (!id) return alert('Ride ID');
      try {
        await api(`/api/rides/${id}/start`, { method: 'POST', body: '{}' });
        alert('Started');
      } catch (e) {
        alert(e.message);
      }
    };

    document.getElementById('btn-done').onclick = async () => {
      const id = document.getElementById('ride-id').value;
      if (!id) return alert('Ride ID');
      try {
        await api(`/api/rides/${id}/complete`, { method: 'POST', body: '{}' });
        alert('Completed');
      } catch (e) {
        alert(e.message);
      }
    };

    setInterval(refreshRides, 8000);
    refreshRides();
  };

  // If maps script skipped (no API key), still poll rides for testing
  if (!document.querySelector('script[src*="maps.googleapis.com"]')) {
    setInterval(refreshRides, 8000);
    refreshRides();
  }
})();
