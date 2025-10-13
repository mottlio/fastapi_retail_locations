# FastAPI app serving data on retail sites from a PostgreSQL/PostGIS database

This repository contains a FastAPI application that serves data on retail sites from a PostgreSQL/PostGIS database. The application provides endpoints to retrieve information about retail locations, including their geographical data, address, name, brand, services offered.

## Data
The data is stored in a PostgreSQL database with PostGIS extension enabled. 

The database contains a current snapshot of data aggregated from multiple sources including company websites, OpenStreetMaps, government data, and other public datasets. The data is updated periodically to ensure accuracy. Data is transformed in a data warehouse before being loaded into the PostgreSQL database.

## Features

- Retrieve the closest retail sites based on latitude and longitude. Options to filter by distance brand and services.

## Running the app

1. Ensure you have Docker and Docker Compose installed on your machine.
2. Clone this repository to your local machine.
3. Navigate to the project directory.
4. Build and run the Docker containers using Docker Compose:

   ```bash
   docker compose up --build
   ```
5. The FastAPI app will be accessible at `http://localhost:8000`.

## Docker Deployment (Production)

This project includes Docker support for production deployment on a VM.

### Prerequisites on VM

1. **Install Docker and Docker Compose**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-plugin
   sudo usermod -aG docker $USER
   ```

2. **Setup firewall** (Ubuntu/Debian):
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 8000/tcp  # For FastAPI app
   sudo ufw enable
   ```

### Initial Deployment

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd my-python-project
   ```

2. **Create `.env` file** from the template:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your secure passwords
   ```

3. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

   Or manually:
   ```bash
   docker compose up -d --build
   ```

### Architecture

The `docker-compose.yml` sets up:
- **Database (db)**: PostgreSQL 16 with PostGIS 3.4
  - Bound to `127.0.0.1:5432` (localhost only for security)
  - Persistent storage with Docker volume
  - Health checks enabled
- **Application (app)**: FastAPI app
  - Built from Dockerfile
  - Exposed on port 8000
  - Waits for database health check
  - Runs as non-root user
  - Includes health checks

### Updating Deployment

When you push new code, on the VM:

```bash
./deploy.sh
```

Or step by step:
```bash
git pull origin main
docker compose build
docker compose down
docker compose run --rm app alembic upgrade head
docker compose up -d
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Just the app
docker compose logs -f app

# Just the database
docker compose logs -f db
```

### Managing Services

```bash
# Stop all services
docker compose stop

# Start all services
docker compose start

# Restart a specific service
docker compose restart app

# View running containers
docker compose ps

# Remove everything (keeps volumes)
docker compose down

# Remove everything including volumes (⚠️ DATA LOSS)
docker compose down -v
```

## Database Migrations with Alembic

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Alembic tracks changes to your database schema over time, making it easy to version control your database structure alongside your code.

### Configuration

Alembic is configured to:
- Use async SQLAlchemy with asyncpg
- Automatically read database credentials from your `.env` file via `app.db.DATABASE_URL`
- Handle URL-encoded passwords (including special characters)

### Initial Setup

If you're setting up the database for the first time:

1. **Start the database**:
   ```bash
   cd db
   docker compose up -d
   ```

2. **Run migrations** to create the schema:
   ```bash
   alembic upgrade head
   ```

This will create all necessary tables and indexes in your database.

### Creating New Migrations

When you need to modify the database schema (add columns, tables, indexes, etc.):

1. **Create a new migration file**:
   ```bash
   alembic revision -m "Add services column to gas_stations"
   ```

2. **Edit the generated file** in `alembic/versions/` to add your schema changes using the `upgrade()` and `downgrade()` functions.

3. **Apply the migration**:
   ```bash
   alembic upgrade head
   ```

### Common Alembic Commands

```bash
# View current migration version
alembic current

# View migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# View SQL without executing (dry run)
alembic upgrade head --sql
```

### Production Deployment

When deploying to production (e.g., via `git pull` on a VM):

1. Pull the latest code:
   ```bash
   git pull origin main
   ```

2. Apply any new migrations:
   ```bash
   alembic upgrade head
   ```

3. Restart your application:
   ```bash
   # If using systemd
   sudo systemctl restart myapp

   # If using Docker Compose
   docker compose restart app
   ```

**Important**: Always backup your database before running migrations in production:
```bash
docker exec gasdb pg_dump -U gasapp -d gas -Fc -f /tmp/backup_$(date +%Y%m%d_%H%M%S).dump
```

## OpenAPI Documentation

You can also view the interactive API docs at:
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc