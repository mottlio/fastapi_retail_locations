# Front-End Development Plan

## Project Overview
Lightweight, responsive front-end UI for the FastAPI retail fuel locations application. The UI allows users to click on a map to find nearby gas stations, with geolocation support and configurable search radius.

## Technology Stack (Lightweight & Fast)

**Core Technologies:**
- **Vanilla JavaScript** - No framework overhead, maximum performance
- **Leaflet.js** (~40KB gzipped) - Interactive map library
- **OpenStreetMap** tiles - Free, no API key required
- **Minimal CSS** - CSS Grid/Flexbox for layout
- **No build process** - Direct deployment, can add Vite/esbuild later if needed

**Why these choices:**
- Minimal bundle size (~50KB total for libraries)
- Fast initial load and runtime performance
- No framework complexity or learning curve
- Easy to deploy and maintain
- Works on all modern browsers

## File Structure

```
fastapi-retail-locations/
├── ui/
│   ├── index.html          # Main page
│   ├── css/
│   │   └── style.css       # Styles
│   ├── js/
│   │   └── app.js          # Application logic
│   └── favicon.ico         # (optional)
├── app/                    # Existing FastAPI app
├── Caddyfile              # Needs update to serve UI
└── ...
```

## UI/UX Design Specifications

### Layout
- **Desktop**: Full-screen split view - 70% map (left), 30% results panel (right)
- **Tablet**: 60% map, 40% results panel
- **Mobile**: Full-screen map with collapsible overlay results panel

### Components

#### 1. Map Canvas (Leaflet)
- Full-screen interactive map
- OpenStreetMap tile layer
- Click-to-search functionality
- Marker for clicked location (blue pin)
- Markers for station results (red pins with labels)
- Zoom controls
- Attribution

#### 2. Control Panel (Top-left overlay on map)
- **Geolocation button**: "Find My Location" with location icon
- **Search radius selector**: Dropdown or button group (5km, 10km, 25km, 50km)
- **Results limit**: Optional slider or input (default 50, max 100)
- Semi-transparent background for visibility over map

#### 3. Results Panel (Right sidebar / Mobile overlay)
- **Header**:
  - "Nearby Gas Stations" title
  - Result count: "Found X stations within Y km"
  - Close button (mobile only)
- **Station list**:
  - Each item shows: Name, Brand, Address, Distance
  - Distance formatted as "X.XX km away"
  - Clickable to center map on station
  - Hover effect for desktop
- **Status messages**:
  - Loading spinner: "Searching for stations..."
  - Error state: "Unable to fetch stations. Please try again."
  - Empty state: "No stations found within X km. Try increasing the search radius."
- **Scroll**: Vertical scroll for long lists

#### 4. Visual Markers
- **Clicked location**: Blue circle marker with popup "Search location"
- **Station markers**:
  - Red map pins
  - Popup on click showing station details
  - Clustered if too many in one area

### Interactions Flow

1. **Page Load**:
   - Map centers on default location (center of Warsaw, Poland)
   - Default zoom level 10
   - Control panel visible
   - Results panel shows welcome message: "Click on the map or use 'Find My Location' to search for stations"

2. **Geolocation Flow**:
   - User clicks "Find My Location" button
   - Browser requests location permission
   - On success: Map centers on user location, auto-searches with current radius
   - On deny: Show message "Location access denied. Click map to search manually."
   - On error: Show message "Unable to get your location. Click map to search manually."

3. **Map Click Flow**:
   - User clicks anywhere on map
   - Blue marker placed at clicked location
   - Loading state shown in results panel
   - API request sent with lat/lon and selected radius
   - Results displayed in panel
   - Red markers added to map for each station
   - Map bounds adjusted to show all results + clicked location

4. **Radius Change**:
   - User selects different radius (5km, 10km, 25km, 50km)
   - If a search has been performed, automatically re-search with new radius
   - If no search yet, radius stored for next search

5. **Station Selection**:
   - User clicks station in results list
   - Map pans to station location
   - Station marker popup opens
   - Station highlighted in results list

## Implementation Steps

### Phase 1: Basic Setup (30 minutes)
- [x] Create `ui/` directory structure
- [ ] Create HTML boilerplate with Leaflet CDN
- [ ] Link CSS and JS files
- [ ] Initialize Leaflet map with OSM tiles
- [ ] Set default center and zoom
- [ ] Test static file serving locally

**Deliverable**: Blank map loads on page

### Phase 2: Core Functionality (1.5 hours)
- [ ] Add map click event handler to capture lat/lon
- [ ] Implement API call to `/api/nearby` with fetch()
- [ ] Parse JSON response
- [ ] Display results in the panel (basic list)
- [ ] Add visual markers to map for results
- [ ] Add marker for clicked location
- [ ] Clear previous results/markers on new search

**Deliverable**: Click map → see stations list + markers

### Phase 3: Geolocation Feature (45 minutes)
- [ ] Create "Find My Location" button in UI
- [ ] Implement browser Geolocation API
- [ ] Handle permission request
- [ ] On success: center map on user location
- [ ] Automatically trigger search at user location
- [ ] Handle errors and denied permissions with user-friendly messages
- [ ] Add loading state to button during geolocation

**Deliverable**: Button centers map on user and searches

### Phase 4: Search Radius Selector (30 minutes)
- [ ] Create radius selector UI (button group or dropdown)
- [ ] Options: 5km, 10km, 25km, 50km
- [ ] Default: 10km
- [ ] Store selected radius in JavaScript variable
- [ ] Pass radius to API as `km` parameter
- [ ] Auto re-search when radius changes (if search already performed)
- [ ] Update results header with current radius

**Deliverable**: User can change search radius

### Phase 5: UX Enhancements (1.5 hours)
- [ ] Add loading spinner during API requests
- [ ] Implement error handling with user-friendly messages
- [ ] Format distance display (e.g., "1.23 km away")
- [ ] Empty state message when no results
- [ ] Welcome message before first search
- [ ] Smooth transitions for results panel
- [ ] Station list item click → pan to marker
- [ ] Marker click → highlight in results list
- [ ] Auto-adjust map bounds to show all results

**Deliverable**: Polished user experience

### Phase 6: Styling & Responsive Design (1.5 hours)
- [ ] Desktop layout: 70/30 split
- [ ] Tablet layout: 60/40 split
- [ ] Mobile layout: full-screen map with overlay
- [ ] Mobile: collapsible results panel
- [ ] Control panel styling (semi-transparent overlay)
- [ ] Results panel styling (clean, readable)
- [ ] Station list item styling with hover effects
- [ ] Button and control styling
- [ ] Loading spinner styling
- [ ] Marker icon customization
- [ ] Color scheme and typography
- [ ] Smooth animations

**Deliverable**: Works beautifully on all screen sizes

### Phase 7: Accessibility & Polish (45 minutes)
- [ ] Keyboard navigation support
- [ ] ARIA labels for controls
- [ ] Focus indicators
- [ ] Semantic HTML
- [ ] Alt text for icons
- [ ] Screen reader friendly status messages
- [ ] High contrast mode support
- [ ] Tab order optimization

**Deliverable**: Accessible to all users

### Phase 8: Deployment Configuration (1 hour)
- [ ] Update Caddyfile to serve static files
- [ ] Configure reverse proxy for API
- [ ] Set cache headers for static assets
- [ ] Test on VM
- [ ] Performance audit (Lighthouse)
- [ ] Browser compatibility check (Chrome, Firefox, Safari, Edge)
- [ ] Mobile device testing

**Deliverable**: Deployed and tested on VM

## API Integration Details

### Endpoint: `/api/nearby`

**Request:**
```javascript
const response = await fetch(
  `/api/nearby?lat=${lat}&lon=${lon}&km=${radius}&limit=50`
);
const data = await response.json();
```

**Parameters:**
- `lat` (float, required): Latitude of search point
- `lon` (float, required): Longitude of search point
- `km` (float, optional): Search radius in kilometers (default: 10)
- `limit` (int, optional): Max results (default: 50, max: 100)

**Expected Response:**
```json
[
  {
    "id": 123,
    "station_key": "unique-key",
    "name": "Shell Station",
    "brand": "Shell",
    "address": "123 Main St, City, State 12345",
    "lat": 40.7128,
    "lon": -74.0060,
    "distance_km": 1.234
  },
  {
    "id": 124,
    "station_key": "another-key",
    "name": "Exxon Station",
    "brand": "Exxon",
    "address": "456 Oak Ave, City, State 12345",
    "lat": 40.7150,
    "lon": -74.0080,
    "distance_km": 2.567
  }
]
```

**Error Handling:**
- Network errors: Show "Unable to connect. Check your connection."
- API errors (500): Show "Server error. Please try again later."
- Empty array: Show "No stations found within X km."
- Invalid coordinates: Show "Invalid location. Please try again."

## Caddy Configuration Update

Update `Caddyfile` to serve UI and proxy API:

```caddyfile
fuel-api.mottl.io {
    encode gzip zstd
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer-when-downgrade"
        # Cache static assets
        Cache-Control "public, max-age=3600"
    }

    # Serve static front-end files from ui/ directory
    root * /app/ui
    file_server

    # Proxy API requests to FastAPI backend
    reverse_proxy /api/* http://gasapp_app:8000
    reverse_proxy /docs http://gasapp_app:8000
    reverse_proxy /redoc http://gasapp_app:8000
    reverse_proxy /openapi.json http://gasapp_app:8000
    reverse_proxy /health http://gasapp_app:8000

    # Handle 404 by serving index.html (SPA fallback)
    try_files {path} /index.html
}
```

**Notes:**
- Static files served from `/app/ui` (container path)
- API calls proxied to FastAPI container
- Compression enabled (gzip, zstd)
- Cache headers for performance
- SPA fallback for clean URLs (future-proof)

## Performance Optimizations

### Client-Side
- **CDN**: Use Leaflet from CDN with SRI hash for caching
- **Lazy loading**: Load map tiles on-demand (Leaflet default)
- **Debouncing**: Debounce radius changes (300ms) to avoid excessive API calls
- **Minimal DOM updates**: Only update changed elements, use DocumentFragment
- **Request abort**: Cancel pending requests when new search starts
- **Marker clustering**: If >100 markers, enable clustering (future)

### Server-Side (Caddy)
- **Compression**: Gzip/Brotli enabled for all text assets
- **Caching**: 1-hour cache for static assets, no cache for API
- **HTTP/2**: Enabled by default in Caddy
- **Minification**: Consider for production (can add build step)

### Code Organization
- **Modular JS**: Separate concerns (map, api, ui, state)
- **No unnecessary libraries**: Keep bundle small
- **Async/await**: Clean async code, proper error handling
- **Event delegation**: Single listener for station lists

## Development Workflow

### Local Development

**Option 1: Separate servers**
```bash
# Terminal 1: FastAPI
uvicorn app.main:app --reload

# Terminal 2: Static files
python -m http.server 8080 -d ui

# Access at http://localhost:8080
# Update JS to point to http://localhost:8000/api/nearby
```

**Option 2: FastAPI serves static**
```python
# Add to app/main.py
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")
```

### VM Deployment

1. Copy `ui/` directory to VM:
   ```bash
   rsync -avz ui/ user@vm:/path/to/app/ui/
   ```

2. Update Caddyfile on VM

3. Reload Caddy:
   ```bash
   docker exec caddy_container caddy reload --config /etc/caddy/Caddyfile
   ```

4. Test at https://fuel-api.mottl.io

## Code Structure

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Meta tags, title, Leaflet CSS -->
</head>
<body>
  <div id="app">
    <!-- Control panel overlay -->
    <div id="controls">
      <button id="geolocate">📍 Find My Location</button>
      <select id="radius">
        <option value="5">5 km</option>
        <option value="10" selected>10 km</option>
        <option value="25">25 km</option>
        <option value="50">50 km</option>
      </select>
    </div>

    <!-- Map container -->
    <div id="map"></div>

    <!-- Results panel -->
    <aside id="results-panel">
      <header>
        <h2>Nearby Gas Stations</h2>
        <button id="close-panel">✕</button>
      </header>
      <div id="results-content">
        <!-- Station list rendered here -->
      </div>
    </aside>
  </div>

  <!-- Leaflet JS, app.js -->
</body>
</html>
```

### JavaScript Modules (Conceptual)

```javascript
// State management
const state = {
  map: null,
  markers: [],
  clickMarker: null,
  currentLocation: null,
  radius: 10,
  lastSearch: null
};

// Map initialization
function initMap() { }

// API calls
async function searchNearby(lat, lon, radius) { }

// UI updates
function displayResults(stations) { }
function showLoading() { }
function showError(message) { }

// Geolocation
function findUserLocation() { }

// Event handlers
function handleMapClick(e) { }
function handleRadiusChange(e) { }
function handleGeolocate(e) { }
function handleStationClick(station) { }
```

### CSS Organization

```css
/* Reset and base styles */
/* Layout (Grid/Flexbox) */
/* Map container */
/* Control panel */
/* Results panel */
/* Station list items */
/* Loading and error states */
/* Mobile responsive */
/* Animations */
```

## Testing Checklist

### Functionality
- [ ] Map loads correctly
- [ ] Click on map searches for stations
- [ ] Geolocation button gets user location
- [ ] Geolocation triggers automatic search
- [ ] Radius selector changes search radius
- [ ] Results display correctly
- [ ] Markers appear on map
- [ ] Clicking station in list pans to marker
- [ ] Clicking marker shows popup
- [ ] Empty state displays when no results
- [ ] Error states display correctly
- [ ] Loading states work properly

### Responsive Design
- [ ] Desktop layout (>1024px)
- [ ] Tablet layout (768px-1024px)
- [ ] Mobile layout (<768px)
- [ ] Mobile results panel collapses/expands
- [ ] Touch interactions work on mobile
- [ ] Pinch-to-zoom works

### Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Performance
- [ ] Lighthouse score >90
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s
- [ ] No console errors
- [ ] No memory leaks

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Color contrast meets WCAG AA

## Future Enhancements (Post-MVP)

### Phase 2 Features
- [ ] Search by address (geocoding API)
- [ ] Filter by brand (checkboxes)
- [ ] Sort results (distance, name, brand)
- [ ] Station details modal with all fields
- [ ] Route planning / directions link
- [ ] Share location via URL parameters
- [ ] Remember last search location (localStorage)

### Phase 3 Features
- [ ] Dark mode toggle
- [ ] Multiple map tile options (satellite, dark)
- [ ] Marker clustering for dense areas
- [ ] Heatmap view
- [ ] User favorites (localStorage)
- [ ] Recent searches history
- [ ] Export results to CSV/JSON

### Phase 4 Features
- [ ] User accounts and saved locations
- [ ] Station ratings and reviews
- [ ] Price information (if available)
- [ ] Real-time updates (WebSocket)
- [ ] Advanced filtering (amenities, services)
- [ ] Batch geocoding for multiple addresses
- [ ] Admin dashboard for data management

## Estimated Timeline

- **Phase 1**: 30 minutes - Basic setup
- **Phase 2**: 1.5 hours - Core functionality
- **Phase 3**: 45 minutes - Geolocation feature
- **Phase 4**: 30 minutes - Search radius selector
- **Phase 5**: 1.5 hours - UX enhancements
- **Phase 6**: 1.5 hours - Styling & responsive design
- **Phase 7**: 45 minutes - Accessibility & polish
- **Phase 8**: 1 hour - Deployment configuration

**Total MVP**: ~8 hours for complete, polished implementation

## Success Metrics

- **Performance**: Page load <2s, API response <500ms
- **Usability**: 3 clicks or less to find nearest station
- **Accessibility**: WCAG AA compliant
- **Responsive**: Works on all screen sizes
- **Browser support**: 95%+ of users
- **Error rate**: <1% API failures handled gracefully

## Notes

- Keep bundle size under 100KB (including libraries)
- Prioritize mobile experience (60% of traffic typically)
- Test with real user coordinates from coverage area
- Monitor API usage for rate limiting needs
- Consider CDN for production (CloudFlare, Fastly)
- Plan for internationalization if expanding beyond US
