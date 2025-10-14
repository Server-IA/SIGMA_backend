# Imagen base de Python
FROM python:3.11-slim

# Evitar que Python guarde pyc y que use buffer en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    cron \
    bash \
    procps \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos primero para aprovechar cache
COPY requirements.txt /app/
COPY vendor/ /app/vendor/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . /app/

# Copiar el script de espera y darle permisos
COPY wait_for_db.sh /app/wait_for_db.sh
RUN chmod +x /app/wait_for_db.sh

# Exponer el puerto 8000
EXPOSE 8000

# Comando por defecto: gunicorn (el compose puede sobreescribirlo si es necesario)
CMD ["gunicorn", "machpaymanager.wsgi:application", "--bind", "0.0.0.0:8000"]

