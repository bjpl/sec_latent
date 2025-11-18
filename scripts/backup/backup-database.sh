#!/bin/bash
# Database Backup Script for SEC Latent
# Supports PostgreSQL, DuckDB, and Redis backups with encryption and rotation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/sec-latent}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
S3_BUCKET="${S3_BUCKET:-}"
ENVIRONMENT="${1:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_tools=()

    command -v pg_dump >/dev/null 2>&1 || missing_tools+=("postgresql-client")
    command -v redis-cli >/dev/null 2>&1 || missing_tools+=("redis-tools")
    command -v openssl >/dev/null 2>&1 || missing_tools+=("openssl")

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    log_info "All prerequisites met"
}

# Create backup directory
create_backup_dir() {
    local date_dir="$BACKUP_DIR/$(date +%Y-%m-%d)"
    mkdir -p "$date_dir"
    echo "$date_dir"
}

# Backup PostgreSQL database
backup_postgres() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/postgres_${ENVIRONMENT}_${timestamp}.sql"

    log_info "Starting PostgreSQL backup..."

    # Get database credentials from environment or k8s secrets
    if [ "$ENVIRONMENT" = "production" ]; then
        PGHOST="${PGHOST:-sec-latent-postgres.sec-latent.svc.cluster.local}"
        PGUSER="${PGUSER:-secuser}"
        PGDATABASE="${PGDATABASE:-sec_latent}"
    else
        PGHOST="${PGHOST:-localhost}"
        PGUSER="${PGUSER:-secuser}"
        PGDATABASE="${PGDATABASE:-sec_latent}"
    fi

    # Perform backup
    PGPASSWORD="${PGPASSWORD}" pg_dump \
        -h "$PGHOST" \
        -U "$PGUSER" \
        -d "$PGDATABASE" \
        --format=custom \
        --compress=9 \
        --file="$backup_file" \
        --verbose

    if [ $? -eq 0 ]; then
        log_info "PostgreSQL backup completed: $backup_file"

        # Calculate checksum
        sha256sum "$backup_file" > "$backup_file.sha256"

        # Encrypt if key provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            encrypt_backup "$backup_file"
        fi

        echo "$backup_file"
    else
        log_error "PostgreSQL backup failed"
        return 1
    fi
}

# Backup DuckDB database
backup_duckdb() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/duckdb_${ENVIRONMENT}_${timestamp}.db"

    log_info "Starting DuckDB backup..."

    local duckdb_path="${DUCKDB_PATH:-/app/data/sec_filings.duckdb}"

    if [ -f "$duckdb_path" ]; then
        cp "$duckdb_path" "$backup_file"
        gzip "$backup_file"
        backup_file="${backup_file}.gz"

        log_info "DuckDB backup completed: $backup_file"

        # Calculate checksum
        sha256sum "$backup_file" > "$backup_file.sha256"

        # Encrypt if key provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            encrypt_backup "$backup_file"
        fi

        echo "$backup_file"
    else
        log_warn "DuckDB file not found: $duckdb_path"
    fi
}

# Backup Redis data
backup_redis() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/redis_${ENVIRONMENT}_${timestamp}.rdb"

    log_info "Starting Redis backup..."

    if [ "$ENVIRONMENT" = "production" ]; then
        REDIS_HOST="${REDIS_HOST:-sec-latent-redis.sec-latent.svc.cluster.local}"
    else
        REDIS_HOST="${REDIS_HOST:-localhost}"
    fi

    # Trigger BGSAVE
    redis-cli -h "$REDIS_HOST" -a "${REDIS_PASSWORD}" BGSAVE

    # Wait for BGSAVE to complete
    while [ "$(redis-cli -h "$REDIS_HOST" -a "${REDIS_PASSWORD}" LASTSAVE)" = "$(date +%s)" ]; do
        sleep 1
    done

    # Copy RDB file
    local redis_data_dir="${REDIS_DATA_DIR:-/var/lib/redis}"
    if [ -f "$redis_data_dir/dump.rdb" ]; then
        cp "$redis_data_dir/dump.rdb" "$backup_file"
        gzip "$backup_file"
        backup_file="${backup_file}.gz"

        log_info "Redis backup completed: $backup_file"

        # Calculate checksum
        sha256sum "$backup_file" > "$backup_file.sha256"

        # Encrypt if key provided
        if [ -n "$ENCRYPTION_KEY" ]; then
            encrypt_backup "$backup_file"
        fi

        echo "$backup_file"
    else
        log_warn "Redis dump file not found"
    fi
}

# Encrypt backup file
encrypt_backup() {
    local file="$1"

    log_info "Encrypting backup: $file"

    openssl enc -aes-256-cbc \
        -salt \
        -in "$file" \
        -out "${file}.enc" \
        -pass pass:"$ENCRYPTION_KEY"

    if [ $? -eq 0 ]; then
        rm "$file"
        log_info "Backup encrypted: ${file}.enc"
    else
        log_error "Encryption failed"
        return 1
    fi
}

# Upload to S3
upload_to_s3() {
    local backup_dir="$1"

    if [ -z "$S3_BUCKET" ]; then
        log_warn "S3_BUCKET not configured, skipping upload"
        return
    fi

    log_info "Uploading backups to S3..."

    aws s3 sync "$backup_dir" "s3://$S3_BUCKET/sec-latent-backups/$(date +%Y-%m-%d)/" \
        --storage-class STANDARD_IA \
        --exclude "*" \
        --include "*.sql*" \
        --include "*.db.gz*" \
        --include "*.rdb.gz*" \
        --include "*.sha256"

    if [ $? -eq 0 ]; then
        log_info "Backups uploaded to S3"
    else
        log_error "S3 upload failed"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."

    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -type d -empty -delete

    # Cleanup old S3 backups
    if [ -n "$S3_BUCKET" ]; then
        aws s3 ls "s3://$S3_BUCKET/sec-latent-backups/" | while read -r line; do
            backup_date=$(echo "$line" | awk '{print $2}' | cut -d'/' -f1)
            if [ -n "$backup_date" ]; then
                age_days=$(( ($(date +%s) - $(date -d "$backup_date" +%s)) / 86400 ))
                if [ $age_days -gt $RETENTION_DAYS ]; then
                    aws s3 rm "s3://$S3_BUCKET/sec-latent-backups/$backup_date/" --recursive
                    log_info "Deleted old S3 backup: $backup_date"
                fi
            fi
        done
    fi

    log_info "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"

    log_info "Verifying backup integrity: $backup_file"

    if [ -f "${backup_file}.sha256" ]; then
        sha256sum -c "${backup_file}.sha256"
        if [ $? -eq 0 ]; then
            log_info "Backup integrity verified"
            return 0
        else
            log_error "Backup integrity check failed"
            return 1
        fi
    else
        log_warn "Checksum file not found, skipping verification"
    fi
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"

    # Send to Sentry
    if [ -n "${SENTRY_DSN:-}" ]; then
        curl -X POST "${SENTRY_DSN}" \
            -H "Content-Type: application/json" \
            -d "{\"message\": \"Backup $status: $message\", \"level\": \"${status}\"}"
    fi

    # Send email notification if configured
    if [ -n "${ALERT_EMAIL:-}" ]; then
        echo "$message" | mail -s "SEC Latent Backup $status" "$ALERT_EMAIL"
    fi
}

# Main backup process
main() {
    log_info "Starting backup process for environment: $ENVIRONMENT"

    check_prerequisites

    local backup_dir=$(create_backup_dir)
    log_info "Backup directory: $backup_dir"

    local backup_files=()
    local failed_backups=()

    # Perform backups
    if postgres_backup=$(backup_postgres "$backup_dir"); then
        backup_files+=("$postgres_backup")
    else
        failed_backups+=("PostgreSQL")
    fi

    if duckdb_backup=$(backup_duckdb "$backup_dir"); then
        backup_files+=("$duckdb_backup")
    else
        failed_backups+=("DuckDB")
    fi

    if redis_backup=$(backup_redis "$backup_dir"); then
        backup_files+=("$redis_backup")
    else
        failed_backups+=("Redis")
    fi

    # Upload to S3
    upload_to_s3 "$backup_dir"

    # Cleanup old backups
    cleanup_old_backups

    # Report status
    if [ ${#failed_backups[@]} -eq 0 ]; then
        log_info "All backups completed successfully"
        send_notification "success" "All backups completed successfully"
        exit 0
    else
        log_error "Some backups failed: ${failed_backups[*]}"
        send_notification "error" "Backup failures: ${failed_backups[*]}"
        exit 1
    fi
}

# Run main function
main
