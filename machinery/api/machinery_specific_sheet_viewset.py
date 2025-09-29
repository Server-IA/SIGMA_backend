from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from machinery.models import SpecificTechnicalSheet, Machinery
from machinery.serializers.machinery_serializers.machinery_specific_sheet_create_serializer import SpecificTechnicalSheetCreateSerializer
from rest_framework import serializers

# Auditoría
import logging
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, specific_technical_snapshot

class SpecificTechnicalSheetViewSet(viewsets.ModelViewSet):


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

    queryset = SpecificTechnicalSheet.objects.all()
    serializer_class = SpecificTechnicalSheetCreateSerializer
    http_method_names = ["get", "post", "put"]

    def create(self, request, *args, **kwargs):
        """
        Crea la ficha técnica específica.
        Valida que no exista ya una ficha técnica para la máquina especificada.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 90  # machinery_specific_sheet.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear una ficha técnica específica de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                sheet = serializer.save()

                after = specific_technical_snapshot(sheet)

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_specific_technical_sheet") or after.get("id_machinery") or "")

                    AuditClient(request).create(
                        object_id=object_id,
                        after=specific_technical_snapshot(serializer.instance),
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

            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica creada exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except serializers.ValidationError as e:
            # Captura errores de validación del serializador
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Captura cualquier otro error inesperado
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al crear la ficha técnica específica",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path=r"machinery/(?P<machinery_id>\d+)")
    def by_machinery(self, request, machinery_id=None):
        """
        Obtiene la ficha técnica específica por el ID de maquinaria.
        Endpoint: GET /machinery-specific-sheet/by-machinery/{machinery_id}/
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 91  # machinery_specific_sheet.retrieve

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para obtener una ficha técnica específica de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            sheet = SpecificTechnicalSheet.objects.filter(id_machinery_id=machinery_id).first()
            if not sheet:
                return Response(
                    {
                        "success": False,
                        "message": "No existe ficha técnica específica para la maquinaria indicada",
                        "data": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = self.get_serializer(sheet)
            response_data = serializer.data
            # Asegurarse de que el ID de la ficha específica esté incluido
            response_data['id_specific_sheet'] = sheet.id_specific_technical_sheet
            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica obtenida exitosamente",
                    "data": response_data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al consultar la ficha técnica específica",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, *args, **kwargs):
        """
        Actualiza la ficha técnica específica.
        No permite actualizar el ID de la maquinaria.
        Actualiza automáticamente la fecha de modificación y el usuario que realizó la modificación.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 92  # machinery_specific_sheet.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar la ficha técnica específica de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        before_snapshot = specific_technical_snapshot(instance)

        # Hacer una copia de los datos de la solicitud
        data = request.data.copy()
        # Si se incluye id_machinery, lo reemplazamos por el valor actual de la instancia
        # para evitar que se modifique pero cumplir con la validación del serializador
        if 'id_machinery' in data:
            data['id_machinery'] = instance.id_machinery_id

        serializer = self.get_serializer(instance, data=data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                # Actualizar la fecha de modificación
                instance.modification_date = timezone.now()
                
                # Si se proporciona un id_responsible_user en la solicitud, usarlo
                # De lo contrario, mantener el usuario actual
                if 'id_responsible_user' in data and data['id_responsible_user']:
                    from users.models.user import User
                    try:
                        responsible_user = User.objects.get(pk=data['id_responsible_user'])
                        instance.id_responsible_user = responsible_user
                    except User.DoesNotExist:
                        pass  # Mantener el usuario actual si el proporcionado no existe
                
                instance.save()
                # Guardar el resto de los datos del serializer
                updated_instance = serializer.save()
                
                after = specific_technical_snapshot(updated_instance)

                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_specific_technical_sheet") or after.get("id_machinery") or "")

                    # Emitir update a auditoría (AuditClient calculará diff)
                    AuditClient(request).update(
                        object_id=object_id,
                        before=before_snapshot,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="specific_technical_sheet",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en update_specific_technical_sheet: %s", e)


            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica actualizada exitosamente"
                },
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al actualizar la ficha técnica específica",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )