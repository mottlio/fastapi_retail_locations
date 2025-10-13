# Deployment Documentation

Complete deployment guide for the FastAPI Retail Locations application.

## Quick Links

- **[QUICK_START.md](QUICK_START.md)** - Fast deployment guide (5 minutes)
- **[DEPLOY_WITH_SECRETS.md](DEPLOY_WITH_SECRETS.md)** - Comprehensive deployment with Docker Secrets
- **[DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md)** - Database backup, restore, and maintenance

## Deployment Overview

This application uses **Docker Swarm** with **Docker Secrets** for secure production deployment.

### Architecture

- **Database**: PostgreSQL 16 + PostGIS 3.4 (for geospatial queries)
- **Application**: FastAPI (Python 3.12) with async SQLAlchemy
- **Networking**: Docker overlay network for service communication
- **Security**: Docker Secrets for password management (encrypted)

## Getting Started

### 1. Choose Your Guide

**New to deployment?** Start with [QUICK_START.md](QUICK_START.md)

**Want detailed explanations?** Use [DEPLOY_WITH_SECRETS.md](DEPLOY_WITH_SECRETS.md)

**Need database help?** See [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md)

### 2. Prerequisites

Before deploying, ensure you have:

- ✅ VM with Docker installed
- ✅ SSH access to your VM
- ✅ Application code transferred to VM
- ✅ Database dump file (gas.dump) ready
- ✅ Strong password generated for database

### 3. Deployment Steps Summary

```bash
# On your VM
cd /opt/fastapi-retail-locations

# 1. Build image
docker build -t gasapp:latest .

# 2. Initialize Swarm
docker swarm init

# 3. Create secret
echo "STRONG_PASSWORD" | docker secret create db_password -

# 4. Deploy
docker stack deploy -c docker-compose.secrets.yml gasapp

# 5. Restore database
docker cp gas.dump $(docker ps -q -f name=gasapp_db):/tmp/gas.dump
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas --clean --if-exists --no-owner --no-privileges /tmp/gas.dump

# 6. Verify
curl "http://localhost:8000/api/nearby?lat=51.5074&lon=-0.1278&km=10&limit=5"
```

## Common Operations

### View Status

```bash
docker stack ps gasapp
docker service logs gasapp_app --follow
```

### Update Application

```bash
# Rebuild image
docker build -t gasapp:latest .

# Redeploy (zero-downtime)
docker stack deploy -c docker-compose.secrets.yml gasapp
```

### Backup Database

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_dump -U gasapp -d gas -Fc > backup_$(date +%Y%m%d).dump
```

### Stop/Start

```bash
docker stack rm gasapp                                    # Stop
docker stack deploy -c docker-compose.secrets.yml gasapp # Start
```

## Accessing the API

### From Local Machine

```bash
curl http://YOUR_VM_IP:8000/health
curl "http://YOUR_VM_IP:8000/api/nearby?lat=LAT&lon=LON&km=10&limit=10"
```

### Interactive API Docs

Open in browser: `http://YOUR_VM_IP:8000/docs`

### Available Endpoints

- `GET /health` - Health check
- `GET /api/nearby` - Find nearby gas stations
  - Query params: `lat`, `lon`, `km` (radius), `limit`

## Security Considerations

### Docker Secrets

- ✅ Passwords encrypted at rest and in transit
- ✅ No plaintext .env files on VM
- ✅ Access control per container
- ✅ Audit trail

### Network Security

```bash
# Check firewall
sudo ufw status

# Open only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw enable
```

### Database Access

- Database only accessible within Docker network
- Port 5432 bound to localhost only (not exposed externally)
- Use strong passwords with Docker Secrets

## Troubleshooting

### Quick Diagnostics

```bash
# Check all services
docker stack ps gasapp --no-trunc

# View logs
docker service logs gasapp_app --follow
docker service logs gasapp_db --follow

# Test database connection
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT COUNT(*) FROM gas_stations"
```

### Common Issues

| Error | Solution |
|-------|----------|
| Network error with "bridge" driver | See troubleshooting in DEPLOY_WITH_SECRETS.md |
| "gas_stations does not exist" | Restore database from dump |
| Port 8000 not accessible | Check firewall with `sudo ufw status` |
| Secret not found | Create with `docker secret create` |

## Files in This Directory

- **README.md** (this file) - Overview and quick reference
- **QUICK_START.md** - Fast deployment guide
- **DEPLOY_WITH_SECRETS.md** - Detailed deployment documentation
- **DATABASE_OPERATIONS.md** - Database management guide

## Production Checklist

Before going live:

- [ ] Strong database password created
- [ ] Firewall configured (only ports 22, 8000 open)
- [ ] Automated backups configured
- [ ] Database restored and verified
- [ ] API tested from external IP
- [ ] Monitoring/logging set up (optional)
- [ ] Domain/SSL configured (optional)

## Monitoring

### Check Service Health

```bash
# Service status
docker stack ps gasapp

# Resource usage
docker stats

# Database connections
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT count(*) FROM pg_stat_activity"
```

### Logs

```bash
# Follow app logs
docker service logs gasapp_app --follow

# Last 100 lines
docker service logs gasapp_app --tail 100

# With timestamps
docker service logs gasapp_app --timestamps
```

## Updating and Maintenance

### Update Application Code

```bash
# 1. Transfer new code to VM
rsync -avz --exclude '__pycache__' /local/path/ user@vm:/opt/fastapi-retail-locations/

# 2. Rebuild image
docker build -t gasapp:latest .

# 3. Redeploy (rolling update)
docker stack deploy -c docker-compose.secrets.yml gasapp
```

### Database Maintenance

```bash
# Run ANALYZE (after data changes)
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "ANALYZE"

# VACUUM (weekly recommended)
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "VACUUM ANALYZE"
```

## Support and Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Docker Secrets**: https://docs.docker.com/engine/swarm/secrets/
- **PostGIS**: https://postgis.net/documentation/
- **PostgreSQL**: https://www.postgresql.org/docs/

## Contributing

When updating deployment docs:

1. Test all commands on a fresh VM
2. Update all relevant files (QUICK_START, DEPLOY_WITH_SECRETS, DATABASE_OPERATIONS)
3. Update this README if adding new files
4. Keep examples realistic and tested
