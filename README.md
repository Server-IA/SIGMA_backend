# Main Backend

Este repositorio contiene el backend **principal** del sistema de **Gestión de Maquinaria y Nómina**.  
Es el servicio central, encargado de proveer la base de datos y los módulos principales del sistema.  
Este documento guía al equipo desde la organización de ramas hasta el levantamiento del contenedor con Docker.  

---

## 1. Organización del Repositorio y Ramas

- **Ramas principales:**
  - **develop:** Desarrollo y Pull Requests.
  - **main:** Recibe los cambios aprobados desde `develop`.
  - **test:** El equipo de QA trae cambios desde `main` para ejecutar pruebas.
  - **dokploy:** Se actualiza tras aprobar pruebas para despliegue/producción.

- **Flujo de trabajo:**
  1. Desarrollo en **develop** (PRs).
  2. Aprobación por el líder → merge a **main**.
  3. QA trae cambios de **main** a **test** y realiza pruebas.
  4. Si todo OK, se actualiza **dokploy** para despliegue.

---

## 2. Configurar Variables de Entorno

Copia el archivo `.env.example` a `.env` y ajusta los valores según tu entorno:  

```dotenv
SECRET_KEY=

DB_NAME=machpaydb
DB_USER=youruser
DB_PASSWORD=yourpassword 
DB_HOST=db
DB_PORT=5432

DEBUG=True
ALLOWED_HOSTS=*

AUTH_SERVICE_URL=http://backend:8001/

FIREBASE_CREDENTIALS='{""}'
FIREBASE_STORAGE_BUCKET=

JWT_SECRET=your_secret_key

SERVICE_NAME=machpayroll
AUDIT_URL=http://audit-service:8002/audit-events
AUDIT_TOKEN=devtoken
AUDIT_HTTP_TIMEOUT=1.5

# Country/State/City API
X_CSCAPI_KEY=SThkSGZBV3Z4amdiSVduRlp0SkE4MEpwMnU4UWhpM2xOdDJERE5uWA==
# Opcional (por defecto: https://api.countrystatecity.in/v1)
# CSC_API_BASE_URL=https://api.countrystatecity.in/v1
```
## 3. Crear la Red de Docker

Para que este servicio pueda comunicarse con otros microservicios (como el de **usuarios**), es necesario contar con una red compartida en Docker.  

La red solo debe crearse **una vez en la máquina local**. Si ya existe, puedes omitir este paso.  

Ejecuta el siguiente comando:  

```bash
docker network create shared_net
```
## 4. Levantar el Contenedor

Una vez configurado el archivo `.env` y creada la red compartida, ya puedes levantar el contenedor de este servicio.  

Construye la imagen y ejecuta el servicio con:  

```bash
docker-compose up --build
```

## 5. Ejecutar Migraciones

Después de que el contenedor esté corriendo por primera vez, es necesario aplicar las migraciones de Django para inicializar la base de datos.  

Ejecuta los siguientes comandos:  

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## 6. Consideraciones Finales

- Este servicio es el **núcleo del sistema**, ya que aquí se genera el contenedor de la base de datos y las tablas iniciales.  
- Todo el desarrollo y la ejecución se realizan dentro de **Docker**, por lo que **no es necesario configurar entornos virtuales locales**.  
- Antes de trabajar, asegúrate de:  
  - Haber creado la red **shared_net**.  
  - Haber ejecutado las migraciones al menos una vez para inicializar la base de datos.  

Si realizas cambios frecuentes en el código, es recomendable usar:  

```bash
docker-compose up --build
```