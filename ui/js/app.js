/**
 * Gas Station Finder - Main Application
 * Phase 2: Core functionality with API integration
 */

// ===========================
// Application State
// ===========================

const state = {
    map: null,
    markers: [],
    clickMarker: null,
    currentLocation: null,
    radius: 10,
    lastSearch: null,
    isLoading: false
};

// ===========================
// Configuration
// ===========================

// Use empty string for relative URLs (works both locally and in production)
// When deployed, requests will go to the same domain as the UI
const API_BASE_URL = '';
const API_ENDPOINTS = {
    nearby: '/api/nearby'
};

// Brand logo configuration
// Maps brand names (normalized) to their logo filenames
const BRAND_LOGOS = {
    'bp': 'bp.png',
    'pieprzyk': 'pieprzyk.png',
    'slovnaft': 'slovnaft.png',
    'watis': 'watis.png',
    'leclerc': 'leclerc.png',
    'lotos': 'lotos.png',
    'uniwar': 'uniwar.png',
    'avia': 'avia.png',
    'orlen': 'orlen.png',
    'auchan': 'auchan.png',
    'moya': 'moya.png',
    'bliska': 'bliska.png',
    'mol': 'mol.png',
    'shell': 'shell.png',
    'huzar': 'huzar.png',
    'circle_k': 'circle_k.png',
    'aral': 'aral.png',
    'carrefour': 'carrefour.png',
    'amic': 'amic.png',
    'tesco': 'tesco.png',
    // Brands without logos will use fallback
    'oktan': null,
    'wadex': null,
    'intermarche': null,
    'olkop': null,
    'inna': null
};

// Fallback logo for generic stations
const FALLBACK_LOGO = 'station_general.png';

// Cache for Leaflet icon objects (performance optimization)
const iconCache = {};

// ===========================
// API Functions
// ===========================

/**
 * Search for nearby gas stations
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {number} radius - Search radius in kilometers
 * @param {number} limit - Maximum number of results
 * @returns {Promise<Array>} Array of station objects
 */
async function searchNearby(lat, lon, radius = 10, limit = 50) {
    const url = `${API_BASE_URL}${API_ENDPOINTS.nearby}?lat=${lat}&lon=${lon}&km=${radius}&limit=${limit}`;

    try {
        console.log(`Searching for stations at (${lat}, ${lon}) within ${radius}km...`);
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`Found ${data.length} stations`);
        return data;
    } catch (error) {
        console.error('Error fetching nearby stations:', error);
        throw error;
    }
}

// ===========================
// UI Helper Functions
// ===========================

/**
 * Show loading state in results panel
 */
function showLoading() {
    const resultsContent = document.getElementById('results-content');
    resultsContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Searching for stations...</p>
        </div>
    `;
}

/**
 * Show error message in results panel
 * @param {string} message - Error message to display
 */
function showError(message) {
    const resultsContent = document.getElementById('results-content');
    resultsContent.innerHTML = `
        <div class="error-message">
            <p>⚠️ ${message}</p>
        </div>
    `;
}

/**
 * Show empty state in results panel
 * @param {number} radius - Search radius used
 */
function showEmptyState(radius) {
    const resultsContent = document.getElementById('results-content');
    resultsContent.innerHTML = `
        <div class="empty-state">
            <p>No stations found within ${radius} km.</p>
            <p>Try increasing the search radius.</p>
        </div>
    `;
}

/**
 * Display search results in the panel
 * @param {Array} stations - Array of station objects
 * @param {number} radius - Search radius used
 */
function displayResults(stations, radius) {
    const resultsContent = document.getElementById('results-content');

    if (stations.length === 0) {
        showEmptyState(radius);
        return;
    }

    // Create results header
    const header = `
        <div style="padding-bottom: 15px; border-bottom: 1px solid #eee; margin-bottom: 15px;">
            <p style="font-size: 14px; color: #666;">
                Found <strong>${stations.length}</strong> station${stations.length !== 1 ? 's' : ''} within <strong>${radius} km</strong>
            </p>
        </div>
    `;

    // Create station list
    const stationItems = stations.map((station, index) => `
        <div class="station-item" data-station-id="${station.id}" data-index="${index}">
            <div class="station-name">${station.name || 'Unknown Station'}</div>
            <div class="station-brand">${station.brand || 'N/A'}</div>
            <div class="station-address">${station.address || 'Address not available'}</div>
            <div class="station-distance">${station.distance_km.toFixed(2)} km away</div>
        </div>
    `).join('');

    resultsContent.innerHTML = `
        ${header}
        <div class="station-list">
            ${stationItems}
        </div>
    `;

    // Add click handlers to station items
    document.querySelectorAll('.station-item').forEach(item => {
        item.addEventListener('click', () => {
            const index = parseInt(item.dataset.index, 10);
            handleStationClick(stations[index]);
        });
    });
}

/**
 * Handle station item click
 * @param {Object} station - Station object
 */
function handleStationClick(station) {
    // Pan to station location
    state.map.setView([station.lat, station.lon], 15);

    // Open marker popup if it exists
    const marker = state.markers.find(m => m.stationId === station.id);
    if (marker) {
        marker.openPopup();
    }
}

// ===========================
// Brand Icon Functions
// ===========================

/**
 * Normalize brand name for logo lookup
 * Handles case sensitivity and special characters
 * @param {string} brand - Brand name from API
 * @returns {string} Normalized brand name
 */
function normalizeBrandName(brand) {
    if (!brand) return null;

    // Convert to lowercase and trim
    let normalized = brand.toLowerCase().trim();

    // Handle special cases
    // "Circle K" -> "circle_k"
    normalized = normalized.replace(/\s+/g, '_');

    return normalized;
}

/**
 * Get the appropriate icon for a station based on its brand
 * Uses cached icons for performance
 * @param {string} brand - Brand name from API
 * @returns {L.Icon} Leaflet icon object
 */
function getBrandIcon(brand) {
    const normalizedBrand = normalizeBrandName(brand);

    // Check if we already have this icon in cache
    if (iconCache[normalizedBrand]) {
        return iconCache[normalizedBrand];
    }

    // Determine which logo file to use
    let logoFile = FALLBACK_LOGO;
    if (normalizedBrand && BRAND_LOGOS[normalizedBrand]) {
        logoFile = BRAND_LOGOS[normalizedBrand];
    }

    // Create Leaflet icon with brand logo
    const icon = L.icon({
        iconUrl: `brands_logos/${logoFile}`,
        iconSize: [32, 37],        // Size of the icon (10% taller)
        iconAnchor: [16, 35],      // Point that corresponds to marker location
        popupAnchor: [0, -35],     // Point where popup opens relative to iconAnchor
        className: 'brand-marker'   // CSS class for custom styling
    });

    // Cache the icon for future use
    iconCache[normalizedBrand] = icon;

    return icon;
}

// ===========================
// Map Marker Functions
// ===========================

/**
 * Clear all markers from the map
 */
function clearMarkers() {
    // Remove station markers
    state.markers.forEach(marker => {
        state.map.removeLayer(marker);
    });
    state.markers = [];

    // Remove click marker
    if (state.clickMarker) {
        state.map.removeLayer(state.clickMarker);
        state.clickMarker = null;
    }
}

/**
 * Add a marker for the clicked location
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 */
function addClickMarker(lat, lon) {
    // Remove existing click marker
    if (state.clickMarker) {
        state.map.removeLayer(state.clickMarker);
    }

    // Create blue circle marker for clicked location
    const blueIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    state.clickMarker = L.marker([lat, lon], { icon: blueIcon })
        .addTo(state.map)
        .bindPopup('<strong>Search Location</strong>')
        .openPopup();
}

/**
 * Add markers for station results
 * @param {Array} stations - Array of station objects
 */
function addStationMarkers(stations) {
    stations.forEach(station => {
        // Get brand-specific icon (or fallback)
        const brandIcon = getBrandIcon(station.brand);

        const marker = L.marker([station.lat, station.lon], { icon: brandIcon })
            .addTo(state.map)
            .bindPopup(`
                <div style="min-width: 150px;">
                    <strong>${station.name}</strong><br>
                    <em>${station.brand}</em><br>
                    <small>${station.address}</small><br>
                    <strong>${station.distance_km.toFixed(2)} km away</strong>
                </div>
            `);

        // Store station ID for reference
        marker.stationId = station.id;
        state.markers.push(marker);
    });

    // Adjust map bounds to show all markers
    if (stations.length > 0) {
        const bounds = L.latLngBounds(
            stations.map(s => [s.lat, s.lon])
        );

        // Include click marker in bounds
        if (state.clickMarker) {
            bounds.extend(state.clickMarker.getLatLng());
        }

        state.map.fitBounds(bounds, { padding: [50, 50] });
    }
}

// ===========================
// Map Initialization
// ===========================

/**
 * Initialize the Leaflet map with OpenStreetMap tiles
 */
function initMap() {
    // Create map instance centered on a default location
    // Using Warsaw, Poland as default
    const defaultCenter = [52.22936, 21.01293]; // Warsaw, Poland
    const defaultZoom = 12;

    // Initialize map
    state.map = L.map('map').setView(defaultCenter, defaultZoom);

    // Add CartoDB Voyager tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19,
        minZoom: 3,
        subdomains: 'abcd'
    }).addTo(state.map);

    console.log('Map initialized successfully');
}

// ===========================
// Event Handlers
// ===========================

/**
 * Handle map click events
 * @param {Object} e - Leaflet click event
 */
async function handleMapClick(e) {
    const { lat, lng } = e.latlng;
    console.log(`Map clicked at: ${lat}, ${lng}`);

    // Prevent multiple simultaneous searches
    if (state.isLoading) {
        console.log('Search already in progress...');
        return;
    }

    state.isLoading = true;

    try {
        // Clear previous results and markers
        clearMarkers();

        // Show loading state
        showLoading();

        // Add marker for clicked location
        addClickMarker(lat, lng);

        // Store search parameters
        state.lastSearch = { lat, lng, radius: state.radius };

        // Perform API search
        const stations = await searchNearby(lat, lng, state.radius);

        // Display results in panel
        displayResults(stations, state.radius);

        // Add markers to map
        addStationMarkers(stations);

    } catch (error) {
        console.error('Search failed:', error);
        showError('Unable to fetch stations. Please check your connection and try again.');
    } finally {
        state.isLoading = false;
    }
}

/**
 * Handle geolocation button click
 */
async function handleGeolocate() {
    console.log('Geolocation button clicked');

    // Check if geolocation is supported
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
    }

    // Prevent multiple simultaneous geolocation requests
    if (state.isLoading) {
        console.log('Request already in progress...');
        return;
    }

    // Get button element for UI updates
    const button = document.getElementById('geolocate-btn');
    const buttonText = button.querySelector('.text');
    const originalText = buttonText.textContent;

    try {
        // Set loading state
        state.isLoading = true;
        button.disabled = true;
        buttonText.textContent = 'Locating...';
        button.classList.add('loading');

        console.log('Requesting user location...');

        // Get user's current position
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        });

        const { latitude, longitude } = position.coords;
        console.log(`User location: ${latitude}, ${longitude}`);

        // Store current location
        state.currentLocation = { lat: latitude, lon: longitude };

        // Clear previous results and markers
        clearMarkers();

        // Show loading state in results panel
        showLoading();

        // Center map on user location
        state.map.setView([latitude, longitude], 13);

        // Add marker for user location
        addClickMarker(latitude, longitude);

        // Update marker popup text
        if (state.clickMarker) {
            state.clickMarker.setPopupContent('<strong>Your Location</strong>').openPopup();
        }

        // Store search parameters
        state.lastSearch = { lat: latitude, lng: longitude, radius: state.radius };

        // Perform API search at user's location
        const stations = await searchNearby(latitude, longitude, state.radius);

        // Display results in panel
        displayResults(stations, state.radius);

        // Add markers to map
        addStationMarkers(stations);

    } catch (error) {
        console.error('Geolocation error:', error);

        // Handle specific error types
        if (error.code === 1) {
            // PERMISSION_DENIED
            showError('Location access denied. Please click on the map to search manually.');
        } else if (error.code === 2) {
            // POSITION_UNAVAILABLE
            showError('Unable to determine your location. Please click on the map to search manually.');
        } else if (error.code === 3) {
            // TIMEOUT
            showError('Location request timed out. Please click on the map to search manually.');
        } else {
            // API or network error
            showError('Unable to fetch stations. Please check your connection and try again.');
        }
    } finally {
        // Reset button state
        state.isLoading = false;
        button.disabled = false;
        buttonText.textContent = originalText;
        button.classList.remove('loading');
    }
}

/**
 * Handle search radius change
 * @param {Event} e - Change event
 */
async function handleRadiusChange(e) {
    const newRadius = parseInt(e.target.value, 10);
    const radiusSelect = e.target;
    console.log(`Search radius changed to: ${newRadius} km`);

    // Update radius in state
    state.radius = newRadius;

    // If no previous search was performed, just store the new radius
    if (!state.lastSearch) {
        console.log('No previous search - radius will be used for next search');
        return;
    }

    // Prevent multiple simultaneous searches
    if (state.isLoading) {
        console.log('Search already in progress...');
        return;
    }

    state.isLoading = true;

    try {
        // Add loading visual feedback
        radiusSelect.disabled = true;
        radiusSelect.classList.add('loading');

        // Get the last search location
        const { lat, lng } = state.lastSearch;
        console.log(`Re-searching at (${lat}, ${lng}) with new radius: ${newRadius} km`);

        // Show loading state
        showLoading();

        // Clear only station markers, keep the click marker
        state.markers.forEach(marker => {
            state.map.removeLayer(marker);
        });
        state.markers = [];

        // Perform API search with new radius
        const stations = await searchNearby(lat, lng, newRadius);

        // Display results in panel
        displayResults(stations, newRadius);

        // Add markers to map
        addStationMarkers(stations);

        // Update last search with new radius
        state.lastSearch.radius = newRadius;

    } catch (error) {
        console.error('Re-search failed:', error);
        showError('Unable to fetch stations. Please check your connection and try again.');
    } finally {
        // Remove loading state
        radiusSelect.disabled = false;
        radiusSelect.classList.remove('loading');
        state.isLoading = false;
    }
}

/**
 * Handle close panel button (mobile)
 */
function handleClosePanel() {
    const panel = document.getElementById('results-panel');
    panel.classList.toggle('hidden');
}

// ===========================
// Event Listeners Setup
// ===========================

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Map click event
    state.map.on('click', handleMapClick);

    // Geolocation button
    const geolocateBtn = document.getElementById('geolocate-btn');
    geolocateBtn.addEventListener('click', handleGeolocate);

    // Radius selector
    const radiusSelect = document.getElementById('radius-select');
    radiusSelect.addEventListener('change', handleRadiusChange);

    // Close panel button (mobile)
    const closeBtn = document.getElementById('close-panel');
    closeBtn.addEventListener('click', handleClosePanel);

    console.log('Event listeners set up');
}

// ===========================
// Initialization
// ===========================

/**
 * Initialize the application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Gas Station Finder - Initializing...');

    // Initialize map
    initMap();

    // Set up event listeners
    setupEventListeners();

    // Initialize radius from selector
    const radiusSelect = document.getElementById('radius-select');
    state.radius = parseInt(radiusSelect.value, 10);

    console.log('Application initialized successfully');
    console.log('Phase 2 complete: Click map to search for nearby stations');
});
