# Deploying with Docker Secrets

This guide explains how to deploy the FastAPI Retail Locations app using Docker Secrets for secure password management.

## Prerequisites

- Docker installed on your VM
- SSH access to your VM
- Your application code and database dump transferred to VM

### Transfer Files to VM

From your local machine:

```bash
# Transfer application code
rsync -avz --exclude '__pycache__' --exclude '.git' --exclude 'node_modules' \
  /path/to/fastapi-retail-locations/ user@your-vm:/opt/fastapi-retail-locations/

# Transfer database dump
scp gas.dump user@your-vm:/opt/fastapi-retail-locations/

# Or if dump is large, use rsync with compression
rsync -avz --progress gas.dump user@your-vm:/opt/fastapi-retail-locations/
```

**Note**: Replace `user@your-vm` with your actual username and VM IP address.

## Step 1: Initialize Docker Swarm

On your VM, initialize Swarm mode (required for Docker Secrets):

```bash
docker swarm init
```

If you have multiple network interfaces, you may need to specify which one:

```bash
docker swarm init --advertise-addr <your-vm-ip>
```

## Step 2: Create Docker Secrets

Create the database password secret:

```bash
# Create the secret (you'll be prompted to paste the password)
echo "YOUR_SECURE_PASSWORD_HERE" | docker secret create db_password -

# Verify the secret was created
docker secret ls
```

**Important**: Replace `YOUR_SECURE_PASSWORD_HERE` with your actual secure password.

### Generating a Strong Password

```bash
# Generate a random 32-character password
openssl rand -base64 32
```

## Step 3: Build the Application Image

Docker Stack doesn't build images, so build first:

```bash
cd /path/to/fastapi-retail-locations

# Build the application image
docker build -t gasapp:latest .
```

## Step 4: Deploy with Docker Stack

Use `docker stack deploy` instead of `docker compose up`:

```bash
# Deploy the stack
docker stack deploy -c docker-compose.secrets.yml gasapp

# Check status
docker stack services gasapp
docker stack ps gasapp
```

## Step 5: Wait for Database to Initialize

The database needs to initialize before restoring data:

```bash
# Watch database logs until ready
docker service logs gasapp_db --follow

# Wait for this message:
# "database system is ready to accept connections"
# Then press Ctrl+C
```

## Step 6: Restore Database from Dump

After the database is ready, restore your data:

```bash
# Copy dump file into the container
docker cp gas.dump $(docker ps -q -f name=gasapp_db):/tmp/gas.dump

# Restore the database
docker exec $(docker ps -q -f name=gasapp_db) pg_restore -U gasapp -d gas --clean --if-exists --no-owner --no-privileges /tmp/gas.dump

# Run ANALYZE to update query planner statistics
docker exec $(docker ps -q -f name=gasapp_db) psql -U gasapp -d gas -c "ANALYZE"

# Verify table exists and has data
docker exec $(docker ps -q -f name=gasapp_db) psql -U gasapp -d gas -c "SELECT COUNT(*) FROM gas_stations"
```

## Step 7: Verify Deployment

Check that services are running and API works:

```bash
# Check service status
docker stack ps gasapp

# Check logs
docker service logs gasapp_app
docker service logs gasapp_db

# Test the health endpoint
curl http://localhost:8000/health

# Test the API with real query
curl "http://localhost:8000/api/nearby?lat=51.5074&lon=-0.1278&km=10&limit=5"
```

## Accessing the API Externally

To access the API from outside the VM:

1. **Test from your local machine**:
   ```bash
   curl http://YOUR_VM_IP:8000/health
   ```

2. **If connection fails, check firewall**:
   ```bash
   # For UFW (Ubuntu)
   sudo ufw status
   sudo ufw allow 8000/tcp
   sudo ufw reload

   # For iptables
   sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
   sudo iptables-save
   ```

3. **Access API documentation**:
   Open `http://YOUR_VM_IP:8000/docs` in your browser for interactive API docs

## Managing Secrets

### View Secrets

```bash
# List all secrets
docker secret ls

# Inspect secret metadata (does NOT show the actual secret value)
docker secret inspect db_password
```

### Update a Secret

Secrets are immutable. To update:

```bash
# Create new secret with different name
echo "NEW_PASSWORD" | docker secret create db_password_v2 -

# Update your docker-compose.secrets.yml to reference db_password_v2
# Redeploy the stack
docker stack deploy -c docker-compose.secrets.yml gasapp

# Remove old secret after deployment succeeds
docker secret rm db_password
```

### Remove a Secret

```bash
# Stop services using the secret first
docker stack rm gasapp

# Then remove the secret
docker secret rm db_password
```

## Stopping and Starting

### Stop the Application

```bash
docker stack rm gasapp
```

### Start the Application

```bash
docker stack deploy -c docker-compose.secrets.yml gasapp
```

## Troubleshooting

### Error: "The network gasapp_app-network cannot be used with services"

This happens when a bridge network exists from a previous failed deployment. Fix:

```bash
# 1. Remove the stack
docker stack rm gasapp

# 2. Wait for cleanup
sleep 10

# 3. Remove any leftover networks
docker network ls | grep gasapp
docker network rm <network-name>  # Remove any gasapp networks

# 4. Verify docker-compose.secrets.yml has overlay driver
grep -A2 "app-network:" docker-compose.secrets.yml
# Should show: driver: overlay

# 5. Redeploy
docker stack deploy -c docker-compose.secrets.yml gasapp
```

### Error: "secret not found"

If you get this error, the secret wasn't created properly:

```bash
# List secrets to verify
docker secret ls

# Recreate if missing
echo "YOUR_PASSWORD" | docker secret create db_password -
```

### Error: "This node is not a swarm manager"

You need to initialize swarm mode:

```bash
docker swarm init
```

### Error: "relation 'gas_stations' does not exist"

This means you haven't restored the database yet. Follow Step 6 above to restore from dump.

### Service Not Starting

Check logs for specific errors:

```bash
# For app service
docker service logs gasapp_app --follow

# For database service
docker service logs gasapp_db --follow

# Check service status
docker stack ps gasapp --no-trunc
```

### Port 8000 Not Accessible Externally

1. Check service is running: `docker stack ps gasapp`
2. Check locally first: `curl http://localhost:8000/health`
3. Check firewall: `sudo ufw status`
4. Open port if needed: `sudo ufw allow 8000/tcp`

## Security Benefits

1. **Encrypted at rest**: Secrets are encrypted in the Swarm cluster
2. **Encrypted in transit**: Secrets are sent over encrypted channels to containers
3. **No plaintext files**: Passwords never stored in plaintext on disk (except temporarily in memory)
4. **Access control**: Only services explicitly granted access can read secrets
5. **Audit trail**: Docker logs which services access which secrets

## Migrating from .env to Secrets

If you're currently using `.env`:

1. Deploy with secrets using instructions above
2. Verify everything works
3. Delete or secure your `.env` file:

```bash
# Securely delete (if available)
shred -u .env

# Or just remove
rm .env
```

## Backup and Recovery

### Backup Database

```bash
# Find the database container ID
docker ps | grep gasapp_db

# Create backup using custom format (recommended)
docker exec $(docker ps -q -f name=gasapp_db) pg_dump -U gasapp -d gas -Fc > gas_backup_$(date +%Y%m%d).dump

# Or plain SQL format
docker exec $(docker ps -q -f name=gasapp_db) pg_dump -U gasapp -d gas > gas_backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Copy backup to container
docker cp gas_backup.dump $(docker ps -q -f name=gasapp_db):/tmp/

# Restore from custom format dump
docker exec $(docker ps -q -f name=gasapp_db) pg_restore -U gasapp -d gas --clean --if-exists --no-owner --no-privileges /tmp/gas_backup.dump

# Or restore from SQL format
docker exec -i $(docker ps -q -f name=gasapp_db) psql -U gasapp -d gas < gas_backup.sql

# Always run ANALYZE after restore
docker exec $(docker ps -q -f name=gasapp_db) psql -U gasapp -d gas -c "ANALYZE"
```

### Automated Backups

Create a cron job for automated backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * docker exec $(docker ps -q -f name=gasapp_db) pg_dump -U gasapp -d gas -Fc > /backup/gas_$(date +\%Y\%m\%d).dump
```

## Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Stack Deploy](https://docs.docker.com/engine/reference/commandline/stack_deploy/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-password.html)
