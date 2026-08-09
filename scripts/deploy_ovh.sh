#!/usr/bin/env bash
# Deploy Virtus Core to OVH Production (manual / CI).
# Requires: GENESIS_OVH_SSH=user@host  GENESIS_OVH_REMOTE_PATH=/srv/genesis
set -euo pipefail

TARGET="${GENESIS_OVH_SSH:?Set GENESIS_OVH_SSH=user@ovh-host}"
REMOTE="${GENESIS_OVH_REMOTE_PATH:-/srv/genesis}"
BRANCH="${GENESIS_OVH_BRANCH:-main}"

echo "==> OVH deploy → $TARGET:$REMOTE ($BRANCH)"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$TARGET" bash -s <<EOF
set -euo pipefail
cd "$REMOTE"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
cd deploy
docker compose up -d --build
curl -fsS http://127.0.0.1/health || curl -fsS http://127.0.0.1:8000/health
echo "commit=\$(git -C "$REMOTE" rev-parse --short HEAD)"
EOF
echo "==> Done. Point virtuscore.com DNS at this OVH host if not already."
