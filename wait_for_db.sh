#!/bin/bash
set -e

echo "⏳ Esperando a que la base de datos esté lista..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "🔁 DB no lista, reintentando en 5s..."
  sleep 5
done

echo "✅ Base de datos disponible."
exec "$@"
