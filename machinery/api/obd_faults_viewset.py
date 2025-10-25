from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
import re

from machinery.models.obd_faults import OBD_Faults
from machinery.serializers.obd_faults_serializers.obd_faults_serializer import OBDFaultsSerializer

class OBDFaultsViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar operaciones con fallos OBD.
    Permite buscar fallos por código.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='by-code')
    def get_by_code(self, request):
        """
        Obtiene un fallo OBD por su código.

        Args:
            code: Código del fallo OBD (formato [P|C|B|U]####, ej: P0123, C0012, B0100, U1001) - se pasa como query parameter

        Returns:
            JSON con información del fallo OBD si existe

        Nota: El código se busca de forma case-insensitive, pero debe tener formato [P|C|B|U]#### (letra seguida de 4 dígitos)
        """
        try:
            code = request.query_params.get('code')

            if not code:
                return Response({
                    'success': False,
                    'message': 'No se proporcionó un código de fallo OBD'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar formato del código antes de buscar
            pattern = r'^[PCBU]\d{4}$'
            if not re.match(pattern, code.upper()):
                return Response({
                    'success': False,
                    'message': f"El código '{code}' no tiene el formato válido [P|C|B|U]0000"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Usar el serializer para validar el formato del código
            serializer = OBDFaultsSerializer(data={'code': code})
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Formato de código OBD inválido',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Si la validación pasa, buscar el fallo OBD por código (case insensitive)
            try:
                obd_fault = OBD_Faults.objects.get(code__iexact=code.upper())
            except OBD_Faults.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'No se encontró un fallo OBD con el código: {code.upper()}'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = OBDFaultsSerializer(obd_fault)
            return Response({
                'success': True,
                'message': 'Fallo OBD encontrado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al buscar el fallo OBD',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
