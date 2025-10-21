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

echo "3. Redeploying stack..."
docker stack deploy -c docker-compose.secrets.yml gasapp
echo ""

echo "4. Waiting for containers to be ready..."
sleep 10
echo ""

echo "5. Running database migrations..."
CONTAINER_ID=$(docker ps -q -f name=gasapp_app)
if [ -n "$CONTAINER_ID" ]; then
    docker exec $CONTAINER_ID alembic upgrade head
    echo "✓ Migrations completed successfully"
else
    echo "⚠ Warning: No running container found. Skipping migrations."
fi
echo ""

echo "6. Verifying migration version..."
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -t -c "SELECT version_num FROM alembic_version" 2>/dev/null || echo "Alembic not initialized"
echo ""

echo "7. Checking service status..."
docker stack ps gasapp --no-trunc | head -5
echo ""

echo "8. Verifying new code is running..."
docker exec $(docker ps -q -f name=gasapp_app) head -5 ./app/main.py
echo ""

echo "=== Update complete! ==="