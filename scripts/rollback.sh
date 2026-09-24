#!/usr/bin/env bash
# -----------------------------------------------------------------------
# Description:
#
# Rolls back to a previously deployed version after a failed deploy.
# Rollbacks are not automatic: deciding "the new version is broken" needs
# a human, so this is meant to be run manually by whoever is on call.
#
# Usage:
#   ./scripts/rollback.sh <git-ref-of-last-known-good-version>
# -----------------------------------------------------------------------

set -euo pipefail         # stop on any error, on undefined variables, and on failures inside a pipe

cd "$(dirname "$0")/.."   # move to the project root, no matter where this script is called from

COMPOSE_FILE="docker-compose.prod.yml"  # the compose file describing the production services
PREVIOUS_REF="${1:-}"                   # first argument: the git commit/tag to roll back to

if [ -z "$PREVIOUS_REF" ]; then                                         # bail out if no reference was given
    echo "Usage: $0 <git-ref-of-last-known-good-version>" >&2           # usage reminder, sent to stderr
    echo "Tip: run 'git log --oneline' on this server to find it." >&2  # help the operator find a valid reference
    exit 1                                                              # exit with an error status
fi

echo "==> Rolling back code to $PREVIOUS_REF"  # progress message
git checkout "$PREVIOUS_REF"                   # move the working tree to the previous known-good commit

# Checking out a specific commit (rather than a branch) leaves Git in
# "detached HEAD": normal to do here, but easy to forget about afterwards.
echo "NOTE: this checkout left the repository in 'detached HEAD' state (not on a branch)." >&2
echo "Once the incident is resolved, run 'git checkout main' to return to the tracked branch." >&2

echo "==> Rebuilding and restarting containers at that version"  # progress message
docker compose -f "$COMPOSE_FILE" build  # rebuild images from the rolled-back code
docker compose -f "$COMPOSE_FILE" up -d  # restart the containers using those images

cat <<MESSAGE  # print a multi-line reminder using a heredoc

Rollback to $PREVIOUS_REF complete.

If the failed deploy also ran a database migration, this older code may not
match the current schema. Restore the backup taken right before the failed
deploy if needed:
  ./scripts/restore_db.sh backups/<backup-from-before-the-deploy>.sql.gz --yes-i-am-sure
MESSAGE
