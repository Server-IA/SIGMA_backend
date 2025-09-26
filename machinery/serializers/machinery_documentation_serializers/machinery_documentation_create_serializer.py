from rest_framework import serializers
from django.utils import timezone
from machinery.models import MachineryDocumentation, Machinery
from parameterization.models import Statues
from users.models.user import User
from core.services.file_upload_service import upload_file_to_firebase


class MachineryDocumentationCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    machinery = serializers.PrimaryKeyRelatedField(
        queryset=Machinery.objects.all(),
        source='id_machinery',
        write_only=True
    )
    file = serializers.FileField(write_only=True)
    justification = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = MachineryDocumentation
        fields = [
            'document',
            'machinery',
            'responsible_user',
            'file',
            'justification',
        ]
        extra_kwargs = {
            'document': {'required': True},
            'file': {'required': True}
        }

    def validate_file(self, value):
        """Validar el archivo subido con verificación de integridad"""
        # Validar extensión
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Formato de archivo no permitido. Formatos permitidos: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño (máximo 10MB)
        max_size_mb = 10
        max_size_bytes = max_size_mb * 1024 * 1024
        if value.size > max_size_bytes:
            raise serializers.ValidationError(
                f"El archivo excede el tamaño máximo permitido de {max_size_mb}MB"
            )
        
        # ✅ VALIDACIÓN DE INTEGRIDAD
        try:
            value.seek(0)
            file_content = value.read()
            
            # Verificar que no esté vacío
            if len(file_content) == 0:
                raise serializers.ValidationError("El archivo está vacío")
            
            # Verificar tamaño consistente
            if len(file_content) != value.size:
                raise serializers.ValidationError("El archivo está corrupto (tamaño inconsistente)")
            
            # Validación específica por tipo
            if file_extension == '.pdf':
                self._validate_pdf_integrity(value)
            elif file_extension in ['.jpg', '.jpeg', '.png']:
                self._validate_image_integrity(value)
            
            # Resetear para Firebase
            value.seek(0)
            
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar el archivo: {str(e)}")
        
        return value

    def validate(self, attrs):
        """Validar unicidad del nombre del documento por maquinaria"""
        machinery = attrs.get('id_machinery')
        document_name = attrs.get('document')
        
        if machinery and document_name:
            qs = MachineryDocumentation.objects.filter(
                id_machinery=machinery, 
                document__iexact=document_name
            )
            if self.instance:  # Si es update
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise serializers.ValidationError({
                    'document': f"Ya existe un documento con el nombre '{document_name}' para esta maquinaria."
                })
        
        return attrs

    def create(self, validated_data):
        """Crear nuevo documento de maquinaria"""
        file = validated_data.pop('file')
        responsible_user = validated_data.pop('responsible_user')
        machinery = validated_data.pop('id_machinery')
        
        # Subir archivo a Firebase Storage
        try:
            file_url = upload_file_to_firebase(
                file=file,
                directory='machinery/documents/',
                allowed_extensions=['.pdf', '.jpg', '.jpeg', '.png'],
                max_size_mb=10
            )
        except Exception as e:
            raise serializers.ValidationError(f"Error al subir el archivo: {str(e)}")
        
        # Crear registro en base de datos
        validated_data['id_machinery'] = machinery
        validated_data['id_responsible_user'] = responsible_user
        validated_data['path'] = file_url
        validated_data['creation_date'] = timezone.now().date()
        
        return MachineryDocumentation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Actualizar documento de maquinaria"""
        responsible_user = validated_data.pop('responsible_user', None)
        file = validated_data.pop('file', None)
        # Requerir justificación en PUT si estado de maquinaria asociada != 3
        request = self.context.get('request')
        if request and request.method == 'PUT':
            try:
                machinery = Machinery.objects.select_related('machinery_operational_status').get(pk=instance.id_machinery_id)
                if machinery.machinery_operational_status_id and machinery.machinery_operational_status.id_statues != 3:
                    if not validated_data.get('justification'):
                        status_3_name = Statues.objects.get(id_statues=3).name
                        raise serializers.ValidationError({
                            'justification': f"La justificación es obligatoria cuando la maquinaria no está en estado '{status_3_name}'. Estado actual: '{machinery.machinery_operational_status.name}'"
                        })
            except Machinery.DoesNotExist:
                pass
        
        if responsible_user:
            instance.id_responsible_user = responsible_user
        
        # Si se envía un nuevo archivo, subirlo
        if file:
            try:
                file_url = upload_file_to_firebase(
                    file=file,
                    directory='machinery/documents/',
                    allowed_extensions=['.pdf', '.jpg', '.jpeg', '.png'],
                    max_size_mb=10
                )
                instance.path = file_url
            except Exception as e:
                raise serializers.ValidationError(f"Error al subir el archivo: {str(e)}")
        
        instance.document = validated_data.get('document', instance.document)
        if 'justification' in validated_data:
            instance.justification = validated_data['justification']
        instance.save()
        return instance

    def _validate_pdf_integrity(self, file):
        """Validar integridad de PDF"""
        try:
            import PyPDF2
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            if len(pdf_reader.pages) == 0:
                raise ValueError("PDF vacío o corrupto")
            # Verificar que se puede acceder a la primera página
            first_page = pdf_reader.pages[0]
            file.seek(0)
        except ImportError:
            # Si no hay PyPDF2, solo verificar que se puede leer
            pass
        except Exception as e:
            raise ValueError(f"PDF corrupto: {str(e)}")

    def _validate_image_integrity(self, file):
        """Validar integridad de imagen"""
        try:
            from PIL import Image
            file.seek(0)
            image = Image.open(file)
            # Verificar que se puede abrir la imagen
            image.verify()  # Verifica la integridad de la imagen
            # Verificar que tiene dimensiones válidas
            if image.size[0] == 0 or image.size[1] == 0:
                raise ValueError("Imagen con dimensiones inválidas")
            file.seek(0)
        except ImportError:
            # Si no hay PIL, solo verificar que se puede leer
            pass
        except Exception as e:
            raise ValueError(f"Imagen corrupta: {str(e)}")
