from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from machinery.models import MachineryDocumentation, Machinery
from machinery.serializers.machinery_documentation_serializers.machinery_documentation_create_serializer import MachineryDocumentationCreateSerializer
from machinery.serializers.machinery_documentation_serializers.machinery_documentation_list_serializer import MachineryDocumentationListSerializer


class MachineryDocumentationViewSet(viewsets.ViewSet):

    def create(self, request):
        """Crear nuevo documento de maquinaria"""
        serializer = MachineryDocumentationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
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
        try:
            document = MachineryDocumentation.objects.get(pk=pk)
        except MachineryDocumentation.DoesNotExist:
            return Response({
                "message": "Documento de maquinaria no encontrado",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = MachineryDocumentationCreateSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
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
        try:
            document = MachineryDocumentation.objects.get(pk=pk)
        except MachineryDocumentation.DoesNotExist:
            return Response({
                "message": "Documento de maquinaria no encontrado",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            document.delete()
            return Response({
                "message": "Documento de maquinaria eliminado exitosamente",
                "status": "success"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": f"Error al eliminar el documento: {str(e)}",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<machinery_id>\d+)')
    def list_by_machinery(self, request, machinery_id=None):
        """Listar documentos por maquinaria"""
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
