#!/usr/bin/env bash
# Controlled database migration runner for production, meant to be called by
# scripts/deploy.sh rather than running `flask db upgrade` by hand on the
# server. Should fail loudly (non-zero exit) if the migration fails, so
# deploy.sh can stop the rollout instead of restarting containers against a
# half-migrated schema.
