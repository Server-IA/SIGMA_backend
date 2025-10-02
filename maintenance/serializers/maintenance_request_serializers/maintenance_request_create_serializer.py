from django.utils import timezone
from django.db.models import Max
from rest_framework import serializers

from maintenance.models import MaintenanceRequest
from parameterization.models import TypesCategory, Statues


class MaintenanceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = (
            "id_machinery",
            "maintenance_type",
            "description",
            "priority",
            "detected_at",
            "id_responsible_user",
        )
        read_only_fields = ("id_responsible_user",)
        
    def generate_request_id(self):
        current_year = timezone.now().year
        # Find the highest request number for the current year
        max_request = MaintenanceRequest.objects.filter(
            id_maintenance_request__startswith=f'SOL-{current_year}'
        ).aggregate(Max('id_maintenance_request'))
        
        if max_request['id_maintenance_request__max']:
            # Extract the number part and increment it
            last_number = int(max_request['id_maintenance_request__max'].split('-')[-1])
            new_number = last_number + 1
        else:
            # First request of the year
            new_number = 1
            
        return f'SOL-{current_year}-{new_number:04d}'

    def validate(self, attrs):
        # Obtenemos el usuario del contexto (que vendrá de la vista)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            # Usamos solo el ID del usuario
            attrs['id_responsible_user_id'] = request.user.id
            
        # Generate the custom ID
        attrs['id_maintenance_request'] = self.generate_request_id()
        return attrs

    def validate_detected_at(self, value):
        # La fecha de detección no puede ser futura
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de detección no puede ser futura.")
        return value

    def validate_id_machinery(self, value):
        # La maquinaria debe estar activa (id de estado operativo = 4)
        try:
            status_id = getattr(value.machinery_operational_status, "id_statues", None)
        except Exception:
            status_id = None
        if status_id != 4:
            raise serializers.ValidationError("La maquinaria no está en estado activo.")
        return value

    def validate_priority(self, value):
        # Debe pertenecer a la categoría con id = 13
        if getattr(value, "id_types_categories_id", None) != 13:
            try:
                expected_category = TypesCategory.objects.get(id_types_categories=13)
                raise serializers.ValidationError(
                    f"La prioridad debe pertenecer a la categoría '{expected_category.name}'."
                )
            except TypesCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de prioridades requerida (id=13) no existe en la parametrización."
                )
        return value

    def validate_maintenance_type(self, value):
        # Debe pertenecer a la categoría con id = 12
        if getattr(value, "id_types_categories_id", None) != 12:
            try:
                expected_category = TypesCategory.objects.get(id_types_categories=12)
                raise serializers.ValidationError(
                    f"El tipo de mantenimiento debe pertenecer a la categoría '{expected_category.name}'."
                )
            except TypesCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de tipos requerida (id=12) no existe en la parametrización."
                )
        return value

    def create(self, validated_data):
        # Estado inicial por defecto: "Pendiente"
        try:
            pending_status = Statues.objects.get(id_statues=10)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("No se encontró el estado 'Pendiente' (id=10) en la parametrización.")

        validated_data["request_status"] = pending_status
        # Guardar fechas explícitas si deseas forzar (aunque el modelo ya usa auto_now)
        validated_data["registration_date"] = timezone.now()
        validated_data["modification_date"] = timezone.now()

        # Crear la solicitud sin consecutivo (solo registro de solicitud, no programación)
        instance = MaintenanceRequest.objects.create(**validated_data)
        return instance
