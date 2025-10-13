# Creating and Managing the Database


## Useful Docker commands

```bash
# Stop (graceful shutdown)
docker compose stop db

# Start again
docker compose start db

# Restart in one go
docker compose restart db

# Bring it up if the container doesn’t exist (or after `down`)
docker compose up -d db

# Bring the stack down (removes the container, keeps named volumes)
docker compose down

# ⚠️ DANGEROUS: also delete volumes (your data!) — usually do NOT run this
docker compose down -v

# Check status / logs
docker compose ps
docker compose logs -f db
```


## Bash command to create the schema

```bash

docker exec -it gasdb psql -U gasapp -d gas

```

This opens an interactive terminal (-it) PostgreSQL shell (psql) within Docker "gasdb" container where I (the user -U "gasapp") can run SQL queries against the "gas" database. 

Key SQL commands:

\dt - List all tables
SELECT * FROM users; - Query data
\q - Quit and exit

## Creating the initial schema (I'll tweak it later)

In the psql shell I'll execute:

```sql

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS gas_stations (
  id           BIGSERIAL PRIMARY KEY,
  station_key  TEXT UNIQUE NOT NULL,   -- natural/business key
  name         TEXT NOT NULL,
  brand        TEXT,
  address      TEXT,
  lat          DOUBLE PRECISION NOT NULL,
  lon          DOUBLE PRECISION NOT NULL,
  row_hash     TEXT NOT NULL,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  geom         GEOGRAPHY(Point,4326)
               GENERATED ALWAYS AS (
                 ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
               ) STORED,
  CHECK (lat BETWEEN -90 AND 90),
  CHECK (lon BETWEEN -180 AND 180)
);

CREATE INDEX IF NOT EXISTS gas_stations_geom_gix ON gas_stations USING GIST (geom);
CREATE INDEX IF NOT EXISTS gas_stations_brand_idx ON gas_stations (brand);

```

Indexes will allow faster spatial queries and brand lookups.





## Connect to VM

via SSH:

```bash
ssh root@<HETZNER_IP>
```







## Setting up the database on a VM

local Postgres/PostGIS (Docker) to a **Hetzner Cloud VM**

---

# Overview of the migration

**Recommended path:** do a **logical dump/restore** with `pg_dump` → `pg_restore`.
It’s safe across hosts, tolerant of version differences (same or newer PG is best), and easy to repeat.

---

## 1) Prepare Hetzner VM

1. **Create a server** (I use Ubuntu 24.04, 4 vCPU / 8 GB RAM, NVMe).
2. **Harden & update**

```bash
sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get -y install ufw docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

3. **Firewall (allow SSH; keep DB private)**

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

4. **API** on the same VM to avoid exposing Postgres publicly.

---

## 2) Start Postgres/PostGIS on Hetzner (Docker)

Create a folder on the VM, e.g. `~/db`, then add:

**`~/db/.env.db`**

```env
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
```

**`~/db/docker-compose.yml`**

```yaml
version: "3.9"
services:
  db:
    image: postgis/postgis:16-3.4
    container_name: gasdb
    env_file: .env.db
    # Bind to localhost only (no public exposure)
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 20
volumes:
  db_data:
```

Bring it up:

```bash
cd ~/db
docker compose up -d
```

> If your API runs on **the same VM**, you don’t need to expose port 5432 at all—remove the `ports:` section and connect to the container by name on the Docker network or via socket/localhost if using a sidecar.

---

## 3) Create schema & PostGIS on Hetzner (one-time)

```bash
docker exec -it gasdb psql -U gasapp -d gas -c "CREATE EXTENSION IF NOT EXISTS postgis"
docker exec -it gasdb psql -U gasapp -d gas <<'SQL'
CREATE TABLE IF NOT EXISTS gas_stations (
  id           BIGSERIAL PRIMARY KEY,
  station_key  TEXT UNIQUE NOT NULL,
  name         TEXT NOT NULL,
  brand        TEXT,
  address      TEXT,
  lat          DOUBLE PRECISION NOT NULL,
  lon          DOUBLE PRECISION NOT NULL,
  row_hash     TEXT NOT NULL,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  geom         GEOGRAPHY(Point,4326)
               GENERATED ALWAYS AS (
                 ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
               ) STORED,
  CHECK (lat BETWEEN -90 AND 90),
  CHECK (lon BETWEEN -180 AND 180)
);
CREATE INDEX IF NOT EXISTS gas_stations_geom_gix ON gas_stations USING GIST (geom);
CREATE INDEX IF NOT EXISTS gas_stations_brand_idx ON gas_stations (brand);
SQL
```

*(If you prefer to restore the schema from dump, you can skip the table creation.)*

---

## 4) Dump your **local** database (Mac)

> Do this on your machine where the local Docker PostGIS is running.

* **Dump roles (optional, if you have custom roles besides `gasapp`):**

```bash
pg_dumpall --globals-only -h localhost -p 5432 -U gasapp > globals.sql
```

* **Dump the DB (custom format is best):**

```bash
pg_dump -h localhost -p 5432 -U gasapp -d gas -Fc -f gas.dump
```

> If your `psql/pg_dump` aren’t installed locally, you can run them *inside the container*:
>
> ```bash
> docker exec -t gasdb pg_dump -U gasapp -d gas -Fc > gas.dump
> ```

---

## 5) Copy dump to the Hetzner VM

```bash
scp gas.dump globals.sql root@<HETZNER_IP>:~
```

*(Skip `globals.sql` if you didn’t create it.)*

---

## 6) Restore on the Hetzner VM

**Option A – simple restore into the existing `gas` DB (recommended for your case):**

```bash
# (optional) apply globals like CREATE ROLE statements
# docker exec -i gasdb psql -U gasapp -d postgres < ~/globals.sql

# restore schema+data
docker exec -i gasdb pg_restore \
  -U gasapp -d gas \
  --no-owner --no-privileges \
  < ~/gas.dump
```

**Option B – create a fresh empty DB and restore “as owner”**
(only if you dumped as a superuser and want to preserve owners):

```bash
docker exec -it gasdb psql -U gasapp -d postgres -c "DROP DATABASE IF EXISTS gas"
docker exec -it gasdb psql -U gasapp -d postgres -c "CREATE DATABASE gas"
docker exec -i gasdb pg_restore -U gasapp -d gas < ~/gas.dump
```

> If your dump contains `CREATE EXTENSION postgis`, it will be restored automatically. If not, keep step 3.

**Checks**

```bash
docker exec -it gasdb psql -U gasapp -d gas -c "SELECT postgis_full_version()"
docker exec -it gasdb psql -U gasapp -d gas -c "SELECT count(*) FROM gas_stations"
```

---

## 7) Connect app (securely)

* **Best:** keep Postgres bound to `127.0.0.1` and run your **API on the same VM** (or use a Hetzner **private network** between API and DB).
* **If you need remote access for admin:** use an **SSH tunnel** instead of opening 5432:

```bash
ssh -N -L 5432:127.0.0.1:5432 root@<HETZNER_IP>
# Then connect locally to localhost:5432 with your GUI/psql.
```

* Update your FastAPI `DATABASE_URL`, e.g. `postgresql+asyncpg://gasapp:change_me@localhost:5432/gas` (if API is co-located), or to the container name on a compose network.


## 9) Production hygiene

* **Backups**: nightly `pg_dump -Fc`, keep 7–14 days; consider WAL archiving when you scale.
* **Monitoring**: enable `pg_stat_statements`; watch disk, CPU, RAM, and latency.
* **Security**: keep 5432 private; strong passwords; rotate secrets; OS updates.
* **Performance**: after restore, run `ANALYZE;`:

```bash
docker exec -it gasdb psql -U gasapp -d gas -c "ANALYZE"
```

---

### TL;DR

1. Spin up a Hetzner VM and run the same **PostGIS Docker** you use locally (bind to localhost).
2. `pg_dump -Fc` locally → `scp` to server → `pg_restore` into the new DB.
3. Keep the DB private; co-locate your API or use an SSH tunnel/private network.

If you want, I can also give you a **one-file Bash script** that performs the dump, copy, and restore end-to-end.
