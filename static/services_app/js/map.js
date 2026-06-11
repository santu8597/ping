
// eslint-disable no-undef
let map;
var set_center = { lat: 20.5937, lng: 78.9629 };
// var set_center = { lat: 0.0000, lng: 0.0000 };
var set_zoom = 5;
// console.log('set_center', set_center);
// console.log('set_zoom', set_zoom);
var citymap = [];
var markers = [];
var check_latency_marker_data = [];
var check_your_latency_circle_data = [];
var kolkata_latency = 0;
var mumbai_latency = 0;
var mohali_latency = 0;
var guwahati_latency = 0;
var bengaluru_latency = 0;
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

function setMarkers(map, markers) {
    //console.log('Marker Data', markers);
    for (let i = 0; i < markers.length; i++) {
        const loca = markers[i];
        new google.maps.Marker({
            position: { lat: parseFloat(loca['latitude']), lng: parseFloat(loca['longitude']) },
            map,
            title: loca['address'] + ', Pin - ' + loca['postal'] + ', Service provider - ' + loca['org'],
            zIndex: loca[3],
        });
    }
}



function setMapCenter(location) {
    // console.log(location)
    // set_center = center;
    // set_zoom = zoom;
    initMap();
    //console.log('set_center', center);
    // console.log('set_zoom', zoom);
    map = new google.maps.Map(document.getElementById("map"), {
        center: set_center,
        zoom: set_zoom,
    });
    getFilterMapData(map, location)
    // areaCircle(map, citymap);
    // setMarkers(map, markers);
}

function getFilterMapData(map, request) {
    //console.log(request)
    // GET MAP DATA THROUGH AJAX
    var myObj = {
        "serve_location": request
    };
    $.ajax({

        url: `${base_url}/api/anchor/serve-map-coordinate/`,
        type: 'post',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(myObj)
    }).done(function (data) {
        // console.log('MAP DATA', data);
        if (data['status'] == 1) {
            citymap = data['data'][0]['circledata'];
            // console.log(citymap.length);
            markers = data['data'][0]['markerdata'];
            // console.log(markers);
            areaCircle(map, citymap);
            setMarkers(map, markers);
        }
    });
}




function areaCircle(map, citymap) {
    // console.log('FFFFFFF', Object.keys(citymap).length);
    // Construct the circle for each value in citymap.
    // Note: We scale the area of the circle based on the count.
    var bound = new google.maps.LatLngBounds();
    if (Object.keys(citymap).length > 0) {
        Object.keys(citymap).forEach(key => {
            let keyname = key;
            let value = citymap[key];
            let var_strokeColor = "#FF0000";
            let var_fillColor = "#FF0000";
            // console.log('keyname', keyname);
            // console.log('value', value);
            let bound = new google.maps.LatLngBounds();
            // console.log('bound', bound);
            let count = 0;
            for (i = 0; i < value.length; i++) {
                bound.extend(new google.maps.LatLng(value[i]['lat'], value[i]['lng']));
                // OTHER CODE
                count = count + value[i]['count']
            }
            if (count < 10 && count > 0) {
                var_strokeColor = "#FF0000";
                var_fillColor = "#FF0000";
            }
            if (count < 30 && count > 11) {
                var_strokeColor = "#FF9333";
                var_fillColor = "#FF9333";
            }
            if (count < 50 && count > 31) {
                var_strokeColor = "#FFE033";
                var_fillColor = "#FFE033";
            }
            if (count < 1000 && count > 51) {
                var_strokeColor = "#307B02";
                var_fillColor = "#307B02";
            }
            // console.log('count', j, count);
            // Add the circle for this city to the map.
            const cityCircle = new google.maps.Circle({
                strokeColor: var_strokeColor,
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: var_fillColor,
                fillOpacity: 0.35,
                map,
                title: keyname,
                // center: citymap[city].center,
                // radius: Math.sqrt(citymap[city].count) * 100,
                // center: { lat: parseFloat(city['latitude']), lng: parseFloat(city['longitude']) },
                center: bound.getCenter(),
                radius: Math.sqrt(30) * 5000,
            });

            google.maps.event.addListener(cityCircle, 'click', function () {

                let base64string = b64EncodeUnicode(cityCircle.title);


                $.ajax({

                    url: `${base_url}/api/anchor/city-latency/` + base64string + `/`,
                    dataType: "json",
                    type: "GET"
                }).done(function (data) {
                    // console.log('MAP DATA', data);
                    // console.log(data);
                    if (data['status'] == 1) {
                        if (data['data'].length > 0) {
                            var latency_table = '<div id="content"><div id="siteNotice"></div><h6 id="firstHeading" class="firstHeading">SERVER AVERAGE LATENCY</h6><table class="table check-table table-striped table-bordered" style="margin-bottom: 0"><thead><tr><th scope="col"> Location</th><th scope="col">Average Latency</th></tr></thead><tbody>';
                            data['data'].forEach(element => {
                                // console.log(element);
                                latency_table += '<tr>';
                                latency_table += '<td>' + element.vartual_anchor_location + '</td><td>' + element.avg_latency.toFixed(3) + '</td>';
                                latency_table += '</tr>';
                            });
                            latency_table += '</tbody></table></div>';
                            let infowindow = new google.maps.InfoWindow({
                                content: latency_table
                            });
                            infowindow.setPosition(cityCircle.getCenter());
                            infowindow.open(map);
                        }
                    }
                });
            });
        });

    }
}




let allowedAnchors = [];
//let PDM_integrated_list = ['IN-V2-07','IN-V2-11', 'IN-V2-10', 'IN-V2-12', 'CL-V2-001', 'CL-V2-002']
let PDM_integrated_list = ['IN-V2-07','IN-V2-11','CL-V2-001']

// Function to extract anchor names from the dropdown
function fetchAllowedAnchorsFromDropdown() {
    allowedAnchors = []; // Clear previous data

    let anchorDropdown = document.getElementById("anchor"); // Get the dropdown element

    for (let i = 0; i < anchorDropdown.options.length; i++) {
        let anchorText = anchorDropdown.options[i].text.trim(); // Get text inside <option>

        if (anchorText !== "--SELECT ANCHOR--") { // Ignore placeholder
            let anchorName = anchorText.split("(")[0].trim(); // Extract just the name
            allowedAnchors.push(anchorName);
        }
    }

   // console.log("Allowed Anchors from Dropdown:", allowedAnchors);
}

// Fetch allowed anchors after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    fetchAllowedAnchorsFromDropdown(); // Populate allowedAnchors from the dropdown
    AnchorLocationSet();
});

function setAnchorMarkers(map, markers) {
    //console.log('Marker Data', markers);

    let infoWindow = new google.maps.InfoWindow(); // Reusable info window

    for (let i = 0; i < markers.length; i++) {
        const loca = markers[i];

        // Set custom icon based on IP type
        let newIcon = '';

        // Check if the anchor name exists in the allowed list
        let isAllowed = allowedAnchors.includes(loca['anchor_id__anchor_name']);
        // Set custom icon based on conditions
        if (!isAllowed) {
            newIcon = '../static/services_app/img/grey.svg'; // If not allowed, set to grey
        } else if (PDM_integrated_list.includes(loca['anchor_id__anchor_name'])) {
            newIcon = '../static/services_app/img/green.svg'; // If allowed and in PDM list, set to green
        } else {
            newIcon = '../static/services_app/img/orange.svg'; // If allowed but not in PDM list, set to orange
        }

        // Create a marker
        let marker = new google.maps.Marker({
            position: { lat: parseFloat(loca['latitude']), lng: parseFloat(loca['longitude']) },
            map,
            icon: newIcon,
            title: loca['anchor_id__anchor_name'],
            zIndex: loca[3],
        });

        // Create a div element for the InfoWindow content
        let infoDiv = document.createElement("div");
        infoDiv.style.fontSize = "14px";
        infoDiv.style.padding = "5px";

        // Add anchor details
        infoDiv.innerHTML = `
            <strong>Name:</strong> ${loca['anchor_id__anchor_name']} <br>
            <strong>Location:</strong> ${loca['location']} <br>
            <strong>Coordinates:</strong> (${loca['latitude']}, ${loca['longitude']}) <br>
        `;

        // If the name is allowed, create a button dynamically
        if (isAllowed) {
            // --- replace single button with these three ---
const commands = [
  { key: "dns",         label: "Execute DNS Query",     colorClass: "btn-success" },
  { key: "ping",        label: "Execute Ping",          colorClass: "btn-warning" },
  { key: "traceroute",  label: "Execute Traceroute",    colorClass: "btn-danger" }
];

commands.forEach(cmd => {
  const btn = document.createElement("button");
  btn.className = `btn ${cmd.colorClass} btn-sm mt-2 me-2`;
  btn.innerText = cmd.label;
  btn.onclick = () => {
    const params = new URLSearchParams({
      anchor_name: loca.anchor_id__anchor_name
    });
    window.location.href = `/${cmd.key}-command/?${params.toString()}`;
  };
  infoDiv.appendChild(btn);
});


        }

        // Add click event to marker
        marker.addListener("click", function () {
            infoWindow.setContent(infoDiv);
            infoWindow.open(map, marker);
        });
    }
}

// Function triggered when button is clicked
function handleButtonClick(anchorName, anchorId) {
    // Set the anchor name in the modal input field
    document.getElementById("anchor_name").value = anchorName;

    // Set the anchor ID in the hidden input field
    document.getElementById("anchor_id").value = anchorId;

    // Show the modal using Bootstrap
    let anchorModal = new bootstrap.Modal(document.getElementById("anchorModal"));
    anchorModal.show();
}


function AnchorLocationSet() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: set_center,
        zoom: set_zoom,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            mapTypeIds: ["roadmap", "satellite", "hybrid", "terrain", "styled_map"],
        },
    });
    //Associate the styled map with the MapTypeId and set it to display.
    // map.mapTypes.set("styled_map", styledMapType);
    // map.setMapTypeId("styled_map");
    $.ajax({
        // headers: { "Content-Type": "application/json", "X-IIFON-API-KEY": "d450c717-57af-4172-ace1-59055ddb7e4a" },
        // url: 'http://localhost:8087/api/common/anchor-locations/',
        // url: "https://vizdata.v0.aior.in/api/smc/",
        //url: "https://apivizv0.aior.in/api/common/anchor-locations/",
        url: `${base_url}/api/common/anchor-locations/`,
        type: 'get',
        dataType: 'json',
        contentType: 'application/json',
        // data: JSON.stringify(myObj)
    }).done(function (data) {
        //console.log('MAP DATA', data);
        if (data['status'] == 1) {
            setAnchorMarkers(map, data['data']);
        }
    });
}




		//Added on 14-03-2025
function setIntegratedAnchorMarkers(map, markers) {
    console.log('Filtered Marker Data', markers);

    let infoWindow = new google.maps.InfoWindow(); // Reusable info window
    
    for (let i = 0; i < markers.length; i++) {
        const loca = markers[i];
        let isAllowed = allowedAnchors.includes(loca['anchor_id__anchor_name']);

        // Check if the anchor name is in PDM_integrated_list
        if (!PDM_integrated_list.includes(loca['anchor_id__anchor_name']) || !isAllowed) {
            continue; // Skip markers that are not in PDM_integrated_list
        }
     
        // Set the green icon (since we are only showing PDM integrated markers)
        let newIcon = '../static/PDM_app/img/green.svg';

        // Create a marker
        let marker = new google.maps.Marker({
            position: { lat: parseFloat(loca['latitude']), lng: parseFloat(loca['longitude']) },
            map,
            icon: newIcon,
            title: loca['anchor_id__anchor_name'],
            zIndex: loca[3],
        });

        // Create a div element for the InfoWindow content
        let infoDiv = document.createElement("div");
        infoDiv.style.fontSize = "14px";
        infoDiv.style.padding = "5px";

        // Add anchor details
        infoDiv.innerHTML = `
            <strong>Name:</strong> ${loca['anchor_id__anchor_name']} <br>
            <strong>Location:</strong> ${loca['location']} <br>
            <strong>Coordinates:</strong> (${loca['latitude']}, ${loca['longitude']}) <br>
        `;

        // Create a button for the allowed marker
        let button = document.createElement("button");
        button.className = "btn btn-primary btn-sm mt-2";
        button.innerText = "Execute Query";
        button.onclick = function () {
            handleButtonClick(loca['anchor_id__anchor_name'], loca['id']);
        };

        infoDiv.appendChild(button); // Append button to info window content

        // Add click event to marker
        marker.addListener("click", function () {
            infoWindow.setContent(infoDiv);
            infoWindow.open(map, marker);
        });
    }
}


