#!/usr/bin/env bash
# Deployment entrypoint, meant to run on the target server (or be called by
# .github/workflows/deploy.yml over SSH). Expected sequence: pull the latest
# code/images, run scripts/migrate.sh, rebuild/restart the containers defined
# in docker-compose.prod.yml, then verify the health endpoints respond before
# considering the deployment successful.
