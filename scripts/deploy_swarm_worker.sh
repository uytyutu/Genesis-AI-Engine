#!/usr/bin/env bash
# Genesis Swarm Worker — deploy to cheap VPS (~€5/mo)
# Usage: bash scripts/deploy_swarm_worker.sh user@YOUR_VPS_IP

set -euo pipefail
TARGET="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_DIR="/opt/genesis-worker"

if [[ -z "$TARGET" ]]; then
  echo "Usage: bash scripts/deploy_swarm_worker.sh user@host"
  echo "Example: bash scripts/deploy_swarm_worker.sh root@203.0.113.10"
  exit 1
fi

echo "==> Packaging swarm worker from $ROOT"
ssh "$TARGET" "mkdir -p $REMOTE_DIR"
rsync -avz --delete \
  "$ROOT/swarm" \
  "$ROOT/scripts/deploy_swarm_worker.py" \
  "$ROOT/scripts/deploy_swarm_worker.sh" \
  "$TARGET:$REMOTE_DIR/"
rsync -avz \
  "$ROOT/dashboard/backend/app/integration/" \
  "$TARGET:$REMOTE_DIR/dashboard/backend/app/integration/"
rsync -avz "$ROOT/dashboard/backend/requirements.txt" "$TARGET:$REMOTE_DIR/dashboard/backend/"

echo "==> Installing deps on VPS"
ssh "$TARGET" "cd $REMOTE_DIR && python3 -m pip install -q httpx fastapi uvicorn pydantic"

echo "==> Systemd unit (optional)"
ssh "$TARGET" "cat > /etc/systemd/system/genesis-worker.service << 'UNIT'
[Unit]
Description=Genesis Swarm Worker Pool
After=network.target

[Service]
WorkingDirectory=$REMOTE_DIR
Environment=FARM_WORKER_ROLE=pool
ExecStart=/usr/bin/python3 -m uvicorn dashboard.backend.app.main:app --host 0.0.0.0 --port 8100
Restart=always

[Install]
WantedBy=multi-user.target
UNIT"

echo ""
echo "Done. On VPS:"
echo "  sudo systemctl enable --now genesis-worker"
echo ""
echo "On laptop .env.local:"
echo "  FARM_EXECUTION_MODE=remote"
echo "  FARM_WORKER_POOL_URL=http://YOUR_VPS:8100"
echo "  FARM_LIVE_MODE=live"
echo "  SCALE_API_KEY=live_..."
