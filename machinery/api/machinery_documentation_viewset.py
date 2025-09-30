from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from machinery.models import MachineryDocumentation, Machinery
from machinery.serializers.machinery_documentation_serializers.machinery_documentation_create_serializer import MachineryDocumentationCreateSerializer
from machinery.serializers.machinery_documentation_serializers.machinery_documentation_list_serializer import MachineryDocumentationListSerializer

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, machinery_documentation_snapshot, build_meta_with_machinery_id
import logging

logger = logging.getLogger(__name__)


class MachineryDocumentationViewSet(viewsets.ViewSet):

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

    def create(self, request):
        """Crear nuevo documento de maquinaria"""

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 101  # machinery_documentation.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear un documento de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MachineryDocumentationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                documentation = serializer.save()

                after = machinery_documentation_snapshot(documentation)

                # Auditoría 
                try:
                    # obtener actor info centralizada
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_machinery_documentation") or after.get("id_machinery") or "")

                    AuditClient(request).create(
                        object_id=object_id,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_documentation_sheet",
                    )
                except Exception as e:
                    # La auditoría no debe romper la creación
                    logging.warning("El servicio de auditoría ha fallado en create_machinery_tracker: %s", e)

                return Response({
                    "message": "Documento de maquinaria creado exitosamente",
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "message": f"Error al crear el documento: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Actualizar documento de maquinaria"""

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 102  # machinery_documentation.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar un documento de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            document = MachineryDocumentation.objects.get(pk=pk)

            before = machinery_documentation_snapshot(document)

        except MachineryDocumentation.DoesNotExist:
            return Response({
                "message": "Documento de maquinaria no encontrado",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = MachineryDocumentationCreateSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_instance = serializer.save()

                after = machinery_documentation_snapshot(updated_instance)

                # Auditoría 
                try:
                    # obtener actor info centralizada
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_machinery_documentation") or after.get("id_machinery") or "")

                    AuditClient(request).update(
                        object_id=object_id,
                        before=before,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_documentation_sheet",
                        meta=build_meta_with_machinery_id(before, after),
                    )
                except Exception as e:
                    # La auditoría no debe romper la actualización
                    logging.warning("El servicio de auditoría ha fallado en update_machinery_tracker: %s", e)

                return Response({
                    "message": "Documento de maquinaria actualizado exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar el documento: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Eliminar documento de maquinaria"""

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 103  # machinery_documentation.delete (ajusta si corresponde)

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para eliminar un documento de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            document = MachineryDocumentation.objects.get(pk=pk)
            # snapshot BEFORE (estado previo a la eliminación)
            try:
                before = machinery_documentation_snapshot(document)
            except Exception:
                before = {"id_machinery_documentation": getattr(document, "id_machinery_documentation", None)}
        except MachineryDocumentation.DoesNotExist:
            return Response({
                "message": "Documento de maquinaria no encontrado",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            # Ejecutar delete
            document.delete()
        except Exception as e:
            # Mantener misma respuesta/estatus en caso de error al eliminar
            logger.error(f"Error al eliminar el documento: {str(e)}")
            return Response({
                "message": f"Error al eliminar el documento: {str(e)}",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Auditoría
        try:
            actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
            object_id = str(before.get("id_machinery_documentation") or before.get("id_machinery") or "")

            ok, status_code, text = AuditClient(request).delete(
                object_id=object_id,
                before=before,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                permission_id=permission_id,
                module="machinery",
                submodule="machinery_documentation_sheet",
                meta={"action": "delete"},
            )

            if not ok:
                logger.warning("Audit delete failed (%s): %s", status_code, text)
        except Exception as e:
            # No romper la respuesta por fallo en auditoría
            logging.warning("El servicio de auditoría ha fallado en delete_machinery_documentation: %s", e)

        return Response({
            "message": "Documento de maquinaria eliminado exitosamente",
            "status": "success"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<machinery_id>\d+)')
    def list_by_machinery(self, request, machinery_id=None):
        """Listar documentos por maquinaria"""

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 104  # machinery_documentation.list

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar documentos de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not Machinery.objects.filter(pk=machinery_id).exists():
            return Response({
                "message": "Maquinaria no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        documents = MachineryDocumentation.objects.filter(id_machinery_id=machinery_id)
        if not documents.exists():
            return Response({
                "message": "No existen documentos registrados para esta maquinaria",
                "data": [],
                "status": "success"
            }, status=status.HTTP_200_OK)

        serializer = MachineryDocumentationListSerializer(documents, many=True)
        return Response({
            "message": "Documentos de maquinaria obtenidos exitosamente",
            "data": serializer.data,
            "status": "success"
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download')
    def download_document(self, request, pk=None):
        """Obtener información del documento para descarga"""

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 105  # machinery_documentation.download

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para descargar un documento de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            document = MachineryDocumentation.objects.get(pk=pk)
        except MachineryDocumentation.DoesNotExist:
            return Response({
                "message": "Documento de maquinaria no encontrado",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = MachineryDocumentationListSerializer(document)
        return Response({
            "message": "Información del documento obtenida exitosamente",
            "data": serializer.data,
            "status": "success"
        }, status=status.HTTP_200_OK)
