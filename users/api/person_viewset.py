# users/api/person_viewset.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from users.models.person import Person
from users.serializers.person_serializers.person_create_serializer import PersonCreateSerializer
from users.serializers.person_serializers.person_list_serializer import PersonListSerializer


class PersonViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = PersonCreateSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save()
            return Response({"message": "Persona creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='listar')
    def listar_personas(self, request):
        personas = Person.objects.all()
        serializer = PersonListSerializer(personas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
