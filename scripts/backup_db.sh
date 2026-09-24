#!/usr/bin/env bash
# ------------------------------------------------------------------------
# Description:
#
# Dumps the production PostgreSQL database to a timestamped, compressed
# file, then deletes backups older than RETENTION_DAYS. Meant to run on a
# schedule (cron), and right before scripts/deploy.sh applies a migration.
#
# Usage:
#   ./scripts/backup_db.sh
# ------------------------------------------------------------------------

set -euo pipefail        # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."  # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"        # the compose file describing the production services
BACKUP_DIR="${BACKUP_DIR:-./backups}"         # where dump files are stored; overridable via env
RETENTION_DAYS="${RETENTION_DAYS:-14}"        # how many days of backups to keep; overridable via env
POSTGRES_USER="${POSTGRES_USER:-cadri_user}"  # database user; overridable via env
POSTGRES_DB="${POSTGRES_DB:-cadri_db}"        # database name; overridable via env

TIMESTAMP="$(date +%Y-%m-%dT%H-%M-%S)"                  # current date/time, used to make each backup filename unique
BACKUP_FILE="$BACKUP_DIR/cadri_db_${TIMESTAMP}.sql.gz"  # full path of the backup file that is about to be created

mkdir -p "$BACKUP_DIR"  # create the backup directory if it doesn't already exist

echo "==> Dumping database to $BACKUP_FILE"  # progress message
# --clean adds DROP statements and --if-exists silences "does not exist"
# errors for objects that aren't there yet, so scripts/restore_db.sh can
# replay this dump directly onto a database that already has data in it,
# instead of failing on "relation already exists".
docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$POSTGRES_USER" --clean --if-exists "$POSTGRES_DB" | gzip > "$BACKUP_FILE"  # dump the DB inside the "db" container, compress it, save it

echo "==> Removing backups older than $RETENTION_DAYS days"                       # progress message
find "$BACKUP_DIR" -name 'cadri_db_*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete  # delete backup files past the retention window

echo "Backup complete: $BACKUP_FILE"  # success message
