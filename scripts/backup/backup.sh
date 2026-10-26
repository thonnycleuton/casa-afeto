#!/bin/sh
# Casa Afeto — Automated PostgreSQL Backup Script
# Runs inside the backup container via cron

set -e

BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION:-7}"
SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"

# Install cron if not present
if ! command -v crontab >/dev/null 2>&1; then
    apk add --no-cache cron
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup function
do_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

    echo "Starting backup at $(date)"
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_SERVER" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --clean --if-exists \
        | gzip > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        echo "Backup completed: $BACKUP_FILE"
    else
        echo "Backup failed!" >&2
        exit 1
    fi

    # Remove old backups
    echo "Cleaning backups older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

    echo "Backup process finished at $(date)"
}

# Run initial backup
do_backup

# Set up cron for recurring backups
echo "$SCHEDULE /backup-scripts/backup.sh" | crontab -

# Start cron in foreground to keep container alive
crond -f
