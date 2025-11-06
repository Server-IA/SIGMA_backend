"""
Vista de health check para el sistema de monitoreo
"""
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Endpoint de health check para verificar el estado del sistema
    """
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            "status": "healthy",
            "service": "AppMachineryPayrollBackend",
            "database": "connected"
        })
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "service": "AppMachineryPayrollBackend",
            "error": str(e)
        }, status=503)

