from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from machinery.models.machinery import Machinery
from parameterization.models import Statues
from machinery.serializers.machinery_serializers.machinery_general_sheet_create_serializer import (
    MachineryGeneralSheetCreateSerializer
)
from machinery.serializers.machinery_serializers.machinery_list_serializer import MachineryListSerializer
from machinery.serializers.machinery_serializers.machinery_list_active_serializer import MachineryListActiveSerializer
from machinery.serializers.machinery_serializers.machinery_general_sheet_update_serializer import MachineryUpdateSerializer
from machinery.serializers.machinery_serializers.machinery_general_sheet_detail_serializer import MachineryDetailSerializer
from django.db.models import Q
from django.utils import timezone
import logging

# Auditoría 
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, machinery_snapshot, build_meta_with_machinery_id

logger = logging.getLogger(__name__)


class MachineryViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de maquinaria.
    """

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        Adaptado de FastAPI para Django REST Framework.
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}

        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []

        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=False, methods=['get'], url_path='list')
    def list_machinery(self, request):
        """
        Lista todas las máquinas con información básica.
        
        Incluye:
        - image_path: Ruta de la imagen de la máquina
        - machinery_name: Nombre de la máquina
        - serial_number: Número de serie
        - machinery_secondary_type: ID y nombre del subtipo de maquinaria
        - acquisition_date: Fecha de adquisición (de la ficha de uso)
        - machinery_operational_status: ID y nombre del estado operativo
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 82  # machinery.list

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = Machinery.objects.select_related(
                'machinery_secondary_type',
                'machinery_operational_status'
            ).prefetch_related(
                'machineryusagesheet_set'  # Default related_name for the reverse relation
            ).all()
            
            serializer = MachineryListSerializer(queryset, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error listing machinery: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': 'Error al listar la maquinaria',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['put'], url_path='update')
    @parser_classes([MultiPartParser, FormParser])
    def update_machinery(self, request, pk=None):
        """
        Actualiza la información de una máquina existente.
        
        Campos actualizables:
        - machinery_name: Nombre de la maquinaria (único)
        - serial_number: Número de serie (único)
        - machinery_type: ID del tipo de maquinaria
        - id_model: ID del modelo
        - machinery_secondary_type: ID del subtipo de maquinaria
        - responsible_user: ID del usuario responsable (obligatorio)
        - manufacturing_year: Año de fabricación
        - tariff_subheading: Partida arancelaria
        - id_device: ID del dispositivo de telemetría (opcional)
        - image: Archivo de imagen (opcional, formatos: JPEG, JPG, PNG, máximo 5MB)
        - machinery_operational_status: ID del estado operativo (con validaciones especiales)
        - justification: Justificación para el cambio de estado (obligatorio si el estado es diferente de 3)
        
        Validaciones:
        1. No se puede actualizar el estado de una máquina con estado 3 (En Registro)
        2. El estado debe pertenecer a la categoría 2 (estados operativos)
        3. No se puede cambiar a estado 3, si el estado actual es diferente de 3
        4. Si el estado es diferente de 3, se requiere justificación, de lo contrario no se requiere
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 83  # machinery.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar la información de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )


        try:
            try:
                machinery = Machinery.objects.get(pk=pk)
            except Machinery.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "La máquina especificada no existe"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            before = machinery_snapshot(machinery)
            
            serializer = MachineryUpdateSerializer(
                instance=machinery,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                updated_machinery = serializer.save()
                
                after = machinery_snapshot(updated_machinery)
                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).update(
                        object_id=str(updated_machinery.id_machinery),
                        before=before,
                        after=after,
                        actor_id=str(actor_id) if actor_id is not None else None,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_general_sheet",
                        meta=build_meta_with_machinery_id(before, after)
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en update_machinery: %s", e)

                return Response(
                    {
                        "success": True,
                        "message": "Maquinaria actualizada exitosamente",
                        "machinery_id": updated_machinery.id_machinery
                    },
                    status=status.HTTP_200_OK                )
                
            return Response(
                {
                    "success": False,
                    "message": "Error en los datos proporcionados",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Error updating machinery {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": f"Error al actualizar la maquinaria: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='create-general-sheet')
    @parser_classes([MultiPartParser, FormParser])
    def create_machinery_general_sheet(self, request):
        """
        Crea una nueva ficha general de maquinaria.

        Campos obligatorios:
        - machinery_name: Nombre de la maquinaria (único)
        - serial_number: Número de serie (único)
        - machinery_type: ID del tipo de maquinaria
        - id_model: ID del modelo
        - machinery_secondary_type: ID del subtipo de maquinaria
        - responsible_user: ID del usuario responsable
        
        Para la imagen de perfil:
        - image_path: Archivo de imagen (opcional, formatos: JPEG, JPG, PNG, máximo 5MB)

        Campos opcionales:
        - manufacturing_year: Año de fabricación
        - tariff_subheading: Partida arancelaria
        - id_device: ID del dispositivo de telemetría (opcional)
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 84  # machinery.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear una maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )


        try:
            serializer = MachineryGeneralSheetCreateSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(serializer.instance.id_machinery),
                        after=machinery_snapshot(serializer.instance),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_general_sheet",
                    )
                except Exception as e:
                    logging.warning(
                        "El servicio de auditoría ha fallado en create_machinery_general_sheet: %s", e
                    )

                return Response(
                    {
                        "success": True,
                        "message": "Maquinaria y ficha general creada exitosamente",
                        "machinery_id": serializer.instance.id_machinery
                    },
                    status=status.HTTP_201_CREATED
                )
                
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error al crear la ficha de maquinaria",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='confirm-registration')
    def confirm_registration(self, request, pk=None):
        """
        Confirma el registro de una maquinaria cambiando su estado de "En Registro" (id=3) a "Activo" (id=4).
        
        Este endpoint:
        1. Valida que la maquinaria existe
        2. Verifica que está en estado "En Registro" (id=3)
        3. Cambia el estado a "Activo" (id=4)
        4. Actualiza automáticamente la fecha de modificación
        """


        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 85  # machinery.confirm_registration

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para confirmar el registro de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener la maquinaria por ID
            machinery = Machinery.objects.get(pk=pk)
            
            # Validar que está en estado "En Registro" (id=3)
            if machinery.machinery_operational_status.id_statues != 3:
                return Response(
                    {
                        "success": False,
                        "message": "La maquinaria no está en estado de registro",
                        "details": f"Estado actual: {machinery.machinery_operational_status.name if hasattr(machinery.machinery_operational_status, 'name') else machinery.machinery_operational_status.id_statues}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener el estado "Activo" (id=4)
            try:
                active_status = Statues.objects.get(id_statues=4)
            except Statues.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Estado activo no encontrado en el sistema",
                        "details": "No existe un estado con id=4"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Cambiar el estado a "Activo"
            machinery.machinery_operational_status = active_status
            machinery.save()  # Esto actualiza modification_date automáticamente
            
            return Response(
                {
                    "success": True,
                    "message": "Registro de maquinaria confirmado exitosamente",
                    "data": {
                        "machinery_id": machinery.id_machinery,
                        "machinery_name": machinery.machinery_name,
                        "new_status": active_status.id_statues,
                        "modification_date": machinery.modification_date
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except Machinery.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Maquinaria no encontrada",
                    "details": f"No existe una maquinaria con ID {pk}"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al confirmar registro de maquinaria {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error interno al confirmar el registro",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """
        Obtiene los detalles de una máquina por su ID.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 86  # machinery.retrieve

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver los detalles de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )


        try:
            machinery = Machinery.objects.get(pk=pk)
            serializer = MachineryDetailSerializer(machinery)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Machinery.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': 'La máquina especificada no existe',
                    'data': None
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving machinery {pk}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': 'Error al obtener los detalles de la máquina',
                    'error': str(e),
                    'data': None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['get'], url_path='active')
    def list_active_machinery(self, request):
        """
        Lista las máquinas con estado 'Activo' (id=4) con información reducida.
        
        Retorna:
        - id_machinery: ID de la máquina
        - machinery_name: Nombre de la máquina
        - serial_number: Número de serie
        """
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 129  # machinery.list_active

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Filtrar máquinas con estado 'Activo' (id=4)
            active_machinery = Machinery.objects.filter(
                machinery_operational_status_id=4
            ).order_by('machinery_name')
            
            serializer = MachineryListActiveSerializer(active_machinery, many=True)
            
            return Response({
                'success': True,
                'message': 'Lista de máquinas activas obtenida correctamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing active machinery: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al obtener la lista de máquinas activas',
                'error': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)