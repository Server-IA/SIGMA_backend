import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings

# Variables globales para controlar el estado de Firebase
firebase_initialized = False
bucket = None

# Cargar credenciales de Firebase
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

def initialize_firebase():
    """Inicializa Firebase solo si las credenciales están disponibles"""
    global firebase_initialized, bucket
    
    if firebase_initialized:
        return bucket
    
    # Verificar si tenemos credenciales válidas
    if not FIREBASE_CREDENTIALS or not FIREBASE_STORAGE_BUCKET:
        print("Warning: FIREBASE_CREDENTIALS no configurado o vacío. Firebase no se inicializará.")
        print("Las funciones de carga de archivos no estarán disponibles.")
        firebase_initialized = False
        return None
    
    # Verificar si las credenciales no están vacías
    if FIREBASE_CREDENTIALS.strip() == '{}' or FIREBASE_CREDENTIALS.strip() == '':
        print("Warning: FIREBASE_CREDENTIALS está vacío. Firebase no se inicializará.")
        print("Las funciones de carga de archivos no estarán disponibles.")
        firebase_initialized = False
        return None
    
    # Procesar credenciales
    try:
        raw = FIREBASE_CREDENTIALS.strip()
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            raw = raw[1:-1]
        
        # Decodificar caracteres escapados
        unescaped = raw.encode('utf-8').decode('unicode_escape')
        firebase_credentials = json.loads(unescaped)
        
        # Verificar que las credenciales tengan el formato correcto
        if not firebase_credentials.get('type') or firebase_credentials.get('type') != 'service_account':
            print("Warning: Credenciales de Firebase inválidas. Firebase no se inicializará.")
            firebase_initialized = False
            return None
        
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
        print("Firebase inicializado correctamente.")
        return bucket
        
    except json.JSONDecodeError as e:
        print(f"Warning: Error al decodificar las credenciales de Firebase: {str(e)}")
        print("Firebase no se inicializará.")
        firebase_initialized = False
        return None
    except Exception as e:
        print(f"Warning: Error al inicializar Firebase: {str(e)}")
        print("Firebase no se inicializará.")
        firebase_initialized = False
        return None

# Inicializar Firebase al importar el módulo
bucket = initialize_firebase()
