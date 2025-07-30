# users/serializers/role_serializers/role_list_serializer.py

from rest_framework import serializers
from users.models.role import Role

class RoleListSerializer(serializers.ModelSerializer):
    rol_status_name = serializers.CharField(source='rol_status.name', read_only=True)
    responsible_user_name = serializers.CharField(source='id_responsible_user.username', read_only=True)

    class Meta:
        model = Role
        fields = ['id_role', 'name', 'rol_status_name', 'creation_date', 'modification_date', 'responsible_user_name']
