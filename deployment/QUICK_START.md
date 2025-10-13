# Quick Start - Deploy with Docker Secrets

**TL;DR** - Secure deployment in 5 commands:

```bash
# 1. Build the app image first
docker build -t gasapp:latest .

# 2. Initialize Swarm
docker swarm init

# 3. Create secret (replace with your strong password)
echo "YOUR_SECURE_PASSWORD" | docker secret create db_password -

# 4. Deploy
docker stack deploy -c docker-compose.secrets.yml gasapp

# 5. Verify
curl http://localhost:8000/health
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

See `DEPLOY_WITH_SECRETS.md` for detailed documentation.
