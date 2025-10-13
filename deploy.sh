#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code from git..."
git pull origin main

# Build and start containers
echo "🏗️  Building Docker images..."
docker compose build --no-cache

# Stop old containers
echo "⏹️  Stopping old containers..."
docker compose down

# Run database migrations
echo "🗄️  Running database migrations..."
docker compose up -d db
sleep 5  # Wait for DB to be ready

# Apply migrations (if running outside container)
# Make sure .env is loaded for DATABASE_URL
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Run migrations
echo "Running Alembic migrations..."
docker compose run --rm app alembic upgrade head

# Start all services
echo "▶️  Starting all services..."
docker compose up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check status
echo "📊 Service status:"
docker compose ps

# Check app health
echo "🏥 Checking app health..."
curl -f http://localhost:8000/health || echo "⚠️  Health check failed"

echo "✅ Deployment complete!"
echo "📍 API available at: http://localhost:8000"
echo "📖 Docs available at: http://localhost:8000/docs"
