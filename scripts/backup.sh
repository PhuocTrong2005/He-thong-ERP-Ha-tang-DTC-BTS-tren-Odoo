#!/bin/bash

# ============================================================================
# Backup Odoo PostgreSQL database + filestore from Docker containers
# ============================================================================
# Cách dùng:
#   bash scripts/backup.sh
# Kết quả:
#   backups/backup-YYYY-MM-DD-HH-MM-SS.tar.gz
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

BACKUP_DIR="${BACKUP_DIR:-backups}"
DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-mis_odoo_db}"
ODOO_CONTAINER_NAME="${ODOO_CONTAINER_NAME:-mis_odoo_web}"
DB_USER="${POSTGRES_USER:-odoo}"
DB_NAME="${ODOO_DB_NAME:-${POSTGRES_DB:-postgres}}"
TIMESTAMP="$(date +"%Y-%m-%d-%H-%M-%S")"
BACKUP_NAME="backup-${TIMESTAMP}"
WORK_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
ARCHIVE_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

mkdir -p "$WORK_DIR"

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER_NAME}$"; then
  echo "❌ Lỗi: Container database '${DB_CONTAINER_NAME}' không chạy."
  echo "Chạy trước: docker compose up -d"
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${ODOO_CONTAINER_NAME}$"; then
  echo "❌ Lỗi: Container Odoo '${ODOO_CONTAINER_NAME}' không chạy."
  echo "Chạy trước: docker compose up -d"
  exit 1
fi

echo "🔄 Backup database Odoo '${DB_NAME}' từ '${DB_CONTAINER_NAME}'..."
if ! docker exec "$DB_CONTAINER_NAME" psql -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  echo "❌ Lỗi: database Odoo '${DB_NAME}' không tồn tại."
  echo "Kiểm tra lại biến ODOO_DB_NAME trong file .env."
  exit 1
fi

docker exec "$DB_CONTAINER_NAME" \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "${WORK_DIR}/db.dump"

echo "🔄 Backup Odoo filestore từ '${ODOO_CONTAINER_NAME}'..."
if docker exec "$ODOO_CONTAINER_NAME" test -d /var/lib/odoo/filestore; then
  docker exec "$ODOO_CONTAINER_NAME" \
    sh -c "cd /var/lib/odoo && tar -czf - filestore" > "${WORK_DIR}/filestore.tar.gz"
else
  echo "⚠️  Không tìm thấy /var/lib/odoo/filestore, bỏ qua filestore."
fi

cat > "${WORK_DIR}/backup-info.txt" <<INFO
Backup time: ${TIMESTAMP}
DB container: ${DB_CONTAINER_NAME}
Odoo container: ${ODOO_CONTAINER_NAME}
Database: ${DB_NAME}
DB user: ${DB_USER}
INFO

tar -czf "$ARCHIVE_FILE" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$WORK_DIR"

FILE_SIZE="$(du -h "$ARCHIVE_FILE" | cut -f1)"
echo "✅ Backup thành công."
echo "📁 File: ${ARCHIVE_FILE}"
echo "📦 Size: ${FILE_SIZE}"
echo "💡 Restore: bash scripts/restore.sh ${ARCHIVE_FILE}"
