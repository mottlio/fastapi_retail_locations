#!/bin/bash
echo "Pulling latest code..."
git pull origin main
echo "Building new image (no cache)..."
docker build --no-cache -t gasapp:latest .
echo "Forcing service update..."
docker service update --force gasapp_app
echo "Waiting for update to complete..."
sleep 10
echo "Update complete! Service status:"
docker service ps gasapp_app --no-trunc | head -3
echo ""
echo "Verifying new code is running:"
docker exec $(docker ps -q -f name=gasapp_app) head -5 ./app/main.py