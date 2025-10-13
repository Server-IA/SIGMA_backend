from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.db.models import Max, Q
from django.core.exceptions import ObjectDoesNotExist
from service_requests.models import ServiceRequest, RequestLocation
from parameterization.models import Statues, Types, TypesCategory, Units, UnitsCategory

class RequestLocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLocation
        fields = [
            'country', 'department', 'city_id', 'place_name', 
            'latitude', 'longitude', 'area', 'area_unit', 
            'soil_type', 'humidity_level', 'altitude', 'altitude_unit'
        ]
        extra_kwargs = {
            'area': {'required': True},
            'humidity_level': {'required': True},
            'altitude': {'required': True},
            'area_unit': {'required': True},
            'soil_type': {'required': True},
            'altitude_unit': {'required': True}
        }
    
    def validate_latitude(self, value):
        """
        Valida el formato y rango de la latitud.
        Formato esperado: -90.000000 a +90.000000 con hasta 6 decimales
        """
        import re
        
        # Validar formato con expresión regular
        pattern = r'^[+-]?\d{1,2}(\.\d{1,6})?$'
        if not re.match(pattern, str(value)):
            raise serializers.ValidationError(
                "Formato de latitud inválido. Use el formato: ±DD.DDDDDD (hasta 6 decimales)"
            )
        
        # Convertir a float y validar rango
        try:
            lat = float(value)
            if not (-90 <= lat <= 90):
                raise serializers.ValidationError(
                    "La latitud debe estar entre -90 y 90 grados."
                )
            return lat
        except (ValueError, TypeError):
            raise serializers.ValidationError("La latitud debe ser un número válido.")
    
    def validate_longitude(self, value):
        """
        Valida el formato y rango de la longitud.
        Formato esperado: -180.000000 a +180.000000 con hasta 6 decimales
        """
        import re
        
        # Validar formato con expresión regular
        pattern = r'^[+-]?\d{1,3}(\.\d{1,6})?$'
        if not re.match(pattern, str(value)):
            raise serializers.ValidationError(
                "Formato de longitud inválido. Use el formato: ±DDD.DDDDDD (hasta 6 decimales)"
            )
        
        # Convertir a float y validar rango
        try:
            lng = float(value)
            if not (-180 <= lng <= 180):
                raise serializers.ValidationError(
                    "La longitud debe estar entre -180 y 180 grados."
                )
            return lng
        except (ValueError, TypeError):
            raise serializers.ValidationError("La longitud debe ser un número válido.")
    
    def validate_area_unit(self, value):
        """
        Valida que la unidad de área pertenezca a la categoría con id 11.
        """
        try:
            if value.id_units_categories_id != 11:
                expected_category = UnitsCategory.objects.get(id_units_categories=11)
                raise serializers.ValidationError(
                    f"La unidad de área debe pertenecer a la categoría '{expected_category.name}'."
                )
        except UnitsCategory.DoesNotExist:
            raise serializers.ValidationError(
                "La categoría de unidades requerida (id=11) no existe en la parametrización."
            )
        return value
    
    def validate_soil_type(self, value):
        """
        Valida que el tipo de suelo pertenezca a la categoría con id 15.
        """
        try:
            if value.id_types_categories_id != 15:
                expected_category = TypesCategory.objects.get(id_types_categories=15)
                raise serializers.ValidationError(
                    f"El tipo de suelo debe pertenecer a la categoría '{expected_category.name}'."
                )
        except TypesCategory.DoesNotExist:
            raise serializers.ValidationError(
                "La categoría de tipos requerida (id=15) no existe en la parametrización."
            )
        return value
    
    def validate_altitude_unit(self, value):
        """
        Valida que la unidad de altitud pertenezca a la categoría con id 7.
        """
        try:
            if value.id_units_categories_id != 7:
                expected_category = UnitsCategory.objects.get(id_units_categories=7)
                raise serializers.ValidationError(
                    f"La unidad de altitud debe pertenecer a la categoría '{expected_category.name}'."
                )
        except UnitsCategory.DoesNotExist:
            raise serializers.ValidationError(
                "La categoría de unidades requerida (id=7) no existe en la parametrización."
            )
        return value
        
    def validate_area(self, value):
        """
        Valida que el área no sea negativa.
        """
        if value < 0:
            raise serializers.ValidationError("El área no puede ser un valor negativo.")
        return value
        
    def validate_altitude(self, value):
        """
        Valida que la altitud no sea negativa.
        """
        if value < 0:
            raise serializers.ValidationError("La altitud no puede ser un valor negativo.")
        return value
        
    def validate_humidity_level(self, value):
        """
        Valida que el nivel de humedad sea un porcentaje válido (entre 0 y 100).
        """
        if not (0 <= value <= 100):
            raise serializers.ValidationError("El nivel de humedad debe estar entre 0 y 100%.")
        return value

class PreRequestCreateSerializer(serializers.ModelSerializer):
    location = RequestLocationCreateSerializer()
    
    class Meta:
        model = ServiceRequest
        fields = [
            'customer', 'request_detail', 'scheduled_start_date', 
            'scheduled_end_date', 'location'
        ]
        read_only_fields = ('id_responsible_user',)

    def validate_customer(self, value):
        # Verify customer is active (customer_statues.id_statues = 1)
        if value.customer_statues.id_statues != 1:
            raise serializers.ValidationError("El cliente no está activo.")
        return value

    def validate_scheduled_start_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("La fecha de inicio no puede ser anterior a la fecha actual.")
        return value

    def validate_scheduled_end_date(self, value):
        start_date_str = self.initial_data.get('scheduled_start_date')
        if start_date_str:
            from datetime import datetime
            try:
                # Convert the string date to a date object
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if value < start_date:
                    raise serializers.ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
            except (ValueError, TypeError):
                # If date parsing fails, let the field validation handle it
                pass
        return value

    def generate_request_id(self):
        current_year = timezone.now().year
        # Find the highest request number for the current year
        max_request = ServiceRequest.objects.filter(
            id_request__startswith=f'SOL-{current_year}'
        ).aggregate(Max('id_request'))
        
        if max_request['id_request__max']:
            # Extract the number part and increment it
            last_number = int(max_request['id_request__max'].split('-')[-1])
            new_number = last_number + 1
        else:
            # First request of the year
            new_number = 1
            
        return f'SOL-{current_year}-{new_number:04d}'

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        request = self.context.get('request')
        
        with transaction.atomic():
            # Set request status to 19 (pre-request)
            request_status = Statues.objects.get(id_statues=19)
            
            # Set responsible user from request
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                validated_data['id_responsible_user'] = request.user
            
            # Generate request ID
            validated_data['id_request'] = self.generate_request_id()
            validated_data['request_status'] = request_status
            
            # Create service request
            service_request = ServiceRequest.objects.create(**validated_data)
            
            # Create location
            RequestLocation.objects.create(request=service_request, **location_data)
            
            return service_request
