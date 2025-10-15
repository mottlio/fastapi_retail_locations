# UI Local Quick Start Guide

This guide describes the steps to run the Gas Station Finder UI locally for development and testing.

## Prerequisites

- **Docker Desktop** - For running PostgreSQL/PostGIS database
- **Python 3.12+** - For running FastAPI backend
- **uv** - Python package manager (or pip)
- **Web browser** - Chrome, Firefox, Safari, or Edge

## Architecture Overview

The local development setup consists of three components:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   UI Frontend   │ ------> │   FastAPI App    │ ------> │  PostgreSQL DB  │
│  localhost:8080 │  HTTP   │  localhost:8000  │  SQL    │  localhost:5432 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

- **UI** serves static HTML/CSS/JS files with Leaflet map
- **FastAPI** provides `/api/nearby` endpoint with CORS enabled
- **PostgreSQL** stores gas station data with PostGIS extensions

---

## Step 1: Start the Database Container

The database runs in a Docker container and must be started first.

```bash
# Navigate to the database directory
cd db

# Start the PostgreSQL/PostGIS container
docker compose up -d

# Verify the container is running
docker compose ps
```

**Expected output:**
```
NAME      IMAGE            STATUS
gasdb     postgres:17      Up X seconds
```

### Verify Database Connectivity

Test that the database is accessible:

```bash
# Connect via psql (optional)
docker exec -it gasdb psql -U gasapp -d gas

# Inside psql, run:
\dt                          # List tables (should show gas_stations)
SELECT COUNT(*) FROM gas_stations;  # Check record count
\q                           # Quit psql
```

### Troubleshooting Database

If the container fails to start:

```bash
# View logs
docker compose logs -f db

# Stop and restart
docker compose down
docker compose up -d

# Hard reset (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

---

## Step 2: Start the FastAPI Backend

The API server provides the `/api/nearby` endpoint for searching stations.

```bash
# Navigate to project root (from db/ directory)
cd ..

# Activate virtual environment (if using venv)
source .venv/bin/activate

# OR start with uv (recommended)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify API is Running

Open a **new terminal** and test the API:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}

# Test nearby endpoint (example coordinates)
curl "http://localhost:8000/api/nearby?lat=40.7128&lon=-74.0060&km=10&limit=5"

# Should return JSON array of stations (or empty array if none in area)
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Troubleshooting API

**Issue: Connection refused**
- Ensure database is running: `docker compose ps` in `db/` directory
- Check database environment variables in `.env` or hardcoded values

**Issue: Module not found errors**
- Install dependencies: `uv pip install -r requirements.txt` or `uv sync`
- Verify you're in project root directory

**Issue: CORS errors (from browser)**
- Verify CORS middleware is configured in `app/main.py`
- Should allow origins: `http://localhost:8080` and `http://127.0.0.1:8080`

---

## Step 3: Start the UI Server

The UI is served as static files using Python's built-in HTTP server.

```bash
# Open a NEW terminal window/tab
# Navigate to project root
cd /path/to/fastapi-retail-locations

# Start the UI server
python3 -m http.server 8080 --directory ui
```

**Expected output:**
```
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

### Access the UI

Open your web browser and navigate to:

**http://localhost:8080/**

You should see:
- Interactive map (default centered on center of USA)
- "Find My Location" button (top-left)
- "Search Radius" dropdown (top-left)
- "Nearby Gas Stations" panel (right side)

### Troubleshooting UI

**Issue: Blank page or map doesn't load**
- Check browser console for errors (F12 → Console tab)
- Verify Leaflet CSS/JS are loading from CDN
- Check that `ui/js/app.js` and `ui/css/style.css` exist

**Issue: "Unable to fetch stations" error**
- Verify FastAPI is running on port 8000
- Check browser console for CORS errors
- Test API directly with curl (see Step 2)

**Issue: Empty results when clicking map**
- Ensure database has station data
- Try clicking on a populated area (e.g., major cities)
- Check API response in browser DevTools → Network tab

**Issue: Port 8080 already in use**
- Kill existing process: `lsof -ti:8080 | xargs kill`
- Or use different port: `python3 -m http.server 8090 --directory ui`
  - Then update `API_BASE_URL` in `ui/js/app.js` if needed

---

## Complete Startup Checklist

Use this checklist when starting the development environment:

- [ ] **Terminal 1**: Start database
  ```bash
  cd db && docker compose up -d
  ```

- [ ] **Terminal 2**: Start FastAPI
  ```bash
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

- [ ] **Terminal 3**: Start UI server
  ```bash
  python3 -m http.server 8080 --directory ui
  ```

- [ ] **Browser**: Open http://localhost:8080/

- [ ] **Verify**: Click map or use "Find My Location" to search for stations

---

## Quick Shutdown

To stop all services:

```bash
# Terminal 1 (database) - from db/ directory
docker compose down

# Terminal 2 (FastAPI)
# Press CTRL+C

# Terminal 3 (UI server)
# Press CTRL+C
```

---

## Testing the UI Features

### Test Map Click Search
1. Open http://localhost:8080/
2. Click anywhere on the map
3. Blue marker should appear at click location
4. Results panel should show loading spinner
5. After ~1-2 seconds, stations should appear (if any in area)
6. Red markers should appear on map for each station

### Test Geolocation
1. Click "Find My Location" button
2. Browser will request location permission → **Allow**
3. Button text changes to "Locating..."
4. Map centers on your location with blue marker
5. Results panel shows nearby stations automatically

### Test Radius Selector
1. Perform a search (map click or geolocation)
2. Change radius dropdown (5km → 10km → 25km → 50km)
3. Search should automatically re-run with new radius
4. Results panel updates with new station count and radius
5. Station markers update on map

### Test Error Handling
1. Stop FastAPI server (CTRL+C in Terminal 2)
2. Click on map
3. Should show: "⚠️ Unable to fetch stations. Please check your connection and try again."
4. Restart FastAPI and try again

---

## Configuration Details

### Database Connection
- **Host**: localhost
- **Port**: 5432
- **User**: gasapp
- **Password**: gaspass (or as configured)
- **Database**: gas

Connection string in `app/db.py`:
```python
postgresql+asyncpg://gasapp:gaspass@localhost:5432/gas
```

### API Endpoints
- **Base URL**: http://localhost:8000
- **Nearby search**: `/api/nearby?lat={lat}&lon={lon}&km={km}&limit={limit}`
- **Health check**: `/health`
- **API docs**: `/docs`

### UI Configuration
- **Server URL**: http://localhost:8080
- **API Base URL**: Configured in `ui/js/app.js:24`
  ```javascript
  const API_BASE_URL = 'http://localhost:8000';
  ```

### CORS Configuration
FastAPI CORS middleware in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Development Tips

### Hot Reload
- **FastAPI**: Auto-reloads when Python files change (with `--reload` flag)
- **UI**: Refresh browser (F5) after changing HTML/CSS/JS files
- **Database**: Requires restart if schema changes

### Browser DevTools
Press **F12** or **Cmd+Option+I** to open DevTools:

- **Console tab**: View JavaScript logs and errors
- **Network tab**: Inspect API requests/responses
- **Elements tab**: Inspect HTML/CSS

### Useful Commands

```bash
# Check what's running on ports
lsof -i :5432    # Database
lsof -i :8000    # FastAPI
lsof -i :8080    # UI server

# View FastAPI logs
# (visible in Terminal 2)

# View database logs
cd db && docker compose logs -f db

# Connect to database
docker exec -it gasdb psql -U gasapp -d gas

# Restart services individually
docker compose restart db     # Database only
# CTRL+C and re-run uvicorn    # FastAPI
# CTRL+C and re-run http.server  # UI
```

### Data Population
If database is empty, you'll get zero results when searching. To populate:

1. Import data via `pg_restore` (see `db/manual.md`)
2. Or insert test data manually via psql
3. Or use your ETL pipeline to load data

---

## Next Steps

Once the UI is running locally:

1. **Test all features** using the checklist above
2. **Review code** in `ui/js/app.js` for application logic
3. **Customize styling** in `ui/css/style.css`
4. **Deploy to production** using Caddy (see production deployment docs)

For production deployment, see:
- `Caddyfile` - Caddy reverse proxy configuration
- `docker-compose.yml` - Production container setup
- Main `CLAUDE.md` - Project architecture and deployment notes

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Database won't start | `docker compose down -v && docker compose up -d` |
| API returns 500 errors | Check database connection and logs |
| CORS errors in browser | Verify CORS middleware in `app/main.py` |
| Empty search results | Click on major city or check if DB has data |
| Port already in use | Kill process: `lsof -ti:PORT \| xargs kill` |
| Geolocation not working | Must use HTTPS or localhost, check browser permissions |
| Map tiles not loading | Check internet connection (OSM tiles from CDN) |

---

## Support

For issues or questions:
- Check `CLAUDE.md` for project documentation
- Review `ui/ui_development_plan.md` for UI architecture
- Check `ui/development_progress.md` for implementation status
- Inspect browser console and network tab for errors
