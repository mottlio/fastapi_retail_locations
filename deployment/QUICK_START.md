# Quick Start - Deploy with Docker Secrets

## Prerequisites

Transfer files to your VM:
```bash
rsync -avz --exclude '__pycache__' --exclude '.git' \
  /path/to/fastapi-retail-locations/ user@your-vm:/opt/fastapi-retail-locations/

# Also transfer your database dump
scp gas.dump user@your-vm:/opt/fastapi-retail-locations/
```

## Deployment Steps

```bash
cd /opt/fastapi-retail-locations

# 1. Build the app image first
docker build -t gasapp:latest .

# 2. Initialize Swarm (one-time setup)
docker swarm init

# 3. Create secret (replace with your strong password)
echo "YOUR_SECURE_PASSWORD" | docker secret create db_password -

# 4. Deploy the stack
docker stack deploy -c docker-compose.secrets.yml gasapp

# 5. Wait for database to be ready (check logs)
docker service logs gasapp_db --follow
# Press Ctrl+C when you see "database system is ready to accept connections"

# 6. Restore database from dump
docker cp gas.dump $(docker ps -q -f name=gasapp_db):/tmp/gas.dump
docker exec $(docker ps -q -f name=gasapp_db) pg_restore -U gasapp -d gas --clean --if-exists --no-owner --no-privileges /tmp/gas.dump

# 7. Run ANALYZE to update statistics
docker exec $(docker ps -q -f name=gasapp_db) psql -U gasapp -d gas -c "ANALYZE"

# 8. Verify the API works
curl "http://localhost:8000/api/nearby?lat=51.5074&lon=-0.1278&km=10&limit=5"
```

## View Status

```bash
docker stack ps gasapp          # Service status
docker service logs gasapp_app  # App logs
docker service logs gasapp_db   # DB logs
```

## Stop/Start

```bash
docker stack rm gasapp                                        # Stop
docker stack deploy -c docker-compose.secrets.yml gasapp     # Start
```

## Troubleshooting Failed Deployments

If deployment fails with network errors:

```bash
# 1. Remove the stack
docker stack rm gasapp

# 2. Wait for cleanup
sleep 10

# 3. Remove any leftover networks
docker network ls | grep gasapp
docker network rm <network-name-if-any>

# 4. Redeploy
docker stack deploy -c docker-compose.secrets.yml gasapp
```

See `DEPLOY_WITH_SECRETS.md` for detailed documentation.
