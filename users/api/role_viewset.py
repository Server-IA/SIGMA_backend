from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from users.models.role import Role
from users.serializers.role_serializers.role_create_serializer import RoleCreateSerializer
from users.serializers.role_serializers.role_list_serializer import RoleListSerializer

class RoleViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({"message": "rol creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='listar')
    def listar_roles(self, request):
        roles = Role.objects.all()
        serializer = RoleListSerializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
