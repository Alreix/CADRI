#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Description:
#
# Restores a backup produced by scripts/backup_db.sh. Destructive:
# overwrites the current database contents, so it refuses to run without
# an explicit confirmation flag.
#
# Usage:
#   ./scripts/restore_db.sh <path-to-backup.sql.gz> --yes-i-am-sure
# ----------------------------------------------------------------------

set -euo pipefail        # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."  # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"        # the compose file describing the production services
POSTGRES_USER="${POSTGRES_USER:-cadri_user}"  # database user; overridable via env
POSTGRES_DB="${POSTGRES_DB:-cadri_db}"        # database name; overridable via env

BACKUP_FILE="${1:-}"   # first argument: path to the backup file to restore
CONFIRM_FLAG="${2:-}"  # second argument: must be --yes-i-am-sure to proceed

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then         # bail out if no file was given, or it doesn't exist
    echo "Usage: $0 <path-to-backup.sql.gz> --yes-i-am-sure" >&2  # usage reminder, sent to stderr
    exit 1                                                        # exit with an error status
fi

if [ "$CONFIRM_FLAG" != "--yes-i-am-sure" ]; then                                          # refuse to run without the explicit confirmation flag
    echo "This overwrites the production database with the contents of $BACKUP_FILE." >&2  # warn about the consequence
    echo "Re-run with --yes-i-am-sure to confirm." >&2                                     # tell the operator how to actually run it
    exit 1                                                                                 # exit with an error status
fi

echo "==> Restoring $BACKUP_FILE into $POSTGRES_DB"                                                              # progress message
gunzip -c "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"  # decompress the backup and replay it into the database

echo "Restore complete."  # success message
