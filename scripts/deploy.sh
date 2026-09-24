#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Description:
#
# Deploys the latest version of CADRI to this server: pulls the code,
# rebuilds the images, applies pending database migrations, restarts the
# containers, then waits for the backend to report healthy.
#
# Usage:
#   ./scripts/deploy.sh
#   (also invoked by .github/workflows/deploy.yml over SSH, once
#   backend-ci.yml / frontend-ci.yml have passed)
# ----------------------------------------------------------------------

set -euo pipefail        # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."  # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"                    # the compose file describing the production services
BACKEND_CONTAINER="${BACKEND_CONTAINER:-cadri_backend}"    # container_name of the backend service, overridable via env

echo "==> Pulling latest code"  # progress message
git pull origin main            # fetch and merge the latest commits from the main branch

echo "==> Building updated images"       # progress message
docker compose -f "$COMPOSE_FILE" build  # rebuild the Docker images with the freshly pulled code

echo "==> Backing up the database before migrating"  # progress message
./scripts/backup_db.sh  # snapshot the pre-migration state, so a bad migration can still be undone

echo "==> Applying database migrations"  # progress message
./scripts/migrate.sh                     # run pending migrations before the new code starts using the database

echo "==> Restarting services"           # progress message
docker compose -f "$COMPOSE_FILE" up -d  # recreate/restart every container in the background with the new images

echo "==> Waiting for the backend to report healthy"  # progress message
for attempt in $(seq 1 10); do  # retry up to 10 times instead of failing on the first slow start
    # The backend container has no port published to the host (only nginx
    # is exposed, see docker-compose.prod.yml), so its own Docker-level
    # healthcheck is read instead of curling a port we deliberately closed.
    HEALTH_STATUS="$(docker inspect --format='{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null || echo "unknown")"  # ask Docker for the container's health check result
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
