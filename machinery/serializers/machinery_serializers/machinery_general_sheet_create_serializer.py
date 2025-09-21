from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import FileField

from machinery.models import Machinery, TelemetryDevices
from parameterization.models import Types, Models, Statues, TypesCategory
from users.models.user import User
from django.utils import timezone
from core.services.file_upload_service import upload_file_to_firebase


class MachineryGeneralSheetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de la ficha general de maquinaria.
    Campos obligatorios: machinery_name, serial_number, machinery_type, id_model, machinery_secondary_type
    """
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='id_responsible_user'
    )

    machinery_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )

    id_model = serializers.PrimaryKeyRelatedField(
        queryset=Models.objects.all()
    )

    machinery_secondary_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )

    id_device = serializers.PrimaryKeyRelatedField(
        queryset=TelemetryDevices.objects.all(),
        required=False,
        allow_null=True
    )

    image = FileField(required=False, allow_null=True, write_only=True)

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
        ]
        extra_kwargs = {
            'machinery_name': {'required': True},
            'serial_number': {'required': True},
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
        if Machinery.objects.filter(machinery_name=value).exists():
            raise serializers.ValidationError("Ya existe una máquina con este nombre.")
        return value

    def validate_manufacturing_year(self, value):
        """
        Valida que el año de fabricación sea válido.
        """
        current_year = timezone.now().year

        if value is not None:
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
        if value:
            if Machinery.objects.filter(id_device=value).exists():
                raise serializers.ValidationError(
                    "Este dispositivo de telemetría ya está siendo utilizado por otra máquina."
                )
        return value

    def create(self, validated_data):
        """
        Crea una nueva instancia de maquinaria con el estado operativo por defecto (id=3) que indica "En Registro".
        También maneja la subida de la imagen a Firebase si se proporciona.
        """
        image_file = validated_data.pop('image', None)
        
        try:
            operational_status = Statues.objects.get(id_statues=3)
            validated_data['machinery_operational_status'] = operational_status
            
            machinery = Machinery.objects.create(**validated_data)
            
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
                    machinery.image_path = image_url
                    machinery.save(update_fields=['image_path'])
                except Exception as e:
                    machinery.delete()
                    raise serializers.ValidationError({"image": f"Error al cargar la imagen: {str(e)}"})
            
            return machinery
            
        except Statues.DoesNotExist:
            raise serializers.ValidationError({"error": "No se encontró el estado requerido"})
        except Exception as e:
            raise serializers.ValidationError({"error": f"Error al crear la maquinaria: {str(e)}"})
        except Exception as e:
            if 'machinery' in locals():
                machinery.delete()
            raise serializers.ValidationError({"error": str(e)})