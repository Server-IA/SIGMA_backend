from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from service_requests.models import ServiceRequest, RequestLocation, RequestMachineryUser, Implementation, SoilType, Texture
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Units, UnitsCategory
from users.models import User
from machinery.models import Machinery

class RequestLocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLocation
        fields = [
            'country', 'department', 'city_id', 'place_name', 
            'latitude', 'longitude', 'area', 'area_unit', 
            'altitude', 'altitude_unit'
        ]
        extra_kwargs = {
            'area': {'required': True},
            'altitude': {'required': True},
            'area_unit': {'required': True},
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
        Solo se aplica si el valor no es None.
        """
        if value is not None:
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
    
    def validate_altitude_unit(self, value):
        """
        Valida que la unidad de altitud pertenezca a la categoría con id 7.
        Solo se aplica si el valor no es None.
        """
        if value is not None:
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
        
    def validate(self, data):
        """
        Validaciones cruzadas entre campos relacionados.
        """
        # Validar que si se proporciona área, también se proporcione su unidad
        if data.get('area') is not None and data.get('area_unit') is None:
            raise serializers.ValidationError({
                'area_unit': 'La unidad de área es obligatoria cuando se proporciona un valor de área.'
            })
            
        # Validar que si se proporciona altitud, también se proporcione su unidad
        if data.get('altitude') is not None and data.get('altitude_unit') is None:
            raise serializers.ValidationError({
                'altitude_unit': 'La unidad de altitud es obligatoria cuando se proporciona un valor de altitud.'
            })
            
        return data
        
    def validate_area(self, value):
        """
        Valida que el área no sea negativa.
        Solo se aplica si el valor no es None.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("El área no puede ser un valor negativo.")
        return value
        
    def validate_altitude(self, value):
        """
        Valida que la altitud no sea negativa.
        Solo se aplica si el valor no es None.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError("La altitud no puede ser un valor negativo.")
        return value

class MachineryUserSerializer(serializers.Serializer):
    machinery_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)
    soil_type = serializers.PrimaryKeyRelatedField(
        queryset=SoilType.objects.all(),
        required=False,
        allow_null=True
    )
    texture = serializers.PrimaryKeyRelatedField(
        queryset=Texture.objects.all(),
        required=False,
        allow_null=True
    )
    humidity_level = serializers.FloatField(required=False, allow_null=True)
    implementation = serializers.PrimaryKeyRelatedField(
        queryset=Implementation.objects.all(),
        required=False,
        allow_null=True
    )
    depth = serializers.FloatField(required=False, allow_null=True)
    slope = serializers.FloatField(required=False, allow_null=True)
    work_duration = serializers.FloatField(required=False, allow_null=True)

    def validate_humidity_level(self, value):
        """
        Valida que el nivel de humedad sea un porcentaje válido (entre 0 y 50).
        Solo se aplica si el valor no es None.
        """
        if value is not None and not (0 <= value <= 50):
            raise serializers.ValidationError("El nivel de humedad debe estar entre 0 y 50%.")
        return value

    def validate_depth(self, value):
        """
        Valida que la profundidad esté entre 0.1 y 0.5.
        Solo se aplica si el valor no es None.
        """
        if value is not None and not (0.1 <= value <= 0.5):
            raise serializers.ValidationError("La profundidad debe estar entre 0.1 y 0.5.")
        return value

    def validate_slope(self, value):
        """
        Valida que la pendiente esté entre 0 y 30.
        Solo se aplica si el valor no es None.
        """
        if value is not None and not (0 <= value <= 30):
            raise serializers.ValidationError("La pendiente debe estar entre 0% y 30%.")
        return value

    def validate_work_duration(self, value):
        """
        Valida que la duración del trabajo no sea negativa y tenga máximo 2 decimales.
        Solo se aplica si el valor no es None.
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("La duración del trabajo no puede ser un valor negativo.")
            # Verificar que no tenga más de 2 decimales
            if not (value * 100).is_integer():
                raise serializers.ValidationError("La duración del trabajo debe tener máximo 2 decimales.")
        return value

    def validate(self, data):
        """
        Valida que si alguno de los campos relacionados con el suelo está presente,
        todos los demás campos relacionados también deben estar presentes.
        """
        soil_fields = [
            'soil_type', 'texture', 'humidity_level', 
            'implementation', 'depth', 'slope', 'work_duration'
        ]
        
        # Verificar si algún campo relacionado con el suelo está presente
        any_soil_field_present = any(field in data and data[field] is not None for field in soil_fields)
        
        if any_soil_field_present:
            missing_fields = [field for field in soil_fields if field not in data or data.get(field) is None]
            if missing_fields:
                raise serializers.ValidationError({
                    'detail': 'Si proporciona algún dato para el entrenamiento del modelo, todos los campos son obligatorios.',
                    'missing_fields': missing_fields
                })
        
        return data


class PreRequestUpdateSerializer(serializers.ModelSerializer):
    location = RequestLocationUpdateSerializer(required=True)
    machinery_users = MachineryUserSerializer(many=True, required=True)

    class Meta:
        model = ServiceRequest
        fields = [
            'customer', 'request_detail', 'scheduled_start_date', 'scheduled_end_date',
            'location', 'machinery_users', 'payment_method', 'payment_status',
            'amount_paid', 'currency_unit_amount_paid', 'amount_to_pay',
            'currency_unit_amount_to_pay'
        ]
        extra_kwargs = {
            'payment_status': {'required': True},
            'amount_paid': {'required': False, 'allow_null': True, 'min_value': 0},
            'currency_unit_amount_paid': {'required': False, 'allow_null': True},
            'amount_to_pay': {'required': False, 'allow_null': True, 'min_value': 0},
            'currency_unit_amount_to_pay': {'required': False, 'allow_null': True},
        }

    def validate_payment_status(self, value):
        """
        Valida que el estado de pago pertenezca a la categoría con ID 6.
        """
        if value is None:
            raise serializers.ValidationError(
                "El estado de pago es obligatorio."
            )
            
        try:
            if value.id_statues_categories_id != 6:
                expected_category = StatuesCategory.objects.get(id_statues_categories=6)
                raise serializers.ValidationError(
                    f"El estado de pago debe pertenecer a la categoría '{expected_category.name}'."
                )
        except StatuesCategory.DoesNotExist:
            raise serializers.ValidationError(
                "La categoría de estados de pago requerida (id=6) no existe en la parametrización."
            )
        return value

    def validate_currency_unit_amount_paid(self, value):
        """
        Valida que la moneda de pago pertenezca a la categoría con ID 10.
        Solo se valida si se proporciona un valor.
        """
        if value is not None:
            try:
                if value.id_units_categories_id != 10:
                    expected_category = UnitsCategory.objects.get(id_units_categories=10)
                    raise serializers.ValidationError(
                        f"La moneda de pago debe pertenecer a la categoría '{expected_category.name}'."
                    )
            except UnitsCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de unidades de moneda requerida (id=10) no existe en la parametrización."
                )
        return value

    def validate_currency_unit_amount_to_pay(self, value):
        """
        Valida que la moneda de pago a futuro pertenezca a la categoría con ID 10.
        Solo se valida si se proporciona un valor.
        """
        if value is not None:
            try:
                if value.id_units_categories_id != 10:
                    expected_category = UnitsCategory.objects.get(id_units_categories=10)
                    raise serializers.ValidationError(
                        f"La moneda de pago a futuro debe pertenecer a la categoría '{expected_category.name}'."
                    )
            except UnitsCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de unidades de moneda requerida (id=10) no existe en la parametrización."
                )
        return value


    def validate_customer(self, value):
        if value.customer_statues_id == 2:  # Inactivo
            raise serializers.ValidationError(
                "El cliente está inactivo. Por favor active el cliente o seleccione otro."
            )
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

    def validate_machinery_users(self, value):
        if not value:
            raise serializers.ValidationError("Debe especificar al menos una máquina y operario.")
        
        # Validar máquinas duplicadas
        machinery_ids = [item['machinery_id'] for item in value]
        if len(machinery_ids) != len(set(machinery_ids)):
            raise serializers.ValidationError("No puede haber máquinas duplicadas en la solicitud.")
        
        return value
        
    def validate(self, data):
        """
        Valida que no existan solicitudes para el mismo cliente en el mismo rango de fechas,
        que no haya conflictos de programación de máquinas y que los datos de pago sean válidos.
        """
        # Validación de pagos
        amount_paid = data.get('amount_paid')
        amount_to_pay = data.get('amount_to_pay')
        currency_paid = data.get('currency_unit_amount_paid')
        currency_to_pay = data.get('currency_unit_amount_to_pay')
        payment_status = data.get('payment_status')

        # Validar que si hay montos, las monedas sean obligatorias y viceversa
        has_any_amount = amount_paid is not None or amount_to_pay is not None
        has_any_currency = currency_paid is not None or currency_to_pay is not None
        
        if has_any_amount or has_any_currency:
            # Validar que ambas monedas estén presentes si alguna lo está
            if not all([currency_paid, currency_to_pay]):
                raise serializers.ValidationError({
                    'currency_unit_amount_paid': 'Debe proporcionar tanto la moneda de pago como la moneda a pagar cuando se especifican montos.',
                    'currency_unit_amount_to_pay': 'Debe proporcionar tanto la moneda de pago como la moneda a pagar cuando se especifican montos.'
                })
                
            # Validar que ambos montos estén presentes si alguno lo está
            if not all([amount_paid is not None, amount_to_pay is not None]):
                raise serializers.ValidationError({
                    'amount_paid': 'Debe proporcionar tanto el monto pagado como el monto a pagar cuando se especifican monedas.',
                    'amount_to_pay': 'Debe proporcionar tanto el monto pagado como el monto a pagar cuando se especifican monedas.'
                })

        # Validar que las monedas sean iguales
        if currency_paid and currency_to_pay and currency_paid != currency_to_pay:
            raise serializers.ValidationError({
                'currency_unit_amount_to_pay': 'La moneda debe ser la misma que la moneda de pago.'
            })

        # Validar que el monto pagado no sea mayor al monto a pagar
        if amount_paid is not None and amount_to_pay is not None:
            if amount_paid > amount_to_pay:
                raise serializers.ValidationError({
                    'amount_paid': 'El monto pagado no puede ser mayor al monto a pagar.'
                })
            
            # Si el estado de pago es 18 (Pago Total), los montos deben ser iguales
            if payment_status and payment_status.id_statues == 18 and amount_paid != amount_to_pay:
                raise serializers.ValidationError({
                    'amount_paid': 'Para el estado de pago Pagado, el monto pagado debe ser igual al monto a pagar.',
                    'amount_to_pay': 'Para el estado de pago Pagado, el monto pagado debe ser igual al monto a pagar.'
                })

        # Validar que el estado de pago pertenezca a la categoría con ID 6
        if payment_status:
            try:
                if payment_status.id_statues_categories_id != 6:
                    expected_category = StatuesCategory.objects.get(id_statues_categories=6)
                    raise serializers.ValidationError({
                        'payment_status': f"El estado de pago debe pertenecer a la categoría '{expected_category.name}'."
                    })
            except StatuesCategory.DoesNotExist:
                raise serializers.ValidationError({
                    'payment_status': 'La categoría de estados de pago requerida (id=6) no existe en la parametrización.'
                })

        # Validar que la moneda de pago pertenezca a la categoría con ID 10
        if currency_paid:
            try:
                if currency_paid.id_units_categories_id != 10:
                    expected_category = UnitsCategory.objects.get(id_units_categories=10)
                    raise serializers.ValidationError({
                        'currency_unit_amount_paid': f"La moneda de pago debe pertenecer a la categoría '{expected_category.name}'."
                    })
            except UnitsCategory.DoesNotExist:
                raise serializers.ValidationError({
                    'currency_unit_amount_paid': 'La categoría de unidades de moneda requerida (id=10) no existe en la parametrización.'
                })

        # Validación de fechas
        scheduled_start_date = data.get('scheduled_start_date')
        scheduled_end_date = data.get('scheduled_end_date')
        
        if scheduled_start_date and scheduled_end_date:
            # Validación de cliente
            customer = data.get('customer')
            if customer:
                # Buscar solicitudes existentes que se superpongan con el rango de fechas
                # Excluir solicitudes finalizadas (22) o canceladas (23)
                overlapping_requests = ServiceRequest.objects.filter(
                    customer=customer,
                    scheduled_start_date__lte=scheduled_end_date,
                    scheduled_end_date__gte=scheduled_start_date
                ).exclude(
                    request_status_id__in=[22, 23]  # Excluir finalizadas y canceladas
                )
                
                # Si estamos actualizando una solicitud existente, la excluimos de la búsqueda
                if self.instance:
                    overlapping_requests = overlapping_requests.exclude(id_request=self.instance.id_request)
                
                if overlapping_requests.exists():
                    conflict = overlapping_requests.first()
                    raise serializers.ValidationError({
                        'non_field_errors': [
                            f'El cliente ya tiene una solicitud activa ({conflict.id_request}) en el rango de fechas: {conflict.scheduled_start_date.strftime("%d/%m/%Y")} - {conflict.scheduled_end_date.strftime("%d/%m/%Y")}'
                        ]
                    })
            
            # Validación de máquinas
            request_id = self.instance.id_request if self.instance else None
            machinery_users = data.get('machinery_users', [])
            
            if machinery_users:
                machinery_ids = [item['machinery_id'] for item in machinery_users]
                
                # Verificar disponibilidad de máquinas
                for machinery_id in machinery_ids:
                    # Excluir solicitudes finalizadas (22) o canceladas (23)
                    overlapping_requests = RequestMachineryUser.objects.filter(
                        machinery_id=machinery_id,
                        request__scheduled_start_date__lte=scheduled_end_date,
                        request__scheduled_end_date__gte=scheduled_start_date
                    ).exclude(
                        request__request_status_id__in=[22, 23]  # Excluir finalizadas y canceladas
                    )
                    
                    if request_id:
                        overlapping_requests = overlapping_requests.exclude(request_id=request_id)
                    
                    if overlapping_requests.exists():
                        machinery = Machinery.objects.get(pk=machinery_id)
                        active_statuses = overlapping_requests.values_list(
                            'request__request_status__name', flat=True
                        ).distinct()
                        # Incluir IDs de solicitudes en conflicto en el mensaje (solo lectura)
                        conflict_ids = list(overlapping_requests.values_list('request__id_request', flat=True).distinct())

                        raise serializers.ValidationError({
                            'machinery_users': [
                                f"La máquina {machinery.machinery_name} ya tiene solicitudes activas "
                                f"(estados: {', '.join(active_statuses)}) en el rango de fechas especificado. "
                                f"Solicitudes en conflicto: {', '.join(str(cid) for cid in conflict_ids)}."
                            ]
                        })
        
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        location_data = validated_data.pop('location', None)
        machinery_users_data = validated_data.pop('machinery_users', [])
        
        # Actualizar la ubicación si se proporciona
        if location_data and hasattr(instance, 'request_location'):
            location = instance.request_location
            for attr, value in location_data.items():
                setattr(location, attr, value)
            location.save()
        
        # Obtener las fechas actuales antes de actualizar
        current_creation_date = instance.creation_date
        current_modification_date = instance.modification_date
        
        # Actualizar los datos básicos de la solicitud, excluyendo las fechas
        for attr, value in validated_data.items():
            if attr not in ['creation_date', 'modification_date']:
                setattr(instance, attr, value)
        
        # Restaurar las fechas originales
        instance.creation_date = current_creation_date
        instance.modification_date = current_modification_date
        
        # Obtener el nombre del campo de clave primaria
        pk_field_name = instance._meta.pk.name
        
        # Guardar sin actualizar automáticamente las fechas ni la clave primaria
        instance.save(update_fields=[
            field.name for field in instance._meta.fields 
            if field.name not in ['creation_date', 'modification_date', pk_field_name]
        ])
        
        # Actualizar asignaciones de máquinas y operarios si se proporcionan
        if machinery_users_data:
            # Eliminar asignaciones existentes
            instance.machinery_users.all().delete()
            
            # Crear nuevas asignaciones
            for item in machinery_users_data:
                RequestMachineryUser.objects.create(
                    request=instance,
                    machinery_id=item['machinery_id'],
                    user_id=item['user_id'],
                    soil_type=item.get('soil_type'),
                    texture=item.get('texture'),
                    humidity_level=item.get('humidity_level'),
                    implementation=item.get('implementation'),
                    depth=item.get('depth'),
                    slope=item.get('slope'),
                    work_duration=item.get('work_duration')
                )
        
        return instance
