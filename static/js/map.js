// Global variables
let map;
let markers = [];
let activeInfoWindow = null;

// Initialize the map
function initMap() {
    // Default center (can be customized)
    const defaultCenter = { lat: 25.276987, lng: 55.296249 }; // Dubai
    
    // Create the map
    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 3,
        styles: [
            { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
        ]
    });
    
    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                };
                
                // Center map on user's location
                map.setCenter(userLocation);
                map.setZoom(10);
            },
            () => {
                console.log("Error: The Geolocation service failed.");
            }
        );
    } else {
        console.log("Error: Your browser doesn't support geolocation.");
    }
    
    // Add markers for all locations
    if (typeof locations !== 'undefined' && locations.length > 0) {
        addMarkersToMap(locations);
    }
    
    // Add custom controls
    addMapControls();
}

// Function to add all markers to the map
function addMarkersToMap(locations) {
    // Clear existing markers
    clearMarkers();
    
    // Add markers for each location
    locations.forEach(location => {
        addMarker(location);
    });
    
    // Fit map bounds to markers if there are any
    if (markers.length > 0) {
        fitMapToMarkers();
    }
}

// Function to add a single marker
function addMarker(location) {
    const position = { lat: location.lat, lng: location.lng };
    
    // Create marker
    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: location.name,
        animation: google.maps.Animation.DROP,
        id: location.id
    });
    
    // Create info window content
    const contentString = `
        <div class="info-window">
            <h5>${location.name}</h5>
            <p class="text-muted">${location.category}</p>
            <p>${location.description}</p>
            <div class="d-flex justify-content-end">
                <a href="/edit/${location.id}" class="btn btn-sm btn-outline-primary me-2">Edit</a>
                <button class="btn btn-sm btn-outline-danger delete-location-btn" data-id="${location.id}" data-name="${location.name}">Delete</button>
            </div>
        </div>
    `;
    
    // Create info window
    const infoWindow = new google.maps.InfoWindow({
        content: contentString,
        maxWidth: 300
    });
    
    // Add click event to marker
    marker.addListener("click", () => {
        // Close any open info windows
        if (activeInfoWindow) {
            activeInfoWindow.close();
        }
        
        // Open this info window
        infoWindow.open(map, marker);
        activeInfoWindow = infoWindow;
        
        // Add event listener to delete button inside info window
        google.maps.event.addListenerOnce(infoWindow, 'domready', () => {
            document.querySelector('.delete-location-btn').addEventListener('click', function() {
                const locationId = this.dataset.id;
                const locationName = this.dataset.name;
                
                document.getElementById('delete-location-name').textContent = locationName;
                document.getElementById('delete-form').action = `/delete/${locationId}`;
                
                const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
                deleteModal.show();
                
                // Close the info window
                infoWindow.close();
            });
        });
    });
    
    // Store the marker
    markers.push(marker);
}

// Function to clear all markers
function clearMarkers() {
    markers.forEach(marker => {
        marker.setMap(null);
    });
    markers = [];
}

// Function to fit the map to show all markers
function fitMapToMarkers() {
    const bounds = new google.maps.LatLngBounds();
    markers.forEach(marker => {
        bounds.extend(marker.getPosition());
    });
    map.fitBounds(bounds);
    
    // Don't zoom in too far
    const zoom = map.getZoom();
    if (zoom > 15) {
        map.setZoom(15);
    }
}

// Function to add custom controls to the map
function addMapControls() {
    // Create a custom control for recenter and zoom out
    const centerControlDiv = document.createElement("div");
    centerControlDiv.classList.add("map-control");
    centerControlDiv.innerHTML = `
        <button class="btn btn-dark btn-sm map-control-btn" title="Fit to all locations">
            <i class="fas fa-expand-arrows-alt"></i>
        </button>
    `;
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(centerControlDiv);
    
    // Add click event to the control
    centerControlDiv.querySelector('button').addEventListener("click", () => {
        if (markers.length > 0) {
            fitMapToMarkers();
        }
    });
}

// Function to center the map on a specific location
function centerMap(lat, lng, locationId) {
    const position = { lat: lat, lng: lng };
    map.setCenter(position);
    map.setZoom(15);
    
    // Find and open the info window for this marker
    const marker = markers.find(m => m.id === locationId);
    if (marker) {
        google.maps.event.trigger(marker, 'click');
    }
}

// Function to update markers on the map
function updateMarkers(locations) {
    addMarkersToMap(locations);
}
