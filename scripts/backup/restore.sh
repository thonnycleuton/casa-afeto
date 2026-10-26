#!/bin/sh
# Casa Afeto — PostgreSQL Restore Script
# Usage: ./restore.sh <backup_file.sql.gz>
# Example: ./restore.sh /backups/backup_20261026_020000.sql.gz

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lt /backups/backup_*.sql.gz 2>/dev/null || echo "No backups found."
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"
echo "Database: $POSTGRES_DB @ $POSTGRES_SERVER:$POSTGRES_PORT"
echo ""
echo "WARNING: This will drop and recreate all tables in the database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read -r

gunzip -c "$BACKUP_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_SERVER" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB"

echo "Restore completed at $(date)"
