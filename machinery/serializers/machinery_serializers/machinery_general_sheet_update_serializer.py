from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import FileField

from machinery.models import Machinery, TelemetryDevices
from parameterization.models import Types, Models, Statues, TypesCategory
from users.models.user import User
from django.utils import timezone
from core.services.file_upload_service import upload_file_to_firebase

class MachineryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para la actualización de la ficha general de maquinaria.
    """
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='id_responsible_user',
        required=True
    )

    machinery_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        required=False
    )

    id_model = serializers.PrimaryKeyRelatedField(
        queryset=Models.objects.all(),
        required=False
    )

    machinery_secondary_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        required=False
    )

    id_device = serializers.PrimaryKeyRelatedField(
        queryset=TelemetryDevices.objects.all(),
        required=False,
        allow_null=True
    )

    image = FileField(required=False, allow_null=True, write_only=True)
    machinery_operational_status = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(),
        required=False
    )
    justification = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Machinery
        fields = [
            'machinery_name',
            'serial_number',
            'machinery_type',
            'id_model',
            'machinery_secondary_type',
            'id_city',
            'manufacturing_year',
            'tariff_subheading',
            'image',
            'image_path',
            'id_device',
            'responsible_user',
            'machinery_operational_status',
            'justification'
        ]
        
        extra_kwargs = {
            'machinery_name': {'required': False},
            'serial_number': {'required': False},
            'image_path': {'read_only': True},
        }

    def validate_image(self, value):
        """
        Validar que la imagen de la maquinaria tenga el formato correcto y no exceda el tamaño máximo permitido (5MB).
        """
        if value:
            if not value.content_type.startswith('image/'):
                raise ValidationError({"image": "El archivo debe ser una imagen (JPEG, PNG, etc.)"})

            if value.size > 5 * 1024 * 1024:
                raise ValidationError({"image": "La imagen no puede pesar más de 5MB"})

        return value
        
    def validate_machinery_name(self, value):
        """
        Validar que el nombre de la maquinaria no exista en la base de datos
        """
        if self.instance and self.instance.machinery_name == value:
            return value

        if Machinery.objects.filter(machinery_name=value).exists():
            raise serializers.ValidationError("Ya existe una máquina con este nombre.")
        return value

    def validate_manufacturing_year(self, value):
        """
        Valida que el año de fabricación sea válido.
        """
        if value is not None:
            current_year = timezone.now().year
            if value > current_year:
                raise serializers.ValidationError(
                    "El año de fabricación no puede ser mayor al año actual."
                )
            if value < 1900:
                raise serializers.ValidationError(
                    "El año de fabricación debe ser posterior a 1900."
                )
        return value

    def validate_serial_number(self, value):
        """
        Validar que el número de serie no exista en la base de datos
        """
        if self.instance and self.instance.serial_number == value:
            return value
            
        if Machinery.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("Ya existe una máquina con este número de serie.")
        return value

    def validate_machinery_type(self, value):
        """
        Valida que el tipo de maquinaria pertenezca a la categoría con id 2.
        """
        if value.id_types_categories_id != 2:
            expected_category = TypesCategory.objects.get(id_types_categories=2)
            raise serializers.ValidationError(
                f"El tipo debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def validate_machinery_secondary_type(self, value):
        """
        Valida que el tipo secundario de maquinaria pertenezca a la categoría con id 3.
        """
        if value.id_types_categories_id != 3:
            expected_category = TypesCategory.objects.get(id_types_categories=3)
            raise serializers.ValidationError(
                f"El tipo debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def validate_id_device(self, value):
        """
        Valida que el dispositivo de telemetría no esté siendo usado por otra máquina.
        """
        if value and Machinery.objects.filter(id_device=value).exclude(
            id_machinery=self.instance.id_machinery if self.instance else None
        ).exists():
            raise serializers.ValidationError(
                "Este dispositivo de telemetría ya está siendo utilizado por otra máquina."
            )
        return value
        
    def validate_id_model(self, value):
        """
        Valida que la marca asociada al modelo pertenezca a la categoría con ID 1.
        """
        if value:
            from parameterization.models import Brands, BrandsCategory
            try:
                brand = value.id_brand
                if brand.id_brands_categories_id != 1:
                    category = BrandsCategory.objects.get(id_brands_categories=1)
                    raise serializers.ValidationError(
                        f"La marca '{brand.name}' del modelo '{value.name}' no pertenece a la categoría de marcas '{category.name}'"
                    )
            except BrandsCategory.DoesNotExist:
                raise serializers.ValidationError("No se encontró la categoría de marcas con ID 1.")
        return value

    def validate(self, data):
        """
        Validaciones adicionales para el estado operativo y la justificación.
        """
        instance = self.instance
        if not instance:
            return data
            
        current_status = instance.machinery_operational_status
        
        # Validar que no se pueda modificar el estado de una máquina que está en estado 3 (Registro)
        if 'machinery_operational_status' in data and current_status and current_status.id_statues == 3:
            raise serializers.ValidationError({
                "machinery_operational_status": f"No se puede actualizar el estado de una máquina que está en estado '{current_status.name}'."
            })

        # Validar justificación si el estado actual de la máquina no es 3
        if current_status and current_status.id_statues != 3 and not data.get('justification'):
            status_3_name = Statues.objects.get(id_statues=3).name
            raise serializers.ValidationError({
                "justification": f"La justificación es obligatoria cuando la maquinaria no está en estado '{status_3_name}'. Estado actual: '{current_status.name}'"
            })

        # Si se está actualizando el estado
        if 'machinery_operational_status' in data:
            new_status = data['machinery_operational_status']

            if new_status.id_statues_categories_id != 2:
                expected_category = TypesCategory.objects.get(id_types_categories=2)
                raise serializers.ValidationError({
                    "machinery_operational_status": f"El estado '{new_status.name}' no pertenece a la categoría de '{expected_category.name}'."
                })

            # Validar que no se intente cambiar a estado 3
            if new_status.id_statues == 3:
                raise serializers.ValidationError({
                    "machinery_operational_status": f"No se puede cambiar al estado '{new_status.name}'."
                })

        return data

    def update(self, instance, validated_data):
        """
        Actualiza la instancia de maquinaria con los datos validados.
        """
        image_file = validated_data.pop('image', None)
        registration_date = instance.registration_date
        
        # Actualizar solo los campos proporcionados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar la fecha de modificación
        instance.modification_date = timezone.now().date()
        
        # Manejar la carga de la imagen si se proporciona
        if image_file:
            try:
                image_file.open()
                image_file.seek(0)
                image_url = upload_file_to_firebase(
                    file=image_file,
                    directory='uploads/machinery_pictures/',
                    allowed_extensions=['.jpg', '.jpeg', '.png'],
                    max_size_mb=5
                )
                instance.image_path = image_url
            except Exception as e:
                raise serializers.ValidationError({"image": f"Error al cargar la imagen: {str(e)}"})
        
        # Guardar la instancia con los campos actualizados
        instance.save(update_fields=[
            'machinery_name',
            'manufacturing_year',
            'serial_number',
            'machinery_type',
            'id_model',
            'tariff_subheading',
            'machinery_secondary_type',
            'id_city',
            'image_path',
            'id_device',
            'modification_date',
            'justification',
            'machinery_operational_status',
            'id_responsible_user'
        ])
        
        # Restaurar la fecha de registro si cambió
        if instance.registration_date != registration_date:
            instance.registration_date = registration_date
            instance.save(update_fields=['registration_date'])
            
        return instance
