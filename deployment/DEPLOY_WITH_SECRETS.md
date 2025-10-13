# Deploying with Docker Secrets

This guide explains how to deploy the FastAPI Retail Locations app using Docker Secrets for secure password management.

## Prerequisites

- Docker installed on your VM
- SSH access to your VM
- Your application code transferred to VM

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

## Step 5: Verify Deployment

Check that containers are running:

```bash
# View running containers
docker ps

# Check logs
docker service logs gasapp_app
docker service logs gasapp_db

# Test the API
curl http://localhost:8000/health
```

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

### Check Container Logs

```bash
# For app service
docker service logs gasapp_app --follow

# For database service
docker service logs gasapp_db --follow
```

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
# Find the database container
docker ps | grep gasdb

# Create backup
docker exec gasdb pg_dump -U gasapp -d gas -Fc > gas_backup_$(date +%Y%m%d).dump
```

### Restore Database

```bash
# Copy backup to container
docker cp gas_backup.dump gasdb:/tmp/

# Restore
docker exec gasdb pg_restore -U gasapp -d gas --clean --if-exists < /tmp/gas_backup.dump

# Analyze
docker exec gasdb psql -U gasapp -d gas -c "ANALYZE"
```

## Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Stack Deploy](https://docs.docker.com/engine/reference/commandline/stack_deploy/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-password.html)
