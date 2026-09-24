#!/usr/bin/env bash
# -----------------------------------------------------------------------
# Description:
#
# Applies pending Alembic migrations to the production database. Meant to
# be called by scripts/deploy.sh — never run `flask db upgrade` by hand
# against production, a typo is much harder to undo there.
#
# Usage:
#   ./scripts/migrate.sh
# -----------------------------------------------------------------------

set -euo pipefail        # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."  # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"  # the compose file describing the production services

echo "==> Running database migrations"                               # progress message for whoever is watching the deploy
docker compose -f "$COMPOSE_FILE" run --rm backend flask db upgrade  # start a throwaway backend container, apply migrations, remove the container
