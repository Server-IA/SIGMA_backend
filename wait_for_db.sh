#!/bin/bash
set -e

LOG_FILE="/app/logs/wait_for_db.log"
mkdir -p /app/logs
echo "⏳ Iniciando script wait_for_db.sh" > "$LOG_FILE"

echo "⏳ Esperando a que la base de datos esté lista..." | tee -a "$LOG_FILE"
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "🔁 Base de datos no disponible todavía... reintentando en 5s" | tee -a "$LOG_FILE"
  sleep 5
done

echo "✅ Base de datos disponible. Registrando cronjobs..." | tee -a "$LOG_FILE"
python manage.py crontab remove || true
python manage.py crontab add || true

echo "🚀 Cronjobs registrados. Finalizando script de espera." | tee -a "$LOG_FILE"
