# Auto-Healing Scripts

## Overview

This directory contains automated fault detection and self-healing scripts for the AI Platform. These scripts are designed to automatically detect and fix common issues, reducing manual intervention and improving system reliability.

## Scripts

### 1. restart-container.sh

**Purpose**: Gracefully restart Docker containers with health checks and rollback capability.

**Usage**:
```bash
# Restart a container
./restart-container.sh ai-platform-backend

# Dry run (preview changes)
./restart-container.sh ai-platform-backend --dry-run
```

**Features**:
- Pre-restart state backup
- Graceful stop and start (30s timeout)
- Health check verification (30s timeout)
- Automatic retry (max 3 attempts)
- Automatic rollback on failure
- Detailed logging and reporting

**Exit Codes**:
- `0`: Success
- `1`: Failed with rollback
- `2`: Failed without rollback (manual intervention required)

**Logs**: `/var/log/ai-platform/ops/restart-container-YYYYMMDD.log`

---

### 2. cleanup-resources.sh

**Purpose**: Clean up Docker resources, temp files, and old logs to reclaim disk space.

**Usage**:
```bash
# Normal cleanup
./cleanup-resources.sh

# Dry run (preview changes)
./cleanup-resources.sh --dry-run

# Aggressive mode (remove old images)
./cleanup-resources.sh --aggressive

# Both
./cleanup-resources.sh --dry-run --aggressive
```

**What It Cleans**:
- Stopped containers
- Dangling images
- Unused volumes
- Unused networks
- Build cache
- Temp files (>1 day old)
- Old logs (>7 days)
- Old images (>30 days, aggressive mode only)

**Features**:
- Space usage reporting (before/after)
- Batch processing
- Safe deletion (preserves running containers)
- Detailed statistics

**Logs**: `/var/log/ai-platform/ops/cleanup-resources-YYYYMMDD.log`

---

### 3. reset-db-connections.sh

**Purpose**: Kill idle connections, slow queries, and reset database connection pool.

**Usage**:
```bash
# Reset default database
./reset-db-connections.sh

# Dry run
./reset-db-connections.sh --dry-run

# Specific database
./reset-db-connections.sh --db-name my_database

# Custom host
DB_HOST=db.example.com ./reset-db-connections.sh
```

**What It Does**:
- Kills idle connections (>5 minutes)
- Kills slow queries (>10 seconds)
- Resets connection pool
- Verifies recovery

**Environment Variables**:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name (default: ai_platform)

**Exit Codes**:
- `0`: Success
- `1`: Partial success (with warnings)

**Logs**: `/var/log/ai-platform/ops/reset-db-connections-YYYYMMDD.log`

---

### 4. cleanup-redis.sh

**Purpose**: Clean expired keys, analyze memory usage, and manage Redis cache namespaces.

**Usage**:
```bash
# General cleanup
./cleanup-redis.sh

# Dry run
./cleanup-redis.sh --dry-run

# Clean specific namespace
./cleanup-redis.sh --namespace cache

# Force clean large namespace (>100 keys)
./cleanup-redis.sh --namespace session --flush
```

**What It Does**:
- Cleans expired keys
- Analyzes key distribution by namespace
- Analyzes memory usage by key type
- Deletes namespace keys
- Optimizes memory

**Environment Variables**:
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)
- `REDIS_PASSWORD`: Redis password (optional)

**Features**:
- Key space analysis
- Memory usage statistics
- Safe namespace deletion (requires --flush for >100 keys)
- TTL analysis

**Logs**: `/var/log/ai-platform/ops/cleanup-redis-YYYYMMDD.log`

---

### 5. rotate-logs.sh

**Purpose**: Archive, compress, and delete old log files to manage disk space.

**Usage**:
```bash
# Normal rotation (30-day retention)
./rotate-logs.sh

# Dry run
./rotate-logs.sh --dry-run

# Custom retention (14 days)
./rotate-logs.sh --retention-days 14
```

**What It Does**:
- Compresses logs older than 1 day (gzip -9)
- Deletes logs older than retention period (default: 30 days)
- Deletes archives older than 90 days
- Maintains disk usage below 85%

**Managed Directories**:
- `/var/log/ai-platform/`
- `backend/logs/`
- `/var/log/nginx/`
- `/var/log/postgresql/`

**Features**:
- Automatic compression (gzip)
- Configurable retention
- Disk space monitoring
- Recursive directory processing

**Logs**: `/var/log/ai-platform/ops/rotate-logs-YYYYMMDD.log`

---

### 6. health-check.sh

**Purpose**: Check health status of all services and system resources.

**Usage**:
```bash
# Full health check (text format)
./health-check.sh

# JSON output
./health-check.sh --format json

# Summary only
./health-check.sh --format summary

# Check specific component
./health-check.sh --check docker
```

**Checks Performed**:
1. **CPU**: Usage percentage with thresholds
2. **Memory**: Usage and available memory
3. **Disk**: Usage and available space
4. **System Load**: 1/5/15 minute load averages
5. **Docker Containers**: Status and health of all containers
6. **PostgreSQL**: Database connectivity
7. **Redis**: Cache connectivity

**Output Formats**:
- `text`: Human-readable report (default)
- `json`: Machine-readable JSON
- `summary`: Brief status summary

**Thresholds**:
- CPU: Warning 70%, Critical 90%
- Memory: Warning 75%, Critical 90%
- Disk: Warning 75%, Critical 85%

**Exit Codes**:
- `0`: All checks healthy
- `2`: One or more critical checks

**Logs**: `/var/log/ai-platform/ops/health-check-YYYYMMDD.log`

---

## Integration with Auto-Healing System

These scripts are triggered automatically by the monitoring system when issues are detected:

### Trigger Conditions

| Script | Trigger | Threshold |
|--------|---------|-----------|
| `restart-container.sh` | Container unhealthy | Health check fails 3 times |
| `cleanup-resources.sh` | High disk usage | >85% disk usage |
| `reset-db-connections.sh` | High DB connections | >80% max connections |
| `cleanup-redis.sh` | High Redis memory | >80% max memory |
| `rotate-logs.sh` | High disk usage | >80% disk usage |
| `health-check.sh` | Periodic check | Every 5 minutes |

### Workflow

```
Monitoring System
    ↓
Detects Issue
    ↓
Evaluates Severity
    ↓
Selects Script
    ↓
Executes (with --dry-run first)
    ↓
Verifies Success
    ↓
Logs Result
    ↓
Sends Alert (if failed)
```

See: `backend/docs/AUTO_HEALING.md` for complete workflow details.

---

## Common Patterns

### Dry Run Mode

All scripts support `--dry-run` mode to preview changes without executing:

```bash
# Preview what would be cleaned
./cleanup-resources.sh --dry-run

# Preview container restart
./restart-container.sh mycontainer --dry-run
```

### Logging

All scripts log to `/var/log/ai-platform/ops/`:

```bash
# View recent logs
tail -f /var/log/ai-platform/ops/cleanup-resources-$(date +%Y%m%d).log

# Search for errors
grep ERROR /var/log/ai-platform/ops/*.log
```

### Exit Codes

Standard exit codes across all scripts:

- `0`: Success
- `1`: Failure (recoverable)
- `2`: Critical failure (manual intervention required)

---

## Safety Features

### Pre-Flight Checks

All scripts perform validation before execution:
- Dependency checking (docker, redis-cli, psql, etc.)
- Connection testing
- Permission verification

### State Backup

Scripts that modify state create backups:
- Container restart: JSON state dump
- Database reset: Connection snapshot
- Resource cleanup: Size statistics

### Rollback Capability

Critical scripts support automatic rollback:
- `restart-container.sh`: Restarts from backup state
- `reset-db-connections.sh`: Verifies recovery

### Rate Limiting

Scripts implement rate limiting to prevent abuse:
- Max 3 retry attempts
- 5-second delay between retries
- Exponential backoff on repeated failures

---

## Dependencies

### Required Commands

All scripts:
- `bash` (4.0+)
- `docker`
- `jq`
- `curl`

Database scripts:
- `psql`
- `pg_isready`

Redis scripts:
- `redis-cli`

Resource scripts:
- `du`, `df`, `find`, `gzip`

### Installation

Ubuntu/Debian:
```bash
apt-get install -y docker.io jq curl postgresql-client redis-tools gzip
```

CentOS/RHEL:
```bash
yum install -y docker jq curl postgresql redis gzip
```

macOS:
```bash
brew install docker jq curl postgresql redis gzip
```

---

## Monitoring and Alerting

### Metrics Collected

Each script reports:
- Execution time
- Resources cleaned/reclaimed
- Success/failure status
- Error details (if any)

### Alert Conditions

Alerts are sent when:
- Script fails after max retries
- Critical threshold exceeded
- Manual intervention required
- Unexpected errors occur

See: `backend/docs/FAULT_DIAGNOSIS.md` for alert configuration.

---

## Testing

### Unit Testing

Test each script individually:

```bash
# Test with dry-run
./restart-container.sh test-container --dry-run
./cleanup-resources.sh --dry-run
./reset-db-connections.sh --dry-run
./cleanup-redis.sh --dry-run
./rotate-logs.sh --dry-run
./health-check.sh --format summary
```

### Integration Testing

Test full workflow:

```bash
# 1. Create test container
docker run -d --name test-container nginx

# 2. Restart it
./restart-container.sh test-container

# 3. Check health
./health-check.sh --check docker

# 4. Cleanup
./cleanup-resources.sh
```

### Load Testing

Simulate high load:

```bash
# Create many stopped containers
for i in {1..10}; do
    docker create --name test-$i nginx
done

# Cleanup
./cleanup-resources.sh

# Verify
docker ps -a | grep test-
```

---

## Troubleshooting

### Script Won't Execute

```bash
# Check permissions
ls -l *.sh

# Fix if needed
chmod +x *.sh
```

### Dependencies Missing

```bash
# Check what's missing
./health-check.sh

# Install missing tools
# (see Dependencies section)
```

### Container Restart Fails

```bash
# Check container logs
docker logs <container_name>

# Check script logs
tail -100 /var/log/ai-platform/ops/restart-container-*.log

# Try manual restart
docker stop <container_name>
docker start <container_name>
```

### Database Connection Fails

```bash
# Test connection
pg_isready -h localhost -p 5432 -U postgres

# Check credentials
echo $DB_PASSWORD

# Check PostgreSQL logs
tail -100 /var/log/postgresql/postgresql-*.log
```

### Redis Cleanup Issues

```bash
# Test connection
redis-cli ping

# Check memory
redis-cli INFO memory

# Check key count
redis-cli DBSIZE
```

---

## Best Practices

### Scheduling

Run scripts via cron:

```cron
# Health check every 5 minutes
*/5 * * * * /path/to/health-check.sh --format json > /var/log/health.json

# Cleanup daily at 2am
0 2 * * * /path/to/cleanup-resources.sh

# Log rotation daily at 3am
0 3 * * * /path/to/rotate-logs.sh

# Redis cleanup weekly
0 4 * * 0 /path/to/cleanup-redis.sh
```

### Notifications

Integrate with alerting:

```bash
# Send Slack notification on failure
./restart-container.sh mycontainer || \
  curl -X POST https://hooks.slack.com/... -d '{"text":"Restart failed"}'

# Email on critical issues
./health-check.sh --format json | \
  jq -r 'select(.checks[] | .status == "critical") | @json' | \
  mail -s "Critical Health Check" ops@example.com
```

### Monitoring

Track script execution:

```bash
# Log to monitoring system
./cleanup-resources.sh 2>&1 | tee >(logger -t cleanup)

# Collect metrics
./health-check.sh --format json | \
  jq '.checks[] | {name, status}' > /var/lib/metrics/health.json
```

---

## References

- [Auto-Healing Documentation](../docs/AUTO_HEALING.md)
- [Fault Diagnosis Guide](../docs/FAULT_DIAGNOSIS.md)
- [Execution Guide](../EXECUTION_GUIDE.md)
- [Quick Reference](../QUICK_REFERENCE.md)

---

## Contributing

When adding new scripts:

1. Follow the existing script structure
2. Include `--dry-run` mode
3. Add comprehensive logging
4. Implement error handling
5. Document usage and examples
6. Add to this README
7. Update auto-healing workflow

---

## License

Copyright © 2024 AI Platform. All rights reserved.
