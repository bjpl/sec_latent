#!/bin/bash
# PostgreSQL Database Restore Script
# Restores database from backup with verification

set -e
set -u
set -o pipefail

# Configuration
ENVIRONMENT="${1:-staging}"
BACKUP_FILE="${2}"
LOG_FILE="/var/log/backups/postgres-restore.log"

# Database configuration
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-sec_latent}"
DB_USER="${POSTGRES_USER:-secuser}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Validate backup file
if [ -z "$BACKUP_FILE" ]; then
    error_exit "Backup file not specified. Usage: $0 <environment> <backup_file>"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Backup file not found: $BACKUP_FILE"
fi

log "Starting database restore for ${ENVIRONMENT} environment"
log "Backup file: $BACKUP_FILE"

# Pre-restore checks
log "Running pre-restore checks..."

# Confirm restore (require confirmation for production)
if [ "$ENVIRONMENT" = "production" ]; then
    read -p "WARNING: You are about to restore PRODUCTION database. Type 'yes' to continue: " confirmation
    if [ "$confirmation" != "yes" ]; then
        error_exit "Restore cancelled by user"
    fi
fi

# Check if database is accessible
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    error_exit "Database is not accessible"
fi

# Verify backup file integrity
log "Verifying backup file integrity..."
if ! gunzip -t "$BACKUP_FILE" 2>> "$LOG_FILE"; then
    error_exit "Backup file is corrupted"
fi

# Create pre-restore backup
log "Creating pre-restore backup..."
PRE_RESTORE_BACKUP="/tmp/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain --no-owner --no-acl | gzip > "$PRE_RESTORE_BACKUP"
log "Pre-restore backup saved: $PRE_RESTORE_BACKUP"

# Terminate existing connections
log "Terminating existing database connections..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
log "Dropping and recreating database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME};
EOF

# Restore database
log "Restoring database from backup..."
gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    2>> "$LOG_FILE"

if [ $? -ne 0 ]; then
    error_exit "Database restore failed"
fi

# Verify restore
log "Verifying database restore..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -eq 0 ]; then
    error_exit "Restore verification failed - no tables found"
fi

log "Restore verification passed: $TABLE_COUNT tables found"

# Run database migrations (if needed)
log "Running database migrations..."
# Uncomment if using Alembic or similar
# alembic upgrade head

# Update database statistics
log "Updating database statistics..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"

log "Database restore completed successfully"

# Send notification
if [ -n "${SLACK_WEBHOOK:-}" ]; then
    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"✅ Database restore completed\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                    {\"title\": \"Backup File\", \"value\": \"$(basename "$BACKUP_FILE")\", \"short\": true},
                    {\"title\": \"Tables Restored\", \"value\": \"$TABLE_COUNT\", \"short\": true},
                    {\"title\": \"Pre-restore Backup\", \"value\": \"$PRE_RESTORE_BACKUP\", \"short\": false}
                ]
            }]
        }"
fi

# Cleanup
unset PGPASSWORD

exit 0
