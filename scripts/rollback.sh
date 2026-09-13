#!/usr/bin/env bash
# Reverts a failed deployment: re-deploys the previous known-good image tag
# (and, if the failed deployment included a migration, restores the database
# from the backup taken right before it via scripts/restore_db.sh). Meant to
# be run manually by whoever is on call, not automatically.
