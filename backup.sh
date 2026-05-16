#!/bin/bash
set -euo pipefail

SERVICE_NAME="${MINECRAFT_SERVICE:-minecraft}"
BACKUP_DIR="${BACKUP_DIR:-/opt/minecraft/backups}"
SERVER_DIR="${SERVER_DIR:-/opt/minecraft/server-2}"
REMOTE_DEST="${BACKUP_REMOTE:-gdrive:minecraft-backups/}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
ARCHIVE="${BACKUP_DIR}/minecraft-${TIMESTAMP}.zip"
WAS_ACTIVE=0

mkdir -p "$BACKUP_DIR"

cleanup() {
	if [[ "$WAS_ACTIVE" -eq 1 ]]; then
		echo "[backup] Starting ${SERVICE_NAME}..."
		systemctl start "$SERVICE_NAME"
	fi
}

trap cleanup EXIT

if systemctl is-active --quiet "$SERVICE_NAME"; then
	WAS_ACTIVE=1
	echo "[backup] Stopping ${SERVICE_NAME}..."
	systemctl stop "$SERVICE_NAME"

	for _ in $(seq 1 60); do
		if ! systemctl is-active --quiet "$SERVICE_NAME"; then
			break
		fi
		sleep 1
	done
fi

echo "[backup] Creating archive: ${ARCHIVE}"
backup_items=(
	"$SERVER_DIR/world"
	"$SERVER_DIR/config"
	"$SERVER_DIR/server.properties"
	"$SERVER_DIR/whitelist.json"
	"$SERVER_DIR/ops.json"
	"$SERVER_DIR/banned-ips.json"
	"$SERVER_DIR/banned-players.json"
	"$SERVER_DIR/usercache.json"
	"$SERVER_DIR/eula.txt"
)

existing_items=()
for item in "${backup_items[@]}"; do
	if [[ -e "$item" ]]; then
		existing_items+=("$item")
	fi
done

if [[ "${#existing_items[@]}" -eq 0 ]]; then
	echo "[backup] No backup items found"
	exit 1
fi

zip -qr "$ARCHIVE" "${existing_items[@]}"

if command -v rclone >/dev/null 2>&1; then
	echo "[backup] Uploading to remote: ${REMOTE_DEST}"
	rclone copy "$ARCHIVE" "$REMOTE_DEST"
else
	echo "[backup] rclone not found, skipping remote upload"
fi

echo "[backup] Removing backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name "*.zip" -mtime "+${RETENTION_DAYS}" -delete

echo "[backup] Done"
