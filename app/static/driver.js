(function () {
  let map = null;
  let marker = null;
  let directionsService = null;
  let directionsRenderer = null;
  let rideMarkers = [];
  let infoWindow = null;

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

  function clearRideMarkers() {
    rideMarkers.forEach((m) => m.setMap(null));
    rideMarkers = [];
  }

  async function refreshRides() {
    const el = document.getElementById('rides-out');
    try {
      const rides = await api('/api/rides/open');
      window.__lastOpenRides = rides;
      el.textContent = JSON.stringify(rides, null, 2);

      if (!map || !window.google || !google.maps) return;

      clearRideMarkers();
      if (infoWindow) {
        infoWindow.close();
        infoWindow = null;
      }

      const bounds = new google.maps.LatLngBounds();
      rides.forEach((ride) => {
        const pos = { lat: ride.pickup_lat, lng: ride.pickup_lng };
        const m = new google.maps.Marker({
          position: pos,
          map,
          title: `Pickup · ride #${ride.id}`,
          label: String(ride.id),
        });
        m.addListener('click', () => {
          document.getElementById('ride-id').value = String(ride.id);
          if (!infoWindow) infoWindow = new google.maps.InfoWindow();
          const esc = (s) =>
            String(s)
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/"/g, '&quot;');
          infoWindow.setContent(
            `<div style="font-family:system-ui,sans-serif;max-width:220px;line-height:1.4">` +
              `<strong>Ride #${esc(ride.id)}</strong><br>` +
              `Status: ${esc(ride.status)}<br>` +
              `<button type="button" id="iw-use">Use for bid / start / complete</button>` +
              `</div>`,
          );
          infoWindow.open(map, m);
          google.maps.event.addListenerOnce(infoWindow, 'domready', () => {
            const b = document.getElementById('iw-use');
            if (b)
              b.onclick = () => {
                document.getElementById('ride-id').value = String(ride.id);
                infoWindow.close();
              };
          });
        });
        rideMarkers.push(m);
        bounds.extend(pos);
      });

      const you = marker && marker.getPosition();
      if (you) bounds.extend(you);
      if (rides.length > 0) {
        map.fitBounds(bounds);
      }
    } catch (e) {
      el.textContent =
        'Could not load open rides (are you logged in as a driver?): ' + e.message;
    }
  }

  window.routeToPickup = function () {
    const id = parseInt(document.getElementById('ride-id').value, 10);
    const rides = window.__lastOpenRides || [];
    const ride = rides.find((r) => r.id === id);
    if (!ride || !directionsService || !directionsRenderer || !marker) {
      if (!ride) alert('Select a ride (marker or ID) first.');
      return;
    }
    const origin = marker.getPosition();
    if (!origin) {
      alert('Waiting for your GPS position…');
      return;
    }
    directionsService.route(
      {
        origin,
        destination: { lat: ride.pickup_lat, lng: ride.pickup_lng },
        travelMode: google.maps.TravelMode.DRIVING,
      },
      (res, status) => {
        if (status === 'OK') directionsRenderer.setDirections(res);
        else alert('Directions failed: ' + status);
      },
    );
  };

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
        await refreshRides();
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
        await refreshRides();
      } catch (e) {
        alert(e.message);
      }
    };

    const btnRoute = document.getElementById('btn-route');
    if (btnRoute) btnRoute.onclick = () => window.routeToPickup();

    setInterval(refreshRides, 8000);
    refreshRides();
  };

  function attachControlsWithoutMap() {
    const bid = document.getElementById('btn-bid');
    if (!bid || bid.dataset.wired === '1') return;
    bid.dataset.wired = '1';
    bid.onclick = async () => {
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
        await refreshRides();
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
        await refreshRides();
      } catch (e) {
        alert(e.message);
      }
    };
    const btnRoute = document.getElementById('btn-route');
    if (btnRoute)
      btnRoute.onclick = () =>
        alert('Route to pickup requires GOOGLE_MAPS_API_KEY and the map to load.');
  }

  if (!document.querySelector('script[src*="maps.googleapis.com"]')) {
    setInterval(refreshRides, 8000);
    refreshRides();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', attachControlsWithoutMap);
    } else {
      attachControlsWithoutMap();
    }
  }
})();
