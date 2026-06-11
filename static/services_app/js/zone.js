let map;
var set_center = { lat: 20.5937, lng: 78.9629 };
// var set_center = { lat: 0.0000, lng: 0.0000 };
var set_zoom = 5;
// console.log('set_center', set_center);
// console.log('set_zoom', set_zoom);
var citymap = [];
var markers = [];

var base_url = document.getElementById('api_header').value;

// Initialize and add the map
function initMapFromScript() {

    // Create a new StyledMapType object, passing it an array of styles,
    // and the name to be displayed on the map type control.
    const styledMapType = new google.maps.StyledMapType([
        { elementType: "geometry", stylers: [{ color: "#fdfbfb" }] },
        { elementType: "labels.text.fill", stylers: [{ color: "#444444" }] },

        {
            featureType: "administrative",
            elementType: "geometry.stroke",
            stylers: [{ color: "#dddddd" }],
        },
        {
            featureType: "administrative.land_parcel",
            elementType: "geometry.stroke",
            stylers: [{ color: "#666666" }],
        },
        {
            featureType: "administrative.land_parcel",
            elementType: "labels.text.fill",
            stylers: [{ color: "#CCCCCC" }],
        },
        {
            featureType: "landscape.natural",
            elementType: "geometry",
            stylers: [{ color: "#eeeeee" }],
        },
        {
            featureType: "poi",
            elementType: "geometry",
            stylers: [{ color: "#fc0a0a" }],
        },
        {
            featureType: "poi",
            elementType: "labels.text.fill",
            stylers: [{ color: "#CCCCCC" }],
        },
        {
            featureType: "poi.park",
            elementType: "geometry.fill",
            stylers: [{ color: "#CCCCCC" }],
        },
        {
            featureType: "poi.park",
            elementType: "labels.text.fill",
            stylers: [{ color: "#447530" }],
        },
        {
            featureType: "road",
            elementType: "geometry",
            stylers: [{ color: "#f5f1e6" }],
        },
        {
            featureType: "road.arterial",
            elementType: "geometry",
            stylers: [{ color: "#fdfcf8" }],
        },
        {
            featureType: "road.highway",
            elementType: "geometry",
            stylers: [{ color: "#d3cece" }],
        },
        {
            featureType: "road.highway",
            elementType: "geometry.stroke",
            stylers: [{ color: "#bcb8b8" }],
        },
        {
            featureType: "road.highway.controlled_access",
            elementType: "geometry",
            stylers: [{ color: "#aca8a8" }],
        },
        {
            featureType: "road.highway.controlled_access",
            elementType: "geometry.stroke",
            stylers: [{ color: "#d4d2d1" }],
        },
        {
            featureType: "road.local",
            elementType: "labels.text.fill",
            stylers: [{ color: "#e4d5cf" }],
        },
        {
            featureType: "transit.line",
            elementType: "geometry",
            stylers: [{ color: "#e9e8e5" }],
        },
        {
            featureType: "transit.line",
            elementType: "labels.text.fill",
            stylers: [{ color: "#8f7d77" }],
        },
        {
            featureType: "transit.line",
            elementType: "labels.text.stroke",
            stylers: [{ color: "#ebe3cd" }],
        },
        {
            featureType: "transit.station",
            elementType: "geometry",
            stylers: [{ color: "#dfd2ae" }],
        },
        {
            featureType: "water",
            elementType: "geometry.fill",
            stylers: [{ color: "#ffffff" }],
        },
        {
            featureType: "water",
            elementType: "labels.text.fill",
            stylers: [{ color: "#ffffff" }],
        },
    ],
        { name: "Styledmap" }
    );

    map = new google.maps.Map(document.getElementById("map"), {
        center: set_center,
        zoom: set_zoom,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            mapTypeIds: ["roadmap", "satellite", "hybrid", "terrain", "styled_map"],
        },
    });

    getMapData(map);

}
function getMapData() {
    //console.log("Voilaa...........................")
    // GET MAP DATA THROUGH AJAX
    $.ajax({
        url: `${base_url}/api/anchor/serve-map-coordinate/`,
        // data: request,
        dataType: "json",
        type: "GET"
    }).done(function (data) {
        // console.log('MAP DATA', data);
        if (data['status'] == 1) {
            citymap = data['data'][0]['circledata'];
            markers = data['data'][0]['markerdata'];
            cityradious = data['data'][0]['citis'];

        }
    });
}

// start of zone.js codes


// Updated marker creation (replace all google.maps.Marker instances)
function createAdvancedMarker(position, map, color) {
  return new google.maps.marker.AdvancedMarkerElement({
    position,
    map,
    content: buildPinElement(color)
  });
}

function buildPinElement(color) {
  const pin = document.createElement('div');
  pin.style.width = '20px';
  pin.style.height = '20px';
  pin.style.backgroundColor = color;
  pin.style.borderRadius = '50%';
  pin.style.border = '2px solid white';
  return pin;
}
/* ---------- Common utility to fetch JWT ---------- */
async function getJWT() {
  try {
    const { token } = await fetch('/zone/?token=true', { credentials: 'include' }).then(r => r.json());
    if (!token) throw new Error('Token missing');
    return token;
  } catch (err) {
    console.error('[JWT] Fetch failed:', err);
    throw err;
  }
}

/* ===================================================================
 *  ZONES page – fullscreen map logic  (final version)
 * ===================================================================*/
window.handleAddZoneClicked = async function () {
    if (window.zoneAddInitiated) return;  // prevent multiple triggers
        window.zoneAddInitiated = true;
  /* ---------- CONFIG ---------- */
  const ZOOM_THRESHOLD            = 6;
  const MAP_CENTER                = { lat: 22.3511148, lng: 78.6677428 };
  const STATE_CIRCLE_RADIUS_KM    = 180;
  const ANCHOR_RED                = '#d9534f';
  const ANCHOR_BLUE               = '#0d6efd';
  const ANCHOR_DOT_SCALE          = 10;     // ≈ 20 px round dot

  // ---------- SHOW mapModal instead of inline container ----------
    document.getElementById('originalMapCard').style.display = 'none';
    const modal = document.getElementById('mapModal');
    modal.style.display = 'flex';
    await new Promise(r => setTimeout(r, 100));     // allow layout
    const mapDiv = document.getElementById('expandedMap');


    let jwt;
    try {
        jwt = await getJWT();
    } catch {
        return;
    }

  /* ---------- FETCH anchor‑map‑coordinates ---------- */
  let stateRows = [], allAnchors = [];
    // ─── Fetch online anchors ─────────────────────────────
  let onlineIds = [];

  try {
    // Step 1: Get JWT token
    const tokenResp = await fetch('/zone/?token=true', { credentials: 'include' });
    const { token: jwt } = await tokenResp.json();

    // Step 2: Call the local user-anchor API with Bearer token
    const anchorResp = await fetch(`${base_url}/api/anchor/user-anchor/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${jwt}`,
        'Accept': 'application/json'
      },
      credentials: 'include'
    });

    const anchorJson = await anchorResp.json();

    // Step 3: Extract anchor IDs where is_online is true
    if (Array.isArray(anchorJson.anchor)) {
      onlineIds = anchorJson.anchor
        .filter(a => a.anchor_details?.[0]?.is_online)
        .map(a => +a.id);
    }
  } catch (e) {
    console.warn('[Zone] Could not fetch online anchors:', e);
  }
  // ────────────F──────────────────────────────────────────

  try {
    const raw = await fetch(
      `${base_url}/api/anchor/anchor-map-coordinates/`,
      { headers:{ Authorization:`Bearer ${jwt}` } }
    ).then(r => r.json());

    /* helper: collect anchors recursively */
    function collectAnchors(node) {
      const ids  = node.user_anchor_ids        || [];
      const lats = node.user_anchor_latitudes  || [];
      const lngs = node.user_anchor_longitudes || node.user_anchor_longitude || [];

      ids.forEach((id, i) => {
        const lat = Number(lats[i]), lng = Number(lngs[i]);
        if (isFinite(lat) && isFinite(lng)) {
          allAnchors.push({ id:+id, lat, lng });
        }
      });
      (node.children || []).forEach(collectAnchors);
    }

    const rootStates = raw.map_coodinets?.[0]?.children ?? [];
    rootStates.forEach(st => {
      collectAnchors(st);   // gather every anchor under this state
      stateRows.push({
        name  : st.state,
        count : +st.register_anchor_count || +st.regiser_anchor_count || 0,
        center: { lat:+st.center_latitude, lng:+st.center_longitude }
      });
    });

  } catch (e) {
    // console.error('[Zones] anchor-map fetch failed:', e);
    return;
  }

//   console.log(`[Zones] parsed ${stateRows.length} states, ${allAnchors.length} anchors`);

  /* ---------- CREATE / REUSE Google Map ---------- */
  let map;
  if (!window.expandedMap || !(window.expandedMap instanceof google.maps.Map)) {
    map = new google.maps.Map(mapDiv, { center: MAP_CENTER, zoom: 6 });
    window.expandedMap = map;
  } else {
    map = window.expandedMap;
    google.maps.event.trigger(map, 'resize');
    map.setCenter(MAP_CENTER);
    map.setZoom(6);
  }

  /* ---------- STATE overlays (circles + labels) ---------- */
    window.stateCircles = [];
    window.stateLabels = [];
  stateRows.forEach(st => {
    stateCircles.push(
      new google.maps.Circle({
        center       : st.center,
        radius       : STATE_CIRCLE_RADIUS_KM * 1000,
        strokeColor  : ANCHOR_RED,
        strokeOpacity: 0.8,
        strokeWeight : 1,
        fillColor    : ANCHOR_RED,
        fillOpacity  : 0.25,
        map          : null
      })
    );
    const label = new google.maps.Marker({
      position: st.center,
      icon    : { path: google.maps.SymbolPath.CIRCLE, scale: 0 },
      label   : { text:String(st.count), color:'#fff', fontSize:'14px', fontWeight:'bold' },
      map     : null
    });
    label.addListener('mouseover', () =>
      label.setLabel({ text: st.name, color:'#fff', fontSize:'12px', fontWeight:'bold' }));
    label.addListener('mouseout', () =>
      label.setLabel({ text: String(st.count), color:'#fff', fontSize:'14px', fontWeight:'bold' }));
    stateLabels.push(label);
  });

  /* ---------- ANCHOR pin markers (Google style) ---------- */
    const RED_PIN  = 'http://maps.google.com/mapfiles/ms/icons/red-dot.png';
    const GREEN_PIN = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png';

    const BLUE_PIN = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png';
    const selectedIds = [];  // <-- Add this line
    window.selectedAnchorIds = selectedIds;   // <-- expose globally

    const infoWindow = new google.maps.InfoWindow();

    let anchorMap = {};

    fetch(`${base_url}/api/common/anchor-locations/`, {
    headers: { Authorization: `Bearer ${jwt}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data && data.data) {
          anchorMap = data.data.reduce((acc, item) => {
            acc[item.id] = item.anchor_id__anchor_name;
            return acc;
          }, {});
          // console.log("Anchor map ready:", anchorMap);
        }
      })
      .catch(err => console.error("Error fetching anchor data:", err));

   window.anchorMarkers = allAnchors.map(a => {
  const isOnline = onlineIds.includes(a.id);
  const iconUrl  = isOnline ? GREEN_PIN : RED_PIN;

  const marker = new google.maps.Marker({
    position: { lat: a.lat, lng: a.lng },
    icon    : iconUrl,
    map     : null
  });

  marker.isOnline = isOnline; // 🟢 store status for toggle
  marker.anchorId = a.id;  // store anchor id
  marker.details  = null;  // cache spot for API data


    marker.addListener('click', () => {
        const idx = selectedIds.indexOf(a.id);
        if (idx > -1) {
        selectedIds.splice(idx, 1);
        marker.setIcon(marker.isOnline ? GREEN_PIN : RED_PIN);
        // console.log(`[Anchor] Deselected: ${a.id} | Current selection:`, [...selectedIds]);
        } else {
        selectedIds.push(a.id);
        marker.setIcon(BLUE_PIN);
        // console.log(`[Anchor] Selected: ${a.id} | Current selection:`, [...selectedIds]);

        }
        // console.log('clicked anchor id:', a.id, '| selected:', selectedIds);
    });

     marker.addListener("mouseover", () => {
      const anchorName = anchorMap[a.id] || "Unknown";
      const infoContent = `<strong>Anchor:</strong> ${anchorName}`;
      infoWindow.setContent(infoContent);
      infoWindow.open(map, marker);
    });

    marker.addListener("mouseout", () => {
      infoWindow.close();
    });


    return marker;
    });


  let hasRendered = false;

    function render() {
    if (hasRendered) {
        console.log('[Zones] re-rendered on zoom', map.getZoom());
    } else {
        console.log('[Zones] initial render', map.getZoom());
        hasRendered = true;
    }

    const showAnchors = map.getZoom() > ZOOM_THRESHOLD;
    stateCircles.forEach(c => c.setMap(showAnchors ? null : map));
    stateLabels .forEach(l => l.setMap(showAnchors ? null : map));
    anchorMarkers.forEach(m => m.setMap(showAnchors ? map  : null));

    console.log('[Zones] zoom', map.getZoom(),
        '→ placed', anchorMarkers.filter(m => m.getMap() === map).length, 'anchor dots');
    }

    map.addListener('zoom_changed', render);
    render();  // initial render



};
/* ------------------------------------------------------------------
 *  "Create Zone" modal + submit (refined version)
 * ------------------------------------------------------------------*/
window.handleCreateZoneClicked = async function () {
  const modal   = document.getElementById('zoneCreateModal');
  const nameInp = document.getElementById('zoneNameInput');
  const listDiv = document.getElementById('selectedAnchorList');
  const saveBtn = document.getElementById('zoneSaveBtn');
  const cancel  = document.getElementById('zoneCancelBtn');

  const selected = [...(window.selectedAnchorIds || [])];
  console.log("[CreateZone] Anchors currently selected (before modal):", selected);

  if (!selected.length) {
    Swal.fire("Select anchors", "Choose at least one anchor.", "warning");
    return;
  }

  let jwt;
  try {
    jwt = await getJWT();
  } catch {
    return;
  }

  /* ---------- Call external API (anchor-request) ---------- */
  let anchorResponse;
  try {
    anchorResponse = await fetch(`${base_url}/api/anchor/anchor-request/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${jwt}`,
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ anchor_ids: selected })
    }).then(r => r.json());

    console.log("[CreateZone] Anchor request response:", anchorResponse);

  } catch (err) {
    console.error("[CreateZone] Anchor request failed:", err);
    Swal.fire("API Error", "Failed to fetch anchor info. Try again.", "error");
    return;
  }

  listDiv.innerHTML = '';
  if (Array.isArray(anchorResponse.anchor_details)) {
    anchorResponse.anchor_details.forEach((item, i) => {
  const name = item.anchor.anchor_name;
  const badge = document.createElement('span');
  badge.textContent = name;
  badge.dataset.anchorId = selected[i];  // ✅ correctly indexed
  badge.className = 'badge rounded-pill bg-primary me-1';
  listDiv.appendChild(badge);
});


  } else {
    selected.forEach(id => {
      const badge = document.createElement('span');
      badge.textContent = id;
      badge.dataset.anchorId = id;  // <-- Also here
      badge.className = 'badge rounded-pill bg-secondary me-1';
      listDiv.appendChild(badge);
    });
  }

  nameInp.value = '';
  modal.style.display = 'flex';

  if (!saveBtn.dataset.bound) {
    saveBtn.addEventListener('click', async () => {
      const zoneName = nameInp.value.trim();
      if (!zoneName) {
        Swal.fire("Missing name", "Please enter a zone name.", "warning");
        return;
      }

      const csrf = document.querySelector('#csrf input')?.value;
      if (!csrf) {
        Swal.fire("Error", "CSRF token not found.", "error");
        return;
      }

      // ✅ Get anchor IDs directly from DOM
      const badgeEls = listDiv.querySelectorAll('span[data-anchor-id]');
      const anchorIds = Array.from(badgeEls).map(el => +el.dataset.anchorId);

      console.log("[CreateZone] Final anchor IDs to submit:", anchorIds);

      if (!anchorIds.length) {
        Swal.fire("Error", "No anchor selected to create a zone.", "error");
        return;
      }

      saveBtn.disabled = true;

      const fd = new FormData();
      fd.append('zone', zoneName);
      anchorIds.forEach(id => fd.append('anchor_list', id));

      try {
        const res = await fetch('/zone/', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrf },
          body: fd,
          credentials: 'include'
        });
        const data = await res.json();

        if (data.status === 1) {
            // 1) Close the “Add Zone” popup (zoneCreateModal)
            modal.style.display = 'none';
            // 2) Close the map modal (mapModal)
            document.getElementById('mapModal').style.display = 'none';

            // 3) Show success popup
            Swal.fire("Created!", "Zone has been created.", "success")
                .then(() => {
                // 4) Finally reload (so that the new zone appears in the table)
                location.reload();
                });
        } else {
          Swal.fire("Error", data.message || "Zone creation failed.", "error");
        }

      } catch (err) {
        console.error('[CreateZone] Zone creation failed:', err);
        Swal.fire("Error", "Network or server error while creating zone.", "error");
      } finally {
        saveBtn.disabled = false;
      }
    });

    cancel.addEventListener('click', () => {
      modal.style.display = 'none';
    });

    saveBtn.dataset.bound = '1';
  }
};



/* -----------------------------------------
 * Newly Added Code (Do NOT modify above)
 * -----------------------------------------*/

// 1) Ensure both modals are injected into <body>
function _ensureModalsExist() {
  // a) Map Modal
  if (!document.getElementById('mapModal')) {
    const mapModalHTML = `
      <div id="mapModal" style="
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          position: relative;
          width: 90%;
          height: 90%;
          background: white;
          border-radius: 8px;
          overflow: hidden;
        ">
          <div class="position-absolute top-0 end-0 m-3 zindex-tooltip">
            <button id="closeExpandedMap" class="btn btn-danger btn-sm me-2">Back</button>
            <button id="expandedCreateZoneBtn" class="btn btn-success btn-sm">Create Zone</button>
          </div>
          <div id="expandedMap" style="width: 100%; height: 100%;"></div>
        </div>
      </div>`;
    document.body.insertAdjacentHTML('beforeend', mapModalHTML);
  }

  // b) Zone Creation Modal
  if (!document.getElementById('zoneCreateModal')) {
    const zoneCreateHTML = `
      <div id="zoneCreateModal" style="
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 3000;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          background: white;
          border-radius: 10px;
          padding: 20px;
          width: 280px;
          box-shadow: 0 4px 15px rgba(0,0,0,0.2);
          font-family: sans-serif;
        ">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <strong style="color: #2c3e50;">Add Zone</strong>
            <button id="zoneCancelBtn" style="border: none; background: none; font-size: 18px;">×</button>
          </div>
          <label style="font-size: 14px; margin-bottom: 4px;">Zone Name</label>
          <input id="zoneNameInput" class="form-control mb-3" placeholder="Zone name" />
          <div id="selectedAnchorList" style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px;"></div>
          <button id="zoneSaveBtn" class="btn btn-primary btn-sm" style="width: 100%;">Save</button>
        </div>
      </div>`;
    document.body.insertAdjacentHTML('beforeend', zoneCreateHTML);
  }
}

// 2) Public function: call this to open the “Add Zone” modal + map
window.openZoneModal = function() {
  // a) Inject modals (if not already there)
  _ensureModalsExist();

  // b) Bind “Back” and “Create Zone” listeners once
  if (!document.getElementById('openZoneBound')) {
    // i) “Back” button inside #mapModal
    document.getElementById('closeExpandedMap').addEventListener('click', () => {
      document.getElementById('mapModal').style.display = 'none';
      // Show prompt card again (if present)
      const prompt = document.getElementById('zonePromptCard');
      if (prompt) prompt.style.display = 'block';
      // Reset state
      window.zoneAddInitiated = false;
      window.selectedAnchorIds = [];
      // Clear markers/circles/labels
      if (window.expandedMap) {
        if (Array.isArray(window.anchorMarkers)) {
          window.anchorMarkers.forEach(m => m.setMap(null));
          window.anchorMarkers = [];
        }
        if (Array.isArray(window.stateCircles)) {
          window.stateCircles.forEach(c => c.setMap(null));
          window.stateCircles = [];
        }
        if (Array.isArray(window.stateLabels)) {
          window.stateLabels.forEach(l => l.setMap(null));
          window.stateLabels = [];
        }
      }
    });

    // ii) “Create Zone” button inside #mapModal
    document.getElementById('expandedCreateZoneBtn').addEventListener('click', () => {
      window.handleCreateZoneClicked();
    });

    // iii) Mark that we bound these only once
    const marker = document.createElement('div');
    marker.id = 'openZoneBound';
    marker.style.display = 'none';
    document.body.appendChild(marker);
  }



   // **Always hide the Zone‐Creation popup first** (in case it was left open)
   document.getElementById('zoneCreateModal').style.display = 'none';

  // c) Finally, kickoff the existing map logic
  window.handleAddZoneClicked();
};

// 3) Also bind “×” inside #zoneCreateModal to close only that modal
document.addEventListener('click', function(e) {
  if (e.target && e.target.id === 'zoneCancelBtn') {
    const modal = document.getElementById('zoneCreateModal');
    if (modal) modal.style.display = 'none';
  }
});

// end of zone.js codes