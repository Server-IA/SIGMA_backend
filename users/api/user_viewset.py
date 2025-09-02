from rest_framework import viewsets, status
from rest_framework.response import Response
from users.models.user import User
from users.serializers.user_serializes.user_serializer import UserSerializer

class UserViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Usuario creado exitosamente"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)