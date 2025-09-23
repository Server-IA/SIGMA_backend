from rest_framework import serializers
from machinery.models import MachineryDocumentation


class MachineryDocumentationListSerializer(serializers.ModelSerializer):
    machinery_name = serializers.CharField(source='id_machinery.machinery_name', read_only=True)
    responsible_user_name = serializers.CharField(source='id_responsible_user.name', read_only=True)
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = MachineryDocumentation
        fields = [
            'id_machinery_documentation',
            'document',
            'path',
            'creation_date',
            'machinery_name',
            'responsible_user_name',
            'file_type',
        ]

    def get_file_type(self, obj):
        """Obtener el tipo de archivo basado en la extensión de la URL"""
        if obj.path:
            # Extraer extensión de la URL
            file_extension = obj.path.lower().split('.')[-1].split('?')[0]  # Remover query params
            if file_extension in ['pdf']:
                return 'PDF'
            elif file_extension in ['jpg', 'jpeg']:
                return 'JPG'
            elif file_extension in ['png']:
                return 'PNG'
        return 'Unknown'
