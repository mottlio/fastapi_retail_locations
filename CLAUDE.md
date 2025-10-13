# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI application serving retail site data (specifically gas stations) from a PostgreSQL/PostGIS database. The app provides geospatial queries to find nearby retail locations based on latitude/longitude coordinates.

## Architecture

### Two-Tier Architecture
- **FastAPI app** (`app/main.py`): Single endpoint `/api/nearby` for proximity search, plus `/health` endpoint
- **PostgreSQL/PostGIS database**: Stores retail locations with geospatial data in `gas_stations` table

### Database Layer (`app/db.py`)
- Uses SQLAlchemy async with `asyncpg` driver
- Connection pooling: 10 base connections, 10 max overflow
- Database configuration via environment variables: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- Password URL encoding handled automatically with `urllib.parse.quote_plus`
- Single pre-compiled spatial query (`NEARBY_SQL`) using PostGIS `ST_Distance` and `ST_DWithin` functions

### Key Database Schema
Table `gas_stations`:
- Primary key: `id` (BIGSERIAL)
- Business key: `station_key` (TEXT, unique)
- Attributes: `name`, `brand`, `address`, `lat`, `lon`, `row_hash`, `updated_at`
- Generated column: `geom` (GEOGRAPHY Point, computed from lat/lon)
- Indexes: GIST index on `geom` for spatial queries, B-tree on `brand`

## Development Commands

### Running the Application

Start the database (from `db/` directory):
```bash
cd db
docker compose up -d
```

Run the FastAPI app:
```bash
uvicorn app.main:app --reload
```

Access the API at `http://localhost:8000`

### Database Management

Connect to the database via psql:
```bash
docker exec -it gasdb psql -U gasapp -d gas
```

Common psql commands:
- `\dt` - List all tables
- `\d gas_stations` - Describe table schema
- `SELECT postgis_full_version()` - Check PostGIS version
- `\q` - Quit

Docker database commands:
```bash
# View logs
docker compose logs -f db

# Restart database
docker compose restart db

# Stop database
docker compose stop db

# Start database
docker compose start db

# Bring down (keeps volumes)
docker compose down

# Check status
docker compose ps
```

### Database Schema Setup

The initial schema creation SQL is documented in `db/manual.md`. To create from scratch:
```bash
docker exec -it gasdb psql -U gasapp -d gas -c "CREATE EXTENSION IF NOT EXISTS postgis"
```

Then run the full schema SQL from `db/manual.md` (lines 52-76).

### Data Migration

For production deployment, the project uses logical dump/restore:
```bash
# Dump from local
pg_dump -h localhost -p 5432 -U gasapp -d gas -Fc -f gas.dump

# Or from within container
docker exec -t gasdb pg_dump -U gasapp -d gas -Fc > gas.dump

# Restore on target
docker exec -i gasdb pg_restore -U gasapp -d gas --no-owner --no-privileges < gas.dump
```

After restore, always run:
```bash
docker exec -it gasdb psql -U gasapp -d gas -c "ANALYZE"
```

## Project Configuration

- **Package manager**: `uv` (see `uv.lock`)
- **Python version**: >=3.12.11
- **Dependencies**: FastAPI 0.119.0+, Uvicorn 0.37.0+, SQLAlchemy (async), asyncpg
- **Database defaults**: User `gasapp`, database `gas`, port `5432`, container name `gasdb`

## Data Sources

Data is aggregated from multiple sources including company websites, OpenStreetMaps, government data, and other public datasets. Data is transformed in a data warehouse before loading into PostgreSQL. The database contains a current snapshot updated periodically.

## Important Implementation Notes

- The `/api/nearby` endpoint clamps the `limit` parameter between 1 and 100 to prevent excessive queries
- All spatial calculations use the geography type with SRID 4326 (WGS84)
- Distance calculations return kilometers
- The health check performs a lightweight `SELECT 1` query to verify database connectivity
- Password encoding in database URL is critical for special characters
