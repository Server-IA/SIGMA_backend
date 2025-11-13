"""
Servicio para obtener temperatura ambiente desde Open-Meteo API
"""
from datetime import datetime, timedelta
from typing import Optional
from django.utils import timezone
import openmeteo_requests
import requests_cache
from retry_requests import retry
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Obtiene temperatura ambiente desde Open-Meteo sin persistirla."""

    def __init__(self, cache_seconds: int = 3600):
        """
        Inicializa el servicio de clima
        
        Args:
            cache_seconds: Segundos de cache para las peticiones (default: 1 hora)
        """
        cache_session = requests_cache.CachedSession('.cache', expire_after=cache_seconds)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self._client = openmeteo_requests.Client(session=retry_session)
        self._url = "https://api.open-meteo.com/v1/forecast"

    def get_average_temperature(
        self,
        latitude: float,
        longitude: float,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[float]:
        """
        Retorna la temperatura promedio (°C) para una ubicación y rango de fechas.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            start_time: Fecha de inicio (opcional, por defecto ahora)
            end_time: Fecha de fin (opcional, por defecto ahora + 1 hora)
            
        Returns:
            Temperatura promedio en °C o None si hay error
        """
        try:
            # Si no se especifica fecha, usar la actual
            if start_time is None:
                start_time = timezone.now()
            if end_time is None or end_time <= start_time:
                end_time = start_time + timedelta(hours=1)

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m",
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "timezone": "auto",  # Ajusta automáticamente al timezone local
            }

            responses = self._client.weather_api(self._url, params=params)
            if not responses:
                logger.warning("Open-Meteo no devolvió resultados.")
                return None

            hourly = responses[0].Hourly()
            if hourly.VariablesLength() == 0:
                logger.warning("No se recibieron variables de temperatura.")
                return None

            temps = hourly.Variables(0).ValuesAsNumpy()
            if len(temps) == 0:
                logger.warning("La respuesta no contiene valores de temperatura.")
                return None

            avg_temperature = float(temps.mean())
            
            logger.debug(
                f"Temperatura obtenida: {avg_temperature:.2f}°C "
                f"para {latitude}, {longitude} en rango {start_time} - {end_time}"
            )
            
            return avg_temperature
            
        except Exception as e:
            logger.error(f"Error obteniendo temperatura de Open-Meteo: {str(e)}", exc_info=True)
            return None

    def get_temperature_for_request(
        self, 
        request_location, 
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Optional[float]:
        """
        Obtiene temperatura para una solicitud de servicio usando su ubicación
        
        Args:
            request_location: Instancia de RequestLocation
            start_datetime: Inicio de la operación
            end_datetime: Fin de la operación
            
        Returns:
            Temperatura promedio en °C
        """
        return self.get_average_temperature(
            latitude=request_location.latitude,
            longitude=request_location.longitude,
            start_time=start_datetime,
            end_time=end_datetime
        )


# Instancia singleton del servicio
weather_service = WeatherService()

