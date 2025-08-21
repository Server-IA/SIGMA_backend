# Imagen base de Python
FROM python:3.11-slim

# Evitar que Python guarde pyc y que use buffer en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos primero para aprovechar cache
COPY requirements.txt /app/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . /app/

# Exponer el puerto 8000
EXPOSE 8000

# Comando por defecto (usamos gunicorn en vez de runserver para prod)
CMD ["gunicorn", "machpaymanager.wsgi:application", "--bind", "0.0.0.0:8000"]
