#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Description:
#
# Deploys the latest version of CADRI to this server: pulls the code,
# rebuilds the images, ensures PostgreSQL is available, backs up the
# database, applies pending migrations, starts the application services,
# then waits for the backend to report healthy.
#
# Usage:
#   ./scripts/deploy.sh
#   (also invoked by .github/workflows/deploy.yml over SSH)
# ----------------------------------------------------------------------

set -euo pipefail        # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."  # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"                    # the compose file describing the production services
BACKEND_CONTAINER="${BACKEND_CONTAINER:-cadri_backend}"   # container_name of the backend service, overridable via env
DB_CONTAINER="${DB_CONTAINER:-cadri_db}"                  # container_name of the PostgreSQL service, overridable via env

echo "==> Pulling latest code"
git pull --ff-only origin main      # update from main only if Git can fast-forward; refuse an unexpected server-side merge

echo "==> Building updated images"
docker compose -f "$COMPOSE_FILE" build  # rebuild the Docker images with the freshly pulled code

echo "==> Starting database"                 # make sure PostgreSQL exists and is running before backup/migrations
docker compose -f "$COMPOSE_FILE" up -d db  # start only the database service; its persistent volume keeps existing data

echo "==> Waiting for PostgreSQL to become healthy"  # do not continue until Docker's database healthcheck succeeds
for attempt in $(seq 1 10); do                         # retry up to 10 times instead of failing while PostgreSQL is still starting
    DB_HEALTH_STATUS="$(
        docker inspect \
            --format='{{.State.Health.Status}}' \
            "$DB_CONTAINER" \
            2>/dev/null || echo "unknown"
    )"  # ask Docker for the database container's current health status

    if [ "$DB_HEALTH_STATUS" = "healthy" ]; then  # PostgreSQL is ready to accept connections
        echo "Database is healthy."
        break  # leave the retry loop and continue the deployment
    fi

    if [ "$attempt" -eq 10 ]; then  # after the final attempt, stop instead of running backup/migrations against an unavailable DB
        echo "Database did not become healthy in time." >&2
        echo "Check 'docker compose -f $COMPOSE_FILE logs db'." >&2
        exit 1
    fi

    echo "Database not healthy yet (status: $DB_HEALTH_STATUS, attempt $attempt/10), retrying in 3s..."  # progress message between retries
    sleep 3  # give PostgreSQL a few seconds before checking again
done

echo "==> Backing up the database before migrating"
./scripts/backup_db.sh  # snapshot the pre-migration state, so a bad migration can still be undone

echo "==> Applying database migrations"  
./scripts/migrate.sh                     # run pending migrations before the new code starts using the database

echo "==> Starting application services"
docker compose -f "$COMPOSE_FILE" up -d          # recreate/start every production service in the background

echo "==> Waiting for the backend to report healthy"
for attempt in $(seq 1 10); do  # retry up to 10 times instead of failing on the first slow start
    HEALTH_STATUS="$(
        docker inspect \
            --format='{{.State.Health.Status}}' \
            "$BACKEND_CONTAINER" \
            2>/dev/null || echo "unknown"
    )"  # ask Docker for the backend container's health check result

    if [ "$HEALTH_STATUS" = "healthy" ]; then  # Docker itself already ran the check defined in docker-compose.prod.yml
        echo "Backend is up. Deployment complete."  # success message
        exit 0  # stop the script here: the deployment succeeded
    fi

    echo "Backend not healthy yet (status: $HEALTH_STATUS, attempt $attempt/10), retrying in 3s..."  # progress message between retries
    sleep 3  # wait a few seconds before checking again
done

echo "Backend did not become healthy in time." >&2                                                     # error message, sent to stderr
echo "Check 'docker compose -f $COMPOSE_FILE logs backend', then consider ./scripts/rollback.sh." >&2  # guidance for whoever is on call
exit 1                                                                                                 # exit with a non-zero status so CI/CD marks this deployment as failed
