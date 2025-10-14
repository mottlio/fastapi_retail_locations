#!/bin/bash
  echo "Pulling latest code..."
  git pull origin main
  echo "Building new image..."
  docker build -t gasapp:latest .
  echo "Deploying update..."
  docker stack deploy -c docker-compose.secrets.yml gasapp
  echo "Update complete! Checking status..."
  sleep 5
  docker stack ps gasapp