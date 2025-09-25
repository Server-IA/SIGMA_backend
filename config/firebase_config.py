import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings

# Cargar credenciales de Firebase
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

if not FIREBASE_CREDENTIALS or not FIREBASE_STORAGE_BUCKET:
    raise ValueError("FIREBASE_CREDENTIALS y FIREBASE_STORAGE_BUCKET deben estar configurados en las variables de entorno")

# Procesar credenciales
raw = FIREBASE_CREDENTIALS.strip()
if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
    raw = raw[1:-1]

# Decodificar caracteres escapados
try:
    unescaped = raw.encode('utf-8').decode('unicode_escape')
    firebase_credentials = json.loads(unescaped)
    
    # Asegurar que la clave privada tenga saltos de línea correctos
    if 'private_key' in firebase_credentials:
        firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\n", "\n").strip()
    
    # Inicializar Firebase solo una vez
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET.strip()})
    
    # Obtener el bucket de almacenamiento
    bucket = storage.bucket()
    
except json.JSONDecodeError as e:
    raise ValueError(f"Error al decodificar las credenciales de Firebase: {str(e)}")
except Exception as e:
    raise ValueError(f"Error al inicializar Firebase: {str(e)}")
