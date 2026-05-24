#!/usr/bin/env bash
# Daily backup (NFR-REL-003, 3-2-1 rule):
#   1. pg_dump from the postgres container
#   2. encrypt with age (zero-knowledge)
#   3. write to local USB mount
#   4. on Sundays, sync to Backblaze B2 (off-site)
set -euo pipefail

STAMP=$(date +%Y%m%d_%H%M)
BACKUP_DIR="${BACKUP_DIR:-/mnt/usb/passion-backups}"
AGE_RECIPIENT="${AGE_RECIPIENT:?set AGE_RECIPIENT public key}"

mkdir -p "$BACKUP_DIR"

docker compose exec -T postgres pg_dump -U passion passion \
  | gzip \
  | age -r "$AGE_RECIPIENT" \
  > "$BACKUP_DIR/passion_${STAMP}.sql.gz.age"

# Retention: keep 7 daily + 1 monthly (TODO: prune logic)

# Off-site on Sundays
if [ "$(date +%u)" -eq 7 ]; then
  rclone copy "$BACKUP_DIR" b2:passion-backups/ --include "passion_${STAMP}*"
fi

echo "Backup complete: passion_${STAMP}.sql.gz.age"
