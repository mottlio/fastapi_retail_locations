# Database Operations Guide

This guide covers common database operations for the FastAPI Retail Locations application.

## Table of Contents

- [Initial Database Setup](#initial-database-setup)
- [Restore from Dump](#restore-from-dump)
- [Backup Database](#backup-database)
- [Database Maintenance](#database-maintenance)
- [Common Database Tasks](#common-database-tasks)
- [Troubleshooting](#troubleshooting)

## Initial Database Setup

### For Docker Swarm Deployment

After deploying with `docker stack deploy`, the database container will automatically:
- Create the `gas` database
- Install PostGIS extensions
- Be ready for data restoration

You then need to restore your data from a dump file.

### Getting Database Container ID

```bash
# Find the container
docker ps | grep gasapp_db

# Or get just the ID
docker ps -q -f name=gasapp_db
```

## Restore from Dump

### Standard Restore Process

```bash
# 1. Copy dump file into container
docker cp gas.dump $(docker ps -q -f name=gasapp_db):/tmp/gas.dump

# 2. Restore using pg_restore (for .dump files)
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas \
  --clean --if-exists \
  --no-owner --no-privileges \
  /tmp/gas.dump

# 3. Run ANALYZE to update statistics
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "ANALYZE"

# 4. Verify data was restored
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT COUNT(*) FROM gas_stations"
```

### Restore from SQL File

If you have a plain SQL dump:

```bash
# Copy SQL file to container
docker cp gas_backup.sql $(docker ps -q -f name=gasapp_db):/tmp/

# Restore SQL file
docker exec -i $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas < gas_backup.sql

# Run ANALYZE
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "ANALYZE"
```

### Restore Options Explained

- `--clean`: Drop database objects before recreating
- `--if-exists`: Don't error if objects don't exist
- `--no-owner`: Don't restore ownership
- `--no-privileges`: Don't restore access privileges
- `-Fc`: Custom format (for pg_dump)

## Backup Database

### Create Backup (Custom Format - Recommended)

```bash
# Backup to local machine
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_dump -U gasapp -d gas -Fc > gas_backup_$(date +%Y%m%d).dump

# Verify backup was created
ls -lh gas_backup_*.dump
```

### Create Backup (SQL Format)

```bash
# Plain SQL format (more portable, larger file)
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_dump -U gasapp -d gas > gas_backup_$(date +%Y%m%d).sql
```

### Backup with Compression (SQL)

```bash
# SQL with gzip compression
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_dump -U gasapp -d gas | gzip > gas_backup_$(date +%Y%m%d).sql.gz
```

### Automated Backups

Create a backup script:

```bash
# Create backup script
cat > /opt/backup-gasdb.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/gasdb"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec $(docker ps -q -f name=gasapp_db) \
  pg_dump -U gasapp -d gas -Fc > $BACKUP_DIR/gas_$DATE.dump

# Keep only last 7 days of backups
find $BACKUP_DIR -name "gas_*.dump" -mtime +7 -delete

echo "Backup completed: gas_$DATE.dump"
EOF

# Make executable
chmod +x /opt/backup-gasdb.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-gasdb.sh") | crontab -
```

## Database Maintenance

### Run ANALYZE

Update query planner statistics (run after data changes):

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "ANALYZE"
```

### Run VACUUM

Reclaim storage and update statistics:

```bash
# Standard VACUUM
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "VACUUM ANALYZE"

# VACUUM FULL (locks tables, more thorough)
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "VACUUM FULL ANALYZE"
```

### Rebuild Indexes

```bash
# Rebuild all indexes in gas_stations table
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "REINDEX TABLE gas_stations"
```

## Common Database Tasks

### Connect to Database Shell

```bash
# Interactive psql session
docker exec -it $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas
```

Common psql commands:
- `\dt` - List tables
- `\d gas_stations` - Describe table schema
- `\di` - List indexes
- `\l` - List databases
- `\du` - List users
- `\q` - Quit

### Check Table Statistics

```bash
# Row count
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT COUNT(*) FROM gas_stations"

# Table size
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT pg_size_pretty(pg_total_relation_size('gas_stations'))"

# Database size
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT pg_size_pretty(pg_database_size('gas'))"
```

### Query Sample Data

```bash
# View first 10 records
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT * FROM gas_stations LIMIT 10"

# Count by brand
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT brand, COUNT(*) FROM gas_stations GROUP BY brand ORDER BY COUNT(*) DESC LIMIT 10"
```

### Check PostGIS Version

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT postgis_full_version()"
```

### Verify Spatial Index

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "\d gas_stations"

# Should show GIST index on geom column
```

## Troubleshooting

### Error: "relation gas_stations does not exist"

The table hasn't been created yet. You need to restore from dump:

```bash
# Follow restore process above
docker cp gas.dump $(docker ps -q -f name=gasapp_db):/tmp/gas.dump
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas --clean --if-exists --no-owner --no-privileges /tmp/gas.dump
```

### Error: "must be owner of table"

Use `--no-owner` flag with pg_restore:

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas --no-owner --no-privileges /tmp/gas.dump
```

### Error: "permission denied"

Make sure you're using the correct database user (`gasapp`):

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT current_user"
```

### Database Connection Timeout

Check if database is running:

```bash
# Check container status
docker ps | grep gasapp_db

# Check database logs
docker service logs gasapp_db --tail 50

# Test connection
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT 1"
```

### Restore Taking Too Long

For large databases:

```bash
# Use verbose mode to see progress
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas -v \
  --no-owner --no-privileges /tmp/gas.dump

# Or restore without indexes first, then create them
docker exec $(docker ps -q -f name=gasapp_db) \
  pg_restore -U gasapp -d gas \
  --no-owner --no-privileges \
  --disable-triggers \
  /tmp/gas.dump
```

### Check for Blocked Queries

```bash
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT pid, usename, state, query FROM pg_stat_activity WHERE state != 'idle'"
```

### Kill Long-Running Query

```bash
# Find the PID from above query, then:
docker exec $(docker ps -q -f name=gasapp_db) \
  psql -U gasapp -d gas -c "SELECT pg_terminate_backend(PID)"
```

## Performance Tips

1. **Always run ANALYZE** after restoring data
2. **Regular VACUUM** prevents table bloat
3. **Monitor index usage** with pg_stat_user_indexes
4. **Use EXPLAIN ANALYZE** to optimize slow queries
5. **Adjust connection pool** settings in app/db.py if needed

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [pg_restore Documentation](https://www.postgresql.org/docs/current/app-pgrestore.html)
