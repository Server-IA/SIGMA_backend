"""
Servicio para predecir consumo de combustible usando el modelo Random Forest.
Descarga y entrena el modelo la primera vez, luego lo reutiliza.
Genera CSV con datos para reentrenamiento cada 100 registros.
"""
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings
import logging
import kagglehub
import csv
from datetime import datetime
from django.utils import timezone
import glob

from machinery.models import Machinery, SpecificTechnicalSheet, Parameters
from service_requests.models import ServiceRequest, RequestMachineryUser, Implementation
from monitoring.models import Data
from monitoring.services.weather_service import weather_service

logger = logging.getLogger(__name__)


class FuelConsumptionPredictionService:
    """
    Servicio para predecir consumo de combustible usando el modelo Random Forest.
    Descarga y entrena el modelo la primera vez, luego lo reutiliza.
    Genera CSV con datos para reentrenamiento cada 100 registros.
    """
    
    MODEL_PATH = Path(settings.BASE_DIR) / "models" / "random_forest_optimizado.pkl"
    MODEL_DIR = Path(settings.BASE_DIR) / "models"
    TRAINING_DATA_CSV = MODEL_DIR / "training_data_accumulated.csv"
    TRAINING_COUNTER_FILE = MODEL_DIR / "training_counter.txt"
    REGISTERS_FOR_RETRAIN = 100  # Reentrenar cada 100 registros
    SAMPLE_INTERVAL_SECONDS = int(os.getenv("TELEMETRY_SAMPLE_INTERVAL_SECONDS", "5"))
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self._ensure_model_dir()
    
    def _ensure_model_dir(self):
        """Crea el directorio de modelos si no existe"""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_training_counter(self) -> int:
        """Obtiene el contador actual de registros para reentrenamiento"""
        try:
            if self.TRAINING_COUNTER_FILE.exists():
                with open(self.TRAINING_COUNTER_FILE, 'r') as f:
                    return int(f.read().strip())
            return 0
        except:
            return 0
    
    def _increment_training_counter(self) -> int:
        """Incrementa el contador y retorna el nuevo valor"""
        current = self._get_training_counter()
        new_count = current + 1
        with open(self.TRAINING_COUNTER_FILE, 'w') as f:
            f.write(str(new_count))
        return new_count
    
    def _reset_training_counter(self):
        """Resetea el contador a 0"""
        with open(self.TRAINING_COUNTER_FILE, 'w') as f:
            f.write('0')
    
    def _append_to_training_csv(self, data_row: Dict):
        """
        Agrega una fila al CSV de entrenamiento.
        Crea el archivo con headers si no existe.
        """
        try:
            # Columnas esperadas (iguales al dataset original)
            columns = [
                'Pnominal(kW)', 'T(°C)', 'Implemento', 'k_base', 'n',
                'Ancho(m)', 'Profundidad(m)', 'Textura', 'Humedad(%)',
                'Velocidad(km/h)', 'Masa_total(kg)', 'Pendiente(%)',
                'Tipo_suelo', 'RPM', 'Duracion(h)', 'Consumo_total(L)'
            ]
            
            # Verificar si el archivo existe
            file_exists = self.TRAINING_DATA_CSV.exists()
            
            # Preparar fila con todas las columnas
            row_data = {col: data_row.get(col, '') for col in columns}
            
            # Escribir al CSV
            with open(self.TRAINING_DATA_CSV, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                
                # Escribir headers si es la primera vez
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(row_data)
            
            logger.debug(f"Dato agregado al CSV de entrenamiento: {len(row_data)} columnas")
            
        except Exception as e:
            logger.error(f"Error agregando dato al CSV: {str(e)}", exc_info=True)
    
    def _get_consumption_real(self, request, machinery, timestamp) -> Optional[float]:
        """
        Calcula el consumo real desde telemetría.
        Busca el nivel de combustible más cercano al timestamp.
        """
        try:
            fuel_level_param = Parameters.objects.filter(avl_id_parameter=48).first()
            if not fuel_level_param:
                return None
            
            # Buscar nivel de combustible más cercano al timestamp
            fuel_data = Data.objects.filter(
                id_request=request,
                id_machinery=machinery,
                id_parameter=fuel_level_param,
                registered_at__lte=timestamp
            ).order_by('-registered_at').first()
            
            if not fuel_data or fuel_data.data is None:
                return None
            
            # Para calcular consumo real necesitamos nivel inicial y final
            # Por ahora retornamos None, se calculará cuando se complete la solicitud
            # O puedes usar fuel_used_gps si está disponible
            fuel_used_param = Parameters.objects.filter(avl_id_parameter=12).first()
            if fuel_used_param:
                fuel_used_data = Data.objects.filter(
                    id_request=request,
                    id_machinery=machinery,
                    id_parameter=fuel_used_param,
                    registered_at__lte=timestamp
                ).order_by('-registered_at').first()
                
                if fuel_used_data and fuel_used_data.data is not None:
                    return float(fuel_used_data.data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo consumo real: {str(e)}")
            return None
    
    def _retrain_model(self):
        """
        Reentrena el modelo con los datos acumulados en el CSV.
        Limpia el CSV después de reentrenar (mantiene solo estructura).
        """
        try:
            if not self.TRAINING_DATA_CSV.exists():
                logger.warning("No hay datos acumulados para reentrenar")
                return False
            
            # Leer CSV acumulado
            df = pd.read_csv(self.TRAINING_DATA_CSV, encoding='utf-8')
            
            if len(df) < 10:  # Mínimo de registros para entrenar
                logger.warning(f"Solo hay {len(df)} registros, mínimo 10 para reentrenar")
                return False
            
            logger.info(f"Reentrenando modelo con {len(df)} registros acumulados...")
            
            # Limpiar y preparar datos (igual que en entrenamiento inicial)
            cols_texto = ['Implemento', 'Textura', 'Tipo_suelo']
            
            # Limpiar datos
            for col in df.columns:
                if col not in cols_texto:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Eliminar filas con valores nulos críticos
            df = df.dropna(subset=['Consumo_total(L)'])
            
            if len(df) < 10:
                logger.warning("Después de limpiar, quedan menos de 10 registros válidos")
                return False
            
            # Codificar variables
            mapa_textura = {'arenoso': 1, 'franco': 2, 'arcilla': 3}
            if 'Textura' in df.columns:
                df['Textura'] = df['Textura'].map(mapa_textura).fillna(2)  # Default: franco
            
            # Verificar qué columnas categóricas existen antes de codificar
            categorical_candidates = ['Implemento', 'Tipo_suelo']
            categorical_present = [col for col in categorical_candidates if col in df.columns]
            
            if categorical_present:
                logger.info(f"Codificando columnas categóricas: {categorical_present}")
                df_encoded = pd.get_dummies(
                    df,
                    columns=categorical_present,
                    drop_first=True
                )
            else:
                logger.info("No se encontraron columnas categóricas para codificar")
                df_encoded = df.copy()
            
            # Entrenar modelo
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestRegressor
            
            target = "Consumo_total(L)"
            if target not in df_encoded.columns:
                logger.error("Columna Consumo_total(L) no encontrada en datos")
                return False
            
            X = df_encoded.drop(columns=[target])
            y = df_encoded[target]
            
            # Usar todos los datos para reentrenar (o hacer split si prefieres)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            logger.info(f"Entrenando con {len(X_train)} muestras de entrenamiento...")
            
            model = RandomForestRegressor(
                n_estimators=400,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=4,
                max_features=None,
                bootstrap=True,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Guardar modelo
            joblib.dump(model, self.MODEL_PATH)
            self.model = model
            self.model_loaded = True
            
            # Guardar columnas esperadas
            self._save_feature_columns(X.columns)
            
            # Limpiar CSV (eliminar todos los registros, mantener solo headers)
            with open(self.TRAINING_DATA_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=X.columns.tolist() + [target])
                writer.writeheader()
            
            logger.info(f"Modelo reentrenado exitosamente. CSV limpiado.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error reentrenando modelo: {str(e)}", exc_info=True)
            return False
    
    def _download_and_train_model(self):
        """
        Descarga el dataset desde Kaggle y entrena el modelo.
        Solo se ejecuta la primera vez.
        """
        try:
            logger.info("Descargando dataset desde Kaggle...")
            dataset_path = kagglehub.dataset_download("jessbeleo/datos-maquinaria-consumo")
            logger.info(f"Dataset descargado en: {dataset_path}")
            
            # Buscar archivo CSV
            csv_files = glob.glob(os.path.join(dataset_path, "*.csv"))
            if not csv_files:
                csv_files = glob.glob(os.path.join(dataset_path, "**", "*.csv"), recursive=True)
            
            if not csv_files:
                raise FileNotFoundError(f"No se encontró CSV en {dataset_path}")
            
            csv_path = None
            for csv_file in csv_files:
                if "datos_maquinaria_consumo" in csv_file.lower() or "maquinaria" in csv_file.lower():
                    csv_path = csv_file
                    break
            
            if not csv_path:
                csv_path = csv_files[0]
            
            logger.info(f"Usando archivo CSV: {csv_path}")
            
            # Columnas necesarias
            cols_usar = [
                'Pnominal(kW)', 'T(°C)', 'Implemento', 'k_base', 'n',
                'Ancho(m)', 'Profundidad(m)', 'Textura', 'Humedad(%)',
                'Velocidad(km/h)', 'Masa_total(kg)', 'Pendiente(%)',
                'Tipo_suelo', 'RPM', 'Duracion(h)', 'Consumo_total(L)'
            ]
            
            # Leer y limpiar datos
            df = pd.read_csv(csv_path, encoding='latin1', sep=';', usecols=cols_usar)
            
            # Limpiar datos
            cols_texto = ['Implemento', 'Textura', 'Tipo_suelo']
            df = df.apply(lambda x: x.str.replace(',', '.').str.strip() if x.dtype == "object" else x)
            
            for col in df.columns:
                if col not in cols_texto:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Codificar variables
            mapa_textura = {'arenoso': 1, 'franco': 2, 'arcilla': 3}
            df['Textura'] = df['Textura'].map(mapa_textura)
            
            df_encoded = pd.get_dummies(
                df,
                columns=['Implemento', 'Tipo_suelo'],
                drop_first=True
            )
            
            # Entrenar modelo
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestRegressor
            
            target = "Consumo_total(L)"
            X = df_encoded.drop(columns=[target])
            y = df_encoded[target]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            logger.info("Entrenando modelo Random Forest...")
            model = RandomForestRegressor(
                n_estimators=400,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=4,
                max_features=None,
                bootstrap=True,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Guardar modelo
            joblib.dump(model, self.MODEL_PATH)
            logger.info(f"Modelo entrenado y guardado en: {self.MODEL_PATH}")
            
            # Guardar columnas esperadas para futuras predicciones
            self._save_feature_columns(X.columns)
            
            return model
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {str(e)}", exc_info=True)
            raise
    
    def _save_feature_columns(self, columns):
        """Guarda las columnas esperadas por el modelo"""
        import json
        columns_path = self.MODEL_DIR / "feature_columns.json"
        with open(columns_path, 'w') as f:
            json.dump(list(columns), f)
    
    def _load_feature_columns(self):
        """Carga las columnas esperadas por el modelo"""
        import json
        columns_path = self.MODEL_DIR / "feature_columns.json"
        if columns_path.exists():
            with open(columns_path, 'r') as f:
                return json.load(f)
        return None
    
    def _load_model(self):
        """Carga el modelo entrenado o lo entrena si no existe"""
        if self.model_loaded and self.model is not None:
            return self.model
        
        if self.MODEL_PATH.exists():
            try:
                logger.info(f"Cargando modelo desde: {self.MODEL_PATH}")
                self.model = joblib.load(self.MODEL_PATH)
                self.model_loaded = True
                logger.info("Modelo cargado exitosamente")
                return self.model
            except Exception as e:
                logger.warning(f"Error cargando modelo, reentrenando: {str(e)}")
        
        # Si no existe, entrenar
        logger.info("Modelo no encontrado, entrenando por primera vez...")
        self.model = self._download_and_train_model()
        self.model_loaded = True
        return self.model
    
    def _get_machinery_data(self, machinery: Machinery) -> Dict[str, Any]:
        """Obtiene datos de la maquinaria desde el backend"""
        try:
            # Intentar obtener la ficha técnica (el atributo reverso es 'specifictechnicalsheet' en minúsculas)
            tech_sheet = getattr(machinery, 'specifictechnicalsheet', None)
            
            # Si no existe, consultar directamente
            if not tech_sheet:
                tech_sheet = SpecificTechnicalSheet.objects.filter(id_machinery=machinery).first()
            
            if not tech_sheet:
                logger.warning(f"No se encontró ficha técnica para machinery {machinery.id_machinery}")
                return {
                    'Pnominal(kW)': 0.0,
                    'Masa_total(kg)': 0.0
                }
            
            # Convertir potencia a kW si es necesario
            power_kw = tech_sheet.power
            if tech_sheet.power_unit and tech_sheet.power_unit.name.lower() not in ['kw', 'kilowatt', 'kilovatio']:
                # Conversión básica (ajustar según unidades disponibles)
                if 'hp' in tech_sheet.power_unit.name.lower() or 'cv' in tech_sheet.power_unit.name.lower():
                    power_kw = power_kw * 0.7457  # HP a kW
            
            # Convertir peso a kg
            mass_kg = tech_sheet.operating_weight
            if tech_sheet.operating_weight_unit and tech_sheet.operating_weight_unit.name.lower() not in ['kg', 'kilogramo', 'kilogram']:
                if 'ton' in tech_sheet.operating_weight_unit.name.lower():
                    mass_kg = mass_kg * 1000
                elif 'lb' in tech_sheet.operating_weight_unit.name.lower():
                    mass_kg = mass_kg * 0.453592
            
            return {
                'Pnominal(kW)': power_kw,
                'Masa_total(kg)': mass_kg
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de maquinaria: {str(e)}")
            return {
                'Pnominal(kW)': 0.0,
                'Masa_total(kg)': 0.0
            }
    
    def _get_request_data(self, request: ServiceRequest, machinery: Machinery) -> Dict[str, Any]:
        """Obtiene datos de la solicitud y operación desde el backend"""
        try:
            # Obtener RequestMachineryUser para esta maquinaria
            rmu = RequestMachineryUser.objects.filter(
                request=request,
                machinery=machinery
            ).first()
            
            if not rmu:
                logger.warning(f"No se encontró RequestMachineryUser para request {request.id_request} y machinery {machinery.id_machinery}")
                return {}
            
            data = {}
            
            # Implemento
            if rmu.implementation:
                data['Implemento'] = rmu.implementation.real_name or rmu.implementation.name
                data['k_base'] = rmu.implementation.k_base or 0.0
                data['n'] = rmu.implementation.n or 0.0
            else:
                data['Implemento'] = 'Desconocido'
                data['k_base'] = 0.0
                data['n'] = 0.0
            
            # Ancho, Profundidad, Humedad, Pendiente, Duración
            data['Ancho(m)'] = rmu.implement_width or 0.0
            data['Profundidad(m)'] = rmu.depth or 0.0
            data['Humedad(%)'] = rmu.humidity_level or 0.0
            data['Pendiente(%)'] = rmu.slope or 0.0
            data['Duracion(h)'] = float(rmu.work_duration) if rmu.work_duration else 0.0
            
            # Textura
            if rmu.texture:
                data['Textura'] = rmu.texture.texture.lower()
            else:
                data['Textura'] = 'franco'  # Default
            
            # Tipo_suelo
            if rmu.soil_type:
                data['Tipo_suelo'] = rmu.soil_type.surface
            else:
                data['Tipo_suelo'] = 'Desconocido'
            
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de solicitud: {str(e)}")
            return {}
    
    def _get_telemetry_data(self, request: ServiceRequest, machinery: Machinery) -> Dict[str, Any]:
        """Obtiene datos de telemetría desde la tabla Data"""
        try:
            # Obtener los últimos datos de telemetría para esta solicitud y maquinaria
            speed_param = Parameters.objects.filter(avl_id_parameter=24).first()
            rpm_param = Parameters.objects.filter(avl_id_parameter=36).first()
            
            data = {}
            
            # Velocidad (promedio o último valor)
            if speed_param:
                speed_data = Data.objects.filter(
                    id_request=request,
                    id_machinery=machinery,
                    id_parameter=speed_param
                ).order_by('-registered_at').first()
                
                if speed_data:
                    data['Velocidad(km/h)'] = float(speed_data.data) if speed_data.data is not None else 0.0
                else:
                    data['Velocidad(km/h)'] = 0.0
            else:
                data['Velocidad(km/h)'] = 0.0
            
            # RPM (promedio o último valor)
            if rpm_param:
                rpm_data = Data.objects.filter(
                    id_request=request,
                    id_machinery=machinery,
                    id_parameter=rpm_param
                ).order_by('-registered_at').first()
                
                if rpm_data:
                    data['RPM'] = float(rpm_data.data) if rpm_data.data is not None else 0.0
                else:
                    data['RPM'] = 0.0
            else:
                data['RPM'] = 0.0
            
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de telemetría: {str(e)}")
            return {}

    def _estimate_duration_hours(
        self,
        request: ServiceRequest,
        machinery: Machinery,
        timestamp: datetime = None
    ) -> float:
        """
        Estima la duración en horas usando registros de ignición encendida.
        """
        try:
            ignition_param = Parameters.objects.filter(avl_id_parameter=239).first()
            if not ignition_param:
                return 0.0

            queryset = Data.objects.filter(
                id_request=request,
                id_machinery=machinery,
                id_parameter=ignition_param
            )

            if timestamp:
                queryset = queryset.filter(registered_at__lte=timestamp)

            count_on = queryset.filter(data__gt=0).count()
            if count_on == 0:
                return 0.0

            duration_hours = (count_on * self.SAMPLE_INTERVAL_SECONDS) / 3600.0
            return round(duration_hours, 4)
        except Exception as e:
            logger.warning(f"Error estimando duración con ignición: {str(e)}")
            return 0.0
    
    def _get_ambient_temperature(self, request: ServiceRequest) -> Optional[float]:
        """Obtiene temperatura ambiente desde Open-Meteo"""
        try:
            if not hasattr(request, 'request_location'):
                logger.warning(f"Request {request.id_request} no tiene ubicación")
                return None
            
            location = request.request_location
            
            # Obtener temperatura para el rango de la solicitud
            # Convertir Date a DateTime
            from django.utils import timezone as django_timezone
            start_datetime = django_timezone.make_aware(
                datetime.combine(request.scheduled_start_date, datetime.min.time())
            )
            end_datetime = django_timezone.make_aware(
                datetime.combine(request.scheduled_end_date, datetime.max.time())
            )
            
            temperature = weather_service.get_average_temperature(
                latitude=location.latitude,
                longitude=location.longitude,
                start_time=start_datetime,
                end_time=end_datetime
            )
            
            if temperature is not None:
                logger.info(
                    "Temperatura ambiente obtenida de Open-Meteo para request %s (lat=%s, lon=%s, rango=%s - %s): %s °C",
                    request.id_request,
                    location.latitude,
                    location.longitude,
                    start_datetime,
                    end_datetime,
                    temperature
                )
            else:
                logger.warning(
                    "No se pudo obtener temperatura de Open-Meteo para request %s (lat=%s, lon=%s), se usará valor por defecto 20°C",
                    request.id_request,
                    location.latitude,
                    location.longitude
                )

            return temperature
            
        except Exception as e:
            logger.error(f"Error obteniendo temperatura ambiente: {str(e)}")
            return None
    
    def _prepare_features(self, machinery_data: Dict, request_data: Dict, 
                         telemetry_data: Dict, temperature: Optional[float]) -> Optional[pd.DataFrame]:
        """
        Prepara el DataFrame con las características para el modelo.
        Debe coincidir exactamente con las columnas del modelo entrenado.
        """
        try:
            # Combinar todos los datos
            temp_value = temperature if temperature is not None else 20.0
            if temperature is None:
                logger.info("Usando temperatura por defecto 20°C para la predicción (no se obtuvo de Open-Meteo)")
            
            features = {
                'Pnominal(kW)': machinery_data.get('Pnominal(kW)', 0.0),
                'T(°C)': temp_value,
                'k_base': request_data.get('k_base', 0.0),
                'n': request_data.get('n', 0.0),
                'Ancho(m)': request_data.get('Ancho(m)', 0.0),
                'Profundidad(m)': request_data.get('Profundidad(m)', 0.0),
                'Textura': request_data.get('Textura', 'franco'),
                'Humedad(%)': request_data.get('Humedad(%)', 0.0),
                'Velocidad(km/h)': telemetry_data.get('Velocidad(km/h)', 0.0),
                'Masa_total(kg)': machinery_data.get('Masa_total(kg)', 0.0),
                'Pendiente(%)': request_data.get('Pendiente(%)', 0.0),
                'RPM': telemetry_data.get('RPM', 0.0),
                'Duracion(h)': request_data.get('Duracion(h)', 0.0),
            }
            
            # Mapear textura
            mapa_textura = {'arenoso': 1, 'franco': 2, 'arcilla': 3}
            features['Textura'] = mapa_textura.get(features['Textura'].lower(), 2)
            
            # Crear DataFrame base
            df = pd.DataFrame([features])
            
            # Obtener columnas esperadas del modelo
            expected_columns = self._load_feature_columns()
            if not expected_columns:
                logger.warning("No se encontraron columnas esperadas, usando columnas básicas")
                # Si no hay columnas guardadas, intentar con las básicas
                df_encoded = pd.get_dummies(
                    df,
                    columns=[],  # Sin columnas categóricas adicionales por ahora
                    drop_first=True
                )
                return df_encoded
            
            # Agregar columnas dummy para Implemento y Tipo_suelo
            implemento = request_data.get('Implemento', 'Desconocido')
            tipo_suelo = request_data.get('Tipo_suelo', 'Desconocido')
            
            # Crear columnas dummy manualmente
            # Esto es un workaround - idealmente deberíamos tener el mapeo completo
            df['Implemento'] = implemento
            df['Tipo_suelo'] = tipo_suelo
            
            # Codificar con get_dummies
            df_encoded = pd.get_dummies(
                df,
                columns=['Implemento', 'Tipo_suelo'],
                drop_first=True
            )
            
            # Asegurar que todas las columnas esperadas estén presentes
            for col in expected_columns:
                if col not in df_encoded.columns:
                    df_encoded[col] = 0
            
            # Reordenar columnas según el modelo
            df_encoded = df_encoded[expected_columns]
            
            return df_encoded
            
        except Exception as e:
            logger.error(f"Error preparando features: {str(e)}", exc_info=True)
            return None
    
    def predict_and_save_training_data(
        self,
        request: ServiceRequest,
        machinery: Machinery,
        imei: str,
        timestamp: datetime,
        user=None
    ) -> Optional[Dict]:
        """
        Predice consumo, guarda datos en CSV para reentrenamiento,
        y reentrena cada 100 registros.
        """
        try:
            # Cargar modelo
            model = self._load_model()
            if not model:
                logger.error("No se pudo cargar el modelo")
                return None
            
            # Obtener todos los datos necesarios
            machinery_data = self._get_machinery_data(machinery)
            request_data = self._get_request_data(request, machinery)
            telemetry_data = self._get_telemetry_data(request, machinery)
            temperature = self._get_ambient_temperature(request)
            
            # Preparar features para predicción
            features_df = self._prepare_features(
                machinery_data, request_data, telemetry_data, temperature
            )
            
            if features_df is None or features_df.empty:
                logger.error("No se pudieron preparar las features")
                return None
            
            # Hacer predicción
            prediction_value = model.predict(features_df)[0]
            
            # Obtener consumo real (si está disponible)
            consumo_real = self._get_consumption_real(request, machinery, timestamp)
            
            # Si no hay consumo real, usar la predicción como aproximación
            # (se actualizará cuando se complete la solicitud)
            consumo_total_l = consumo_real if consumo_real is not None else prediction_value
            
            # Calcular duración efectiva a partir de ignición cuando no existe dato manual
            duracion_h = float(request_data.get('Duracion(h)', 0.0) or 0.0)
            if duracion_h <= 0.0:
                duracion_h = self._estimate_duration_hours(request, machinery, timestamp)

            # Preparar fila para CSV de entrenamiento
            temp_value = temperature if temperature is not None else 20.0
            if temperature is None:
                logger.info("Usando temperatura por defecto 20°C para el CSV de entrenamiento (no se obtuvo de Open-Meteo)")
            
            training_row = {
                'Pnominal(kW)': machinery_data.get('Pnominal(kW)', 0.0),
                'T(°C)': temp_value,
                'Implemento': request_data.get('Implemento', 'Desconocido'),
                'k_base': request_data.get('k_base', 0.0),
                'n': request_data.get('n', 0.0),
                'Ancho(m)': request_data.get('Ancho(m)', 0.0),
                'Profundidad(m)': request_data.get('Profundidad(m)', 0.0),
                'Textura': request_data.get('Textura', 'franco'),
                'Humedad(%)': request_data.get('Humedad(%)', 0.0),
                'Velocidad(km/h)': telemetry_data.get('Velocidad(km/h)', 0.0),
                'Masa_total(kg)': machinery_data.get('Masa_total(kg)', 0.0),
                'Pendiente(%)': request_data.get('Pendiente(%)', 0.0),
                'Tipo_suelo': request_data.get('Tipo_suelo', 'Desconocido'),
                'RPM': telemetry_data.get('RPM', 0.0),
                'Duracion(h)': duracion_h,
                'Consumo_total(L)': consumo_total_l  # Usar real si está disponible, sino predicción
            }
            
            # Agregar al CSV
            self._append_to_training_csv(training_row)
            
            # Incrementar contador
            counter = self._increment_training_counter()
            
            logger.info(
                f"Registro {counter}/{self.REGISTERS_FOR_RETRAIN} agregado al CSV. "
                f"Predicción: {prediction_value:.2f} L"
            )
            
            # Reentrenar si llegamos a 100 registros
            if counter >= self.REGISTERS_FOR_RETRAIN:
                logger.info(f"Llegamos a {counter} registros, reentrenando modelo...")
                if self._retrain_model():
                    # Resetear contador después de reentrenar
                    self._reset_training_counter()
                    logger.info("Reentrenamiento completado, contador reseteado")
                else:
                    logger.warning("Reentrenamiento falló, contador no reseteado")
            
            # Calcular consumo estimado por hora
            consumo_estimado_lh = prediction_value / duracion_h if duracion_h > 0 else 0.0
            
            return {
                'consumo_estimado_l': float(prediction_value),
                'consumo_estimado_lh': consumo_estimado_lh,
                'consumo_real_l': consumo_real,
                'timestamp': timestamp.isoformat(),
                'imei': imei,
                'training_counter': counter,
                'duracion_h': duracion_h
            }
            
        except Exception as e:
            logger.error(f"Error en predicción y guardado: {str(e)}", exc_info=True)
            return None


# Instancia singleton
prediction_service = FuelConsumptionPredictionService()

