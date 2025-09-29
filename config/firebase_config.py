import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings

# Cargar credenciales de Firebase
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# Inicializar variables por defecto
bucket = None
firebase_initialized = False

# Solo inicializar Firebase si las credenciales están configuradas correctamente
if FIREBASE_CREDENTIALS and FIREBASE_STORAGE_BUCKET and FIREBASE_CREDENTIALS.strip() not in ['{}', '""', "''"]:
    try:
        # Procesar credenciales
        raw = FIREBASE_CREDENTIALS.strip()
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            raw = raw[1:-1]

        # Decodificar caracteres escapados
        unescaped = raw.encode('utf-8').decode('unicode_escape')
        firebase_credentials = json.loads(unescaped)
        
        # Verificar que las credenciales tengan el formato correcto
        if firebase_credentials.get("type") == "service_account":
            # Asegurar que la clave privada tenga saltos de línea correctos
            if 'private_key' in firebase_credentials:
                firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\n", "\n").strip()
            
            # Inicializar Firebase solo una vez
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_credentials)
                firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET.strip()})
            
            # Obtener el bucket de almacenamiento
            bucket = storage.bucket()
            firebase_initialized = True
            
    except json.JSONDecodeError as e:
        print(f"Warning: Error al decodificar las credenciales de Firebase: {str(e)}")
        print("Firebase no se inicializará. Las funciones de carga de archivos no estarán disponibles.")
    except Exception as e:
        print(f"Warning: Error al inicializar Firebase: {str(e)}")
        print("Firebase no se inicializará. Las funciones de carga de archivos no estarán disponibles.")
else:
    print("Warning: FIREBASE_CREDENTIALS no configurado o vacío. Firebase no se inicializará.")
    print("Las funciones de carga de archivos no estarán disponibles.")
