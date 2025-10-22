#!/bin/bash
set -e  # Exit on error

echo "=== Starting gasapp update ==="
echo ""

echo "1. Pulling latest code..."
git pull origin main
echo ""

echo "2. Building new image (no cache)..."
docker build --no-cache -t gasapp:latest .
echo ""

echo "3. Removing old stack..."
docker stack rm gasapp
echo ""

echo "4. Waiting for cleanup..."
sleep 15
echo ""

echo "5. Deploying new stack..."
docker stack deploy -c docker-compose.secrets.yml gasapp
echo ""

echo "6. Waiting for containers to be ready..."
sleep 15
echo ""

echo "7. Running database migrations..."
CONTAINER_ID=$(docker ps -q -f name=gasapp_app)
if [ -n "$CONTAINER_ID" ]; then
    docker exec $CONTAINER_ID alembic upgrade head
    echo "✓ Migrations completed successfully"
else
    echo "⚠ Warning: No running container found. Skipping migrations."
fi
echo ""

echo "8. Verifying migration version..."
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -t -c "SELECT version_num FROM alembic_version" 2>/dev/null || echo "Alembic not initialized"
echo ""

echo "9. Checking service status..."
docker stack ps gasapp --no-trunc | head -5
echo ""

echo "10. Verifying new code is running..."
docker exec $(docker ps -q -f name=gasapp_app) head -5 ./app/main.py
echo ""

echo "11. Verifying UI files are updated..."
ICON_COUNT=$(docker exec $(docker ps -q -f name=gasapp_app) grep -c "renderServiceIcons" ./ui/js/app.js 2>/dev/null || echo "0")
if [ "$ICON_COUNT" -gt "0" ]; then
    echo "✓ UI contains service icons code (found $ICON_COUNT occurrences)"
else
    echo "⚠ Warning: Service icons code not found in UI"
fi
echo ""

echo "=== Update complete! ==="