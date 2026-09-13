#!/usr/bin/env bash
# Scheduled PostgreSQL backup (e.g. via a cron job on the server). Expected
# to run `pg_dump` against the production database, store the dump with a
# timestamped filename, and enforce a retention policy (delete backups older
# than a defined number of days) instead of keeping every dump forever.
