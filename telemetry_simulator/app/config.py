"""
Configuration settings for Telemetry Simulator
"""
import os
import logging
from typing import List, Optional
from pydantic import field_validator, ConfigDict

logger = logging.getLogger(__name__)

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback si pydantic-settings no está instalado
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    """Application settings with IMEI management"""
    
    # IMEI Configuration
    DEVICE_IMEI: Optional[str] = None
    DEVICE_IMEI_LIST: Optional[str] = None
    ALLOW_GENERATE_IMEI: bool = False
    
    # WebSocket Password Configuration
    WEBSOCKET_PASSWORD: str
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    @field_validator('DEVICE_IMEI', mode='before')
    @classmethod
    def validate_single_imei(cls, v):
        """Validate single IMEI format"""
        if v is None:
            return None
        v = str(v).strip()
        if not v.isdigit() or len(v) != 15:
            raise ValueError(f"DEVICE_IMEI debe ser exactamente 15 dígitos. Recibido: '{v}'")
        return v
    
    @property
    def imei_list(self) -> List[str]:
        """
        Get list of valid IMEIs from environment variables.
        Returns empty list if none configured.
        """
        imeis = []
        
        # Add single IMEI if provided
        if self.DEVICE_IMEI:
            imeis.append(self.DEVICE_IMEI)
        
        # Add list of IMEIs if provided
        if self.DEVICE_IMEI_LIST:
            # Parse CSV
            raw_list = self.DEVICE_IMEI_LIST.split(",")
            for imei in raw_list:
                imei = imei.strip()
                if imei and imei.isdigit() and len(imei) == 15:
                    imeis.append(imei)
                elif imei:  # Non-empty but invalid
                    logger.warning(f"IMEI inválido descartado: '{imei}' (debe ser 15 dígitos)")
        
        return imeis
    
    def validate_imei_config(self) -> str:
        """
        Validate IMEI configuration and return first IMEI or generate one.
        
        Returns:
            str: Valid IMEI to use
            
        Raises:
            RuntimeError: If configuration is invalid
        """
        imeis = self.imei_list
        
        if imeis:
            # Use first IMEI from the list
            selected_imei = imeis[0]
            logger.info(f"IMEI configurado: {selected_imei}")
            if len(imeis) > 1:
                logger.info(f"Lista de IMEIs disponible: {len(imeis)} dispositivos")
            return selected_imei
        
        # No IMEI configured
        if self.ALLOW_GENERATE_IMEI:
            # Generate random IMEI
            from app.simulator.generator import generate_random_imei
            generated_imei = generate_random_imei()
            logger.warning(
                f"No DEVICE_IMEI configurado. Generando IMEI aleatorio: {generated_imei}\n"
                f"Para usar IMEI específico, configure:\n"
                f"   DEVICE_IMEI=352099001761481\n"
                f"   o DEVICE_IMEI_LIST=352099001761481,352099001761482"
            )
            return generated_imei
        else:
            # Configuration error
            error_msg = (
                "ERROR: No se configuró DEVICE_IMEI ni DEVICE_IMEI_LIST.\n"
                "Configuraciones disponibles:\n"
                "   - Variable de entorno única: DEVICE_IMEI=352099001761481\n"
                "   - Múltiples dispositivos: DEVICE_IMEI_LIST=352099001761481,352099001761482\n"
                "   - Permitir generación automática: ALLOW_GENERATE_IMEI=true"
            )
            logger.error(error_msg)
            raise RuntimeError("DEVICE_IMEI no configurado")


# Global settings instance
settings = Settings()

