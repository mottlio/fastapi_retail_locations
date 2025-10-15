# VM Deployment Plan for Gas Station Finder UI

This document outlines the steps required to deploy the UI to your virtual machine where the database and API services are already running.

## Current State Analysis

### What's Already Running on VM
- ✅ PostgreSQL/PostGIS database (via Docker Swarm)
- ✅ FastAPI application (via Docker Swarm)
- ✅ Caddy reverse proxy (via Docker Swarm)
- ✅ Docker secrets for database password
- ✅ Network overlay: `app-network`

### What's Missing
- ❌ UI static files not included in Docker image
- ❌ Caddyfile not configured to serve static files
- ❌ Caddyfile not configured to proxy API requests

### Current Architecture
```
Internet → Caddy (fuel-api.mottl.io) → FastAPI (:8000)
                                           ↓
                                      PostgreSQL (:5432)
```

### Target Architecture
```
Internet → Caddy (fuel-api.mottl.io)
              ├─→ / (static files: UI)
              ├─→ /api/* (proxy: FastAPI)
              └─→ /docs, /redoc, /health (proxy: FastAPI)
                                ↓
                           FastAPI (:8000)
                                ↓
                           PostgreSQL (:5432)
```

---

## Required Changes Overview

| File | Change Required | Purpose |
|------|----------------|---------|
| `Dockerfile` | Add UI files to image | Include static HTML/CSS/JS in container |
| `Caddyfile` | Update routing config | Serve static files and proxy API |
| `docker-compose.secrets.yml` | Update Caddy volumes | Mount UI files into Caddy container |
| `update-gasapp.sh` | No changes needed | Already rebuilds and deploys |

---

## Step-by-Step Deployment Plan

### Phase 1: Prepare Files Locally

#### 1.1 Update Dockerfile

**File**: `Dockerfile`

**Add these lines** after line 44 (after copying alembic.ini):

```dockerfile
# Copy UI static files
COPY --chown=appuser:appuser ui/ ./ui/
```

**Complete context** (lines 42-50):
```dockerfile
# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser ui/ ./ui/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000
```

**Why**: This includes the UI directory in the Docker image so Caddy can serve it.

---

#### 1.2 Update Caddyfile

**File**: `Caddyfile`

**Replace entire contents** with:

```caddyfile
fuel-api.mottl.io {
    encode gzip zstd

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer-when-downgrade"
    }

    # Serve static UI files from the app container's /app/ui directory
    # Note: We'll mount this from the app container
    root * /srv/ui
    file_server

    # Proxy API requests to FastAPI backend
    reverse_proxy /api/* gasapp_app:8000
    reverse_proxy /docs gasapp_app:8000
    reverse_proxy /redoc gasapp_app:8000
    reverse_proxy /openapi.json gasapp_app:8000
    reverse_proxy /health gasapp_app:8000

    # SPA fallback: serve index.html for non-API routes
    try_files {path} /index.html
}
```

**Why**:
- Serves static files from `/srv/ui` (mounted from app container)
- Proxies `/api/*` to FastAPI
- Proxies docs endpoints to FastAPI
- SPA fallback for client-side routing (future-proof)

**Alternative approach** (simpler but requires Caddy to access app container filesystem):
If the above doesn't work due to volume mounting complexity, we can serve directly from the app container by having FastAPI serve static files. See "Alternative Approach" section below.

---

#### 1.3 Update docker-compose.secrets.yml

**File**: `docker-compose.secrets.yml`

**Update the `caddy` service** (around line 56):

**Before:**
```yaml
  caddy:
    image: caddy:2
    depends_on:
      - app
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data        # stores TLS certs (persist!)
      - caddy_config:/config
    networks:
      - app-network
    deploy:
      restart_policy:
        condition: on-failure
```

**After:**
```yaml
  caddy:
    image: caddy:2
    depends_on:
      - app
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data        # stores TLS certs (persist!)
      - caddy_config:/config
      - ui_files:/srv/ui:ro     # Mount UI files from shared volume
    networks:
      - app-network
    deploy:
      restart_policy:
        condition: on-failure
```

**Update the `app` service** (around line 27):

**Before:**
```yaml
  app:
    image: gasapp:latest
    environment:
      DB_USER: ${DB_USER:-gasapp}
      # App will read password from secret file
      DB_PASSWORD_FILE: /run/secrets/db_password
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: ${DB_NAME:-gas}
    expose:
      - "8000"
    secrets:
      - db_password
    depends_on:
      - db
    networks:
      - app-network
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**After:**
```yaml
  app:
    image: gasapp:latest
    environment:
      DB_USER: ${DB_USER:-gasapp}
      # App will read password from secret file
      DB_PASSWORD_FILE: /run/secrets/db_password
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: ${DB_NAME:-gas}
    expose:
      - "8000"
    volumes:
      - ui_files:/app/ui:ro     # Share UI files with Caddy
    secrets:
      - db_password
    depends_on:
      - db
    networks:
      - app-network
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Add named volume** (around line 73, in the `volumes:` section):

**Before:**
```yaml
volumes:
  db_data:
  caddy_data:
  caddy_config:
```

**After:**
```yaml
volumes:
  db_data:
  caddy_data:
  caddy_config:
  ui_files:     # Shared volume for UI static files
```

**Why**: This creates a shared volume where the app container puts UI files and Caddy reads them.

---

### Phase 2: Deploy to VM

#### 2.1 Commit and Push Changes

On your **local machine**:

```bash
# Stage all changes
git add Dockerfile Caddyfile docker-compose.secrets.yml

# Commit with descriptive message
git commit -m "Add UI deployment configuration

- Add ui/ directory to Dockerfile
- Configure Caddyfile to serve static files and proxy API
- Add shared volume for UI files in docker-compose.secrets.yml"

# Push to remote repository
git push origin main
```

---

#### 2.2 Deploy on VM

**SSH into your VM**:

```bash
ssh user@your-vm-ip
```

**Navigate to project directory**:

```bash
cd /path/to/fastapi-retail-locations
```

**Run the update script**:

```bash
./update-gasapp.sh
```

**What this script does**:
1. Pulls latest code from git (including ui/ directory)
2. Builds new Docker image with `--no-cache` (includes UI files)
3. Forces update of `gasapp_app` service
4. Waits for update to complete
5. Verifies new code is running

**Expected output**:
```
Pulling latest code...
From github.com:yourusername/fastapi-retail-locations
 * branch            main       -> FETCH_HEAD
Already up to date. (or merge message)

Building new image (no cache)...
[+] Building XX.Xs (X/X) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.12-slim
 => CACHED [builder 1/6] FROM docker.io/library/python:3.12-slim
 => [builder 2/6] RUN apt-get update && apt-get install -y curl
 => [builder 3/6] RUN curl -LsSf https://astral.sh/uv/install.sh | sh
 => [builder 4/6] WORKDIR /app
 => [builder 5/6] COPY pyproject.toml uv.lock ./
 => [builder 6/6] RUN uv pip install --system -r pyproject.toml
 => [stage-1 1/7] FROM docker.io/library/python:3.12-slim
 => [stage-1 2/7] RUN apt-get update && apt-get install -y libpq5
 => [stage-1 3/7] RUN useradd -m -u 1000 appuser
 => [stage-1 4/7] WORKDIR /app
 => [stage-1 5/7] COPY --from=builder /usr/local/lib/python3.12/site-packages
 => [stage-1 6/7] COPY --from=builder /usr/local/bin /usr/local/bin
 => [stage-1 7/7] COPY --chown=appuser:appuser app/ ./app/
 => [stage-1 8/8] COPY --chown=appuser:appuser ui/ ./ui/
 => exporting to image
 => => naming to docker.io/library/gasapp:latest

Forcing service update...
gasapp_app
overall progress: 1 out of 1 tasks
1/1: running   [==================================================>]
verify: Service converged

Waiting for update to complete...
(sleep 10 seconds)

Update complete! Service status:
ID             NAME             IMAGE            NODE      DESIRED STATE  CURRENT STATE
abc123def456   gasapp_app.1     gasapp:latest    vm-node   Running        Running 15 seconds ago

Verifying new code is running:
# app/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .db import find_nearby, Session, text
```

---

#### 2.3 Update Caddy Configuration

After the app service is updated, we need to reload Caddy with the new configuration.

**Note**: The Caddyfile was already updated in git, so it's on the VM. But we need to reload the Caddy service.

**Option 1: Update Caddy service** (recommended):

```bash
# Update the Caddy service to pick up new Caddyfile
docker service update --force gasapp_caddy
```

**Option 2: Reload Caddy configuration** (if Caddy supports it):

```bash
# Find the Caddy container ID
docker ps | grep caddy

# Reload Caddy config inside container
docker exec <caddy-container-id> caddy reload --config /etc/caddy/Caddyfile
```

**Expected output**:
```
gasapp_caddy
overall progress: 1 out of 1 tasks
1/1: running   [==================================================>]
verify: Service converged
```

---

#### 2.4 Copy UI Files to Shared Volume

**IMPORTANT**: Since we're using a named volume approach, we need to ensure the UI files from the app container are accessible to Caddy.

The issue is that the Dockerfile copies files into the app container's filesystem, but Caddy needs to read them.

**Solution**: We need a helper script to copy UI files to the shared volume.

**Create a helper script on VM**:

```bash
cat > copy-ui-files.sh << 'EOF'
#!/bin/bash
# Find the app container
APP_CONTAINER=$(docker ps -q -f name=gasapp_app)

if [ -z "$APP_CONTAINER" ]; then
    echo "Error: gasapp_app container not found"
    exit 1
fi

echo "Copying UI files from app container to shared volume..."

# Create a temporary container to access the volume
docker run --rm \
    -v gasapp_ui_files:/target \
    --volumes-from $APP_CONTAINER \
    busybox \
    sh -c "cp -r /app/ui/* /target/"

echo "UI files copied successfully!"
EOF

chmod +x copy-ui-files.sh
```

**Run the helper script**:

```bash
./copy-ui-files.sh
```

**Alternative**: See "Alternative Approach" section below for a simpler method.

---

### Phase 3: Verification

#### 3.1 Check Service Status

```bash
# Check all services are running
docker service ls

# Expected output:
ID             NAME           MODE         REPLICAS   IMAGE               PORTS
abc123def456   gasapp_app     replicated   1/1        gasapp:latest
def456ghi789   gasapp_caddy   replicated   1/1        caddy:2             *:80->80/tcp, *:443->443/tcp
ghi789jkl012   gasapp_db      replicated   1/1        postgis/postgis:16-3.4

# Check app service logs
docker service logs gasapp_app --tail 50

# Check Caddy service logs
docker service logs gasapp_caddy --tail 50
```

---

#### 3.2 Test API Endpoints

```bash
# From VM
curl http://localhost:8000/health
# Expected: {"status":"ok"}

curl "http://localhost:8000/api/nearby?lat=40.7128&lon=-74.0060&km=10&limit=5"
# Expected: JSON array of stations
```

---

#### 3.3 Test UI via Caddy

```bash
# Test homepage (should return HTML)
curl https://fuel-api.mottl.io/

# Expected: HTML content starting with <!DOCTYPE html>

# Test API through Caddy
curl "https://fuel-api.mottl.io/api/nearby?lat=40.7128&lon=-74.0060&km=10&limit=5"

# Expected: JSON array of stations

# Test static file
curl https://fuel-api.mottl.io/js/app.js

# Expected: JavaScript code
```

---

#### 3.4 Test in Browser

1. Open browser and navigate to: **https://fuel-api.mottl.io/**

2. **Expected behavior**:
   - Map loads and displays
   - Control panel visible (top-left)
   - Results panel visible (right side)
   - No CORS errors in console

3. **Test functionality**:
   - Click on map → should search for stations
   - Click "Find My Location" → should request permission and search
   - Change radius → should re-search

4. **Check browser console** (F12 → Console):
   - No errors
   - Should see logs like "Gas Station Finder - Initializing..."
   - Should see "Map initialized successfully"

5. **Check browser network tab** (F12 → Network):
   - HTML file loads from fuel-api.mottl.io
   - CSS and JS files load from fuel-api.mottl.io
   - API requests to `/api/nearby` should succeed with 200 status
   - No CORS errors

---

## Alternative Approach: Simpler Deployment

If the shared volume approach is too complex, use this simpler method where FastAPI serves the static files directly.

### Alternative Step 1: Update app/main.py

Add static file serving to FastAPI (after CORS middleware):

```python
from fastapi.staticfiles import StaticFiles

# ... existing CORS middleware ...

# Serve static UI files
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")
```

**Important**: This must come **AFTER** all route definitions to avoid conflicts.

### Alternative Step 2: Update Caddyfile

Simplify to just proxy everything:

```caddyfile
fuel-api.mottl.io {
    encode gzip zstd

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer-when-downgrade"
    }

    # Proxy everything to FastAPI (it will serve static files and API)
    reverse_proxy gasapp_app:8000
}
```

### Alternative Step 3: No volume changes needed

With this approach, you don't need to modify `docker-compose.secrets.yml` volumes.

### Alternative Benefits

- ✅ Simpler configuration
- ✅ Single service serves everything
- ✅ No shared volume complexity
- ✅ Easier to maintain

### Alternative Drawbacks

- ❌ FastAPI handles static files (slight performance impact)
- ❌ No static file caching by Caddy
- ❌ Less separation of concerns

**Recommendation**: Start with the alternative approach for simplicity. Optimize later if needed.

---

## Rollback Procedure

If deployment fails, rollback to previous version:

```bash
# On VM

# Option 1: Rollback to previous service version
docker service rollback gasapp_app
docker service rollback gasapp_caddy

# Option 2: Manually revert to previous image
# (if you tagged previous version)
docker service update --image gasapp:previous gasapp_app

# Option 3: Redeploy from last known good commit
git checkout <previous-commit-hash>
./update-gasapp.sh
```

---

## Troubleshooting

### Issue: UI doesn't load (404 errors)

**Symptoms**:
- Browser shows "Page not found"
- Network tab shows 404 for `/index.html`

**Solutions**:
1. Check if UI files are in Docker image:
   ```bash
   # Find app container
   docker ps | grep gasapp_app

   # Check if ui/ directory exists
   docker exec <container-id> ls -la /app/ui
   ```

2. Check Caddyfile is correct:
   ```bash
   docker exec <caddy-container-id> cat /etc/caddy/Caddyfile
   ```

3. Check Caddy logs:
   ```bash
   docker service logs gasapp_caddy --tail 100
   ```

---

### Issue: CORS errors in browser

**Symptoms**:
- Console shows "blocked by CORS policy"
- API calls fail from browser

**Solutions**:
1. Verify CORS middleware in app/main.py includes correct origins
2. Check API is accessible through Caddy:
   ```bash
   curl "https://fuel-api.mottl.io/api/nearby?lat=40&lon=-74&km=10"
   ```

3. Ensure HTTPS is working (CORS often fails on mixed HTTP/HTTPS)

---

### Issue: Shared volume is empty

**Symptoms**:
- UI files don't appear when accessing site
- Caddy logs show "file not found"

**Solutions**:
1. Use the Alternative Approach (FastAPI serves static files)
2. Or manually copy files to volume (see Phase 2.4)
3. Or rebuild app service:
   ```bash
   docker service update --force gasapp_app
   ```

---

### Issue: Caddy won't reload

**Symptoms**:
- Old Caddyfile configuration still active
- Changes not reflected

**Solutions**:
1. Force update Caddy service:
   ```bash
   docker service update --force gasapp_caddy
   ```

2. Check Caddyfile syntax:
   ```bash
   docker run --rm -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile caddy:2 caddy validate --config /etc/caddy/Caddyfile
   ```

3. Check Caddy logs for errors:
   ```bash
   docker service logs gasapp_caddy --tail 200
   ```

---

### Issue: Map tiles don't load

**Symptoms**:
- Gray tiles instead of map
- Console shows errors loading from tile.openstreetmap.org

**Solutions**:
1. Check internet connectivity from browser
2. Verify no firewall blocking OSM tiles
3. Check browser console for specific errors
4. Try different map tile provider in ui/js/app.js

---

## Post-Deployment Checklist

- [ ] All three services running (db, app, caddy)
- [ ] API health endpoint returns `{"status":"ok"}`
- [ ] UI loads at https://fuel-api.mottl.io/
- [ ] Map displays correctly
- [ ] Map click triggers search (check Network tab)
- [ ] "Find My Location" button works
- [ ] Radius selector triggers re-search
- [ ] No CORS errors in browser console
- [ ] HTTPS certificate is valid (green lock icon)
- [ ] No errors in service logs

---

## Maintenance Notes

### Updating UI in Future

When you make changes to UI files (HTML/CSS/JS):

1. **Local**: Edit files in `ui/` directory
2. **Test locally**: Run `python3 -m http.server 8080 --directory ui`
3. **Commit**: `git commit -am "Update UI: <description>"`
4. **Push**: `git push origin main`
5. **Deploy**: SSH to VM, run `./update-gasapp.sh`
6. **Verify**: Check https://fuel-api.mottl.io/ in browser

### Updating API Only

When you make changes to FastAPI code:

1. **Local**: Edit files in `app/` directory
2. **Test locally**: Run `uvicorn app.main:app --reload`
3. **Commit**: `git commit -am "Update API: <description>"`
4. **Push**: `git push origin main`
5. **Deploy**: SSH to VM, run `./update-gasapp.sh`
6. **Verify**: Check https://fuel-api.mottl.io/docs

### Monitoring

```bash
# Check service health
docker service ls

# View logs
docker service logs -f gasapp_app     # API logs
docker service logs -f gasapp_caddy   # Proxy logs
docker service logs -f gasapp_db      # Database logs

# Check resource usage
docker stats

# Check disk usage
docker system df
```

---

## Security Considerations

- ✅ UI served over HTTPS (via Caddy)
- ✅ CORS properly configured (only allows specific origins)
- ✅ Database not exposed to internet (only internal network)
- ✅ App runs as non-root user
- ✅ Database password stored in Docker secret
- ✅ Security headers configured in Caddy
- ⚠️ Consider adding rate limiting to API (future enhancement)
- ⚠️ Consider adding authentication if UI becomes public (future enhancement)

---

## Performance Optimization

Once deployed, consider these optimizations:

1. **Enable HTTP/2** (Caddy does this automatically)
2. **Enable compression** (already configured: gzip, zstd)
3. **Add caching headers** for static assets:
   ```caddyfile
   header /js/* Cache-Control "public, max-age=3600"
   header /css/* Cache-Control "public, max-age=3600"
   ```
4. **Consider CDN** for static assets (future)
5. **Database query optimization** (indexes already exist)
6. **API response caching** for frequently searched locations (future)

---

## Summary

**Recommended Deployment Path**:

1. ✅ Update `Dockerfile` to include `ui/` directory
2. ✅ Use **Alternative Approach** (FastAPI serves static files)
3. ✅ Update `Caddyfile` to proxy to FastAPI
4. ✅ Commit, push, and run `./update-gasapp.sh`
5. ✅ Verify at https://fuel-api.mottl.io/

**Total deployment time**: ~15 minutes

**Required changes**: 2 files (Dockerfile + Caddyfile)

**No changes needed**: docker-compose.secrets.yml, update-gasapp.sh

---

## Next Steps

After successful deployment:

1. Monitor logs for errors
2. Test all UI features thoroughly
3. Share URL with stakeholders
4. Set up monitoring/alerting (optional)
5. Document any issues in development_progress.md
6. Plan Phase 5+ enhancements per ui_development_plan.md

For questions or issues, refer to:
- `CLAUDE.md` - Project overview
- `deployment/UI_LOCAL_QUICK_START.md` - Local development
- `ui/development_progress.md` - Implementation status
