#!/bin/bash

# ============================================================================
# Restore Odoo PostgreSQL database + filestore from backup archive
# ============================================================================
# Cách dùng:
#   bash scripts/restore.sh backups/backup-YYYY-MM-DD-HH-MM-SS.tar.gz
# CẢNH BÁO:
#   Restore sẽ ghi đè database và filestore hiện tại.
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-mis_odoo_db}"
ODOO_CONTAINER_NAME="${ODOO_CONTAINER_NAME:-mis_odoo_web}"
DB_USER="${POSTGRES_USER:-odoo}"
DB_NAME="${ODOO_DB_NAME:-${POSTGRES_DB:-postgres}}"
BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
  echo "❌ Lỗi: thiếu file backup."
  echo "Cách dùng: bash scripts/restore.sh backups/backup-YYYY-MM-DD-HH-MM-SS.tar.gz"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Lỗi: file backup không tồn tại: $BACKUP_FILE"
  exit 1
fi

if ! docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER_NAME}$"; then
  echo "❌ Lỗi: không tìm thấy container database '${DB_CONTAINER_NAME}'."
  echo "Chạy trước: docker compose up -d"
  exit 1
fi

if ! docker ps -a --format '{{.Names}}' | grep -q "^${ODOO_CONTAINER_NAME}$"; then
  echo "❌ Lỗi: không tìm thấy container Odoo '${ODOO_CONTAINER_NAME}'."
  echo "Chạy trước: docker compose up -d"
  exit 1
fi

echo "⚠️  CẢNH BÁO: Restore sẽ GHI ĐÈ database và filestore hiện tại."
echo "📁 File restore: $BACKUP_FILE"
read -r -p "Nhập exactly 'yes' để tiếp tục: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "❌ Restore bị hủy."
  exit 0
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

tar -xzf "$BACKUP_FILE" -C "$TMP_DIR"
EXTRACTED_DIR="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

if [ ! -f "${EXTRACTED_DIR}/db.dump" ]; then
  echo "❌ Lỗi: backup không có file db.dump"
  exit 1
fi

echo "⏸️  Dừng Odoo để tránh ghi dữ liệu trong lúc restore..."
docker compose stop odoo >/dev/null

echo "🔄 Restore database Odoo '${DB_NAME}'..."
if ! docker exec "$DB_CONTAINER_NAME" psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  echo "Database '${DB_NAME}' chưa tồn tại. Đang tạo mới..."
  docker exec "$DB_CONTAINER_NAME" createdb -U "$DB_USER" "$DB_NAME"
fi

cat "${EXTRACTED_DIR}/db.dump" | docker exec -i "$DB_CONTAINER_NAME" \
  pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner

if [ -f "${EXTRACTED_DIR}/filestore.tar.gz" ]; then
  echo "🔄 Restore filestore..."
  docker run --rm \
    --volumes-from "$ODOO_CONTAINER_NAME" \
    -v "${EXTRACTED_DIR}:/backup:ro" \
    busybox sh -c "rm -rf /var/lib/odoo/filestore && cd /var/lib/odoo && tar -xzf /backup/filestore.tar.gz"
else
  echo "⚠️  Backup không có filestore, bỏ qua bước restore filestore."
fi

echo "▶️  Khởi động lại Odoo..."
docker compose up -d odoo >/dev/null

echo "✅ Restore thành công."
echo "Mở lại Odoo sau vài giây: http://localhost:${ODOO_PORT:-8069}"
