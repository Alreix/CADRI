#!/usr/bin/env bash
# Restores a PostgreSQL dump produced by scripts/backup_db.sh, e.g.
# `./restore_db.sh path/to/backup.sql`. Should refuse to run against the
# production database without an explicit confirmation flag, since it is a
# destructive operation that overwrites current data.
