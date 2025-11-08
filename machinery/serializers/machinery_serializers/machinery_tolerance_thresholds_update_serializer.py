from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction

from machinery.models import (
    ToleranceThresholds,
    OBDFaultMachinery,
    EventTypeMachinery,
    Machinery,
    Parameters,
    OBD_Faults,
    EventTypes
)
from maintenance.models import Maintenance


class MachineryToleranceThresholdsUpdateSerializer(serializers.Serializer):
    """
    Serializer para actualizar configuraciones de tolerancia, fallos OBD y tipos de eventos para una maquinaria.
    El id_machinery viene por query parameter en la URL, no en el JSON body.

    Campos requeridos:
    - tolerance_thresholds: Array de configuraciones de tolerancia (OBLIGATORIO, debe tener al menos 1 elemento)
    - obd_fault_machinery: Array de fallos OBD (opcional)
    - event_type_machinery: Array de tipos de eventos (opcional)

    Campos obligatorios en cada item:
    - tolerance_thresholds: id_parameter, alert_enabled (cuando id_parameter está presente)
    - obd_fault_machinery: id_obd_fault, alert_enabled (cuando id_obd_fault está presente)
    - event_type_machinery: id_event_type, alert_enabled (cuando id_event_type está presente), threshold (cuando id_event_type está presente)

    Validaciones específicas:
    - alert_enabled es OBLIGATORIO cuando se proporciona el ID principal del modelo
    - tolerance_thresholds: parámetro ID no puede ser 1, 2, 4, 5, 13, 16, 17, 18
    - event_type_machinery: threshold debe estar en rango del parámetro ID 17
    """
    tolerance_thresholds = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    obd_fault_machinery = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    event_type_machinery = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )

    def validate_tolerance_thresholds(self, value):
        """
        Validaciones específicas para tolerance_thresholds
        """
        if not value:
            return value

        # 1) Validar que al menos un parámetro esté seleccionado
        if len(value) == 0:
            raise ValidationError("Debe seleccionar al menos un parámetro.")

        # 2) Validar que no se incluyan parámetros específicos (1, 2, 4, 5, 13, 16, 17, 18)
        excluded_parameters = [1, 2, 4, 5, 13, 16, 17, 18]
        for item in value:
            id_parameter = item.get('id_parameter')
            if id_parameter in excluded_parameters:
                raise ValidationError(f"El parámetro con ID {id_parameter} no puede ser utilizado.")

        # 3) Validar que no haya parámetros duplicados
        seen_parameters = set()
        for item in value:
            id_parameter = item.get('id_parameter')
            if id_parameter in seen_parameters:
                raise ValidationError(f"El parámetro con ID {id_parameter} está duplicado.")
            seen_parameters.add(id_parameter)

        # 4) Validar que alert_enabled sea obligatorio cuando se proporciona id_parameter
        for item in value:
            id_parameter = item.get('id_parameter')
            alert_enabled = item.get('alert_enabled')

            if id_parameter is not None and alert_enabled is None:
                raise ValidationError(
                    f"El campo 'alert_enabled' es obligatorio cuando se proporciona 'id_parameter'."
                )

        # 5) Validar rangos de threshold con respecto a los parámetros
        for item in value:
            id_parameter = item.get('id_parameter')
            minimum_threshold = item.get('minimum_threshold')
            maximum_threshold = item.get('maximum_threshold')

            try:
                parameter = Parameters.objects.get(id=id_parameter)

                # Validar minimum_threshold
                if minimum_threshold is not None:
                    if parameter.minimum_range is not None and minimum_threshold < parameter.minimum_range:
                        raise ValidationError(
                            f"El minimum_threshold ({minimum_threshold}) no puede ser menor que "
                            f"el minimum_range del parámetro ({parameter.minimum_range})."
                        )
                    if parameter.maximum_range is not None and minimum_threshold > parameter.maximum_range:
                        raise ValidationError(
                            f"El minimum_threshold ({minimum_threshold}) no puede ser mayor que "
                            f"el maximum_range del parámetro ({parameter.maximum_range})."
                        )

                # Validar maximum_threshold
                if maximum_threshold is not None:
                    if parameter.minimum_range is not None and maximum_threshold < parameter.minimum_range:
                        raise ValidationError(
                            f"El maximum_threshold ({maximum_threshold}) no puede ser menor que "
                            f"el minimum_range del parámetro ({parameter.minimum_range})."
                        )
                    if parameter.maximum_range is not None and maximum_threshold > parameter.maximum_range:
                        raise ValidationError(
                            f"El maximum_threshold ({maximum_threshold}) no puede ser mayor que "
                            f"el maximum_range del parámetro ({parameter.maximum_range})."
                        )

                # 6) Validar que minimum_threshold no sea mayor que maximum_threshold
                if minimum_threshold is not None and maximum_threshold is not None:
                    if minimum_threshold > maximum_threshold:
                        raise ValidationError(
                            f"El minimum_threshold ({minimum_threshold}) no puede ser mayor que "
                            f"el maximum_threshold ({maximum_threshold})."
                        )

            except Parameters.DoesNotExist:
                raise ValidationError(f"No se encontró el parámetro con ID {id_parameter}.")

        return value

    def validate_obd_fault_machinery(self, value):
        """
        Validaciones específicas para obd_fault_machinery
        """
        if not value:
            return value

        # 1) Validar que alert_enabled sea obligatorio cuando se proporciona id_obd_fault
        for item in value:
            id_obd_fault = item.get('id_obd_fault')
            alert_enabled = item.get('alert_enabled')

            if id_obd_fault is not None and alert_enabled is None:
                raise ValidationError(
                    f"El campo 'alert_enabled' es obligatorio cuando se proporciona 'id_obd_fault'."
                )

        # 2) Validar que no haya id_obd_fault duplicados
        seen_obd_faults = set()
        for item in value:
            id_obd_fault = item.get('id_obd_fault')
            if id_obd_fault in seen_obd_faults:
                raise ValidationError(f"El OBD fault con ID {id_obd_fault} está duplicado.")
            seen_obd_faults.add(id_obd_fault)

        return value

    def validate_event_type_machinery(self, value):
        """
        Validaciones específicas para event_type_machinery
        """
        if not value:
            return value

        # 1) Validar que si se proporciona id_event_type, threshold y alert_enabled sean obligatorios
        for item in value:
            id_event_type = item.get('id_event_type')
            threshold = item.get('threshold')
            alert_enabled = item.get('alert_enabled')

            if id_event_type is not None:
                if threshold is None:
                    raise ValidationError(
                        f"El campo 'threshold' es obligatorio cuando se proporciona 'id_event_type'."
                    )
                if alert_enabled is None:
                    raise ValidationError(
                        f"El campo 'alert_enabled' es obligatorio cuando se proporciona 'id_event_type'."
                    )

        # 2) Validar que no haya id_event_type duplicados
        seen_event_types = set()
        for item in value:
            id_event_type = item.get('id_event_type')
            if id_event_type in seen_event_types:
                raise ValidationError(f"El event type con ID {id_event_type} está duplicado.")
            seen_event_types.add(id_event_type)

        # 3) Validar que el threshold esté en el rango del parámetro ID 17
        try:
            parameter_17 = Parameters.objects.get(id=17)
            for item in value:
                threshold = item.get('threshold')
                if threshold is not None:
                    if (parameter_17.minimum_range is not None and
                        threshold < parameter_17.minimum_range):
                        raise ValidationError(
                            f"El threshold ({threshold}) no puede ser menor que "
                            f"el minimum_range del valor G definido ({parameter_17.minimum_range})."
                        )
                    if (parameter_17.maximum_range is not None and
                        threshold > parameter_17.maximum_range):
                        raise ValidationError(
                            f"El threshold ({threshold}) no puede ser mayor que "
                            f"el maximum_range del valor G definido ({parameter_17.maximum_range})."
                        )
        except Parameters.DoesNotExist:
            raise ValidationError("No se encontró el parámetro con ID 17.")

        return value

    def validate(self, data):
        """
        Validación general del serializer
        El id_machinery viene del contexto (query parameter)
        """
        # Obtener el id_machinery del contexto
        id_machinery_id = self.context.get('machinery_id')
        if not id_machinery_id:
            raise ValidationError({"error": "El id_machinery es requerido como query parameter."})

        # Validar que la maquinaria existe
        try:
            machinery = Machinery.objects.get(id_machinery=id_machinery_id)
            data['id_machinery'] = machinery
        except Machinery.DoesNotExist:
            raise ValidationError({"error": f"La maquinaria con ID {id_machinery_id} no existe."})

        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Crear/Actualizar todos los registros relacionados en una transacción:
        1. Eliminar todos los registros existentes de tolerance_thresholds, obd_fault_machinery y event_type_machinery
        2. Crear los nuevos registros
        """
        id_machinery = validated_data['id_machinery']
        updated_records = {
            'tolerance_thresholds': [],
            'obd_fault_machinery': [],
            'event_type_machinery': []
        }

        try:
            # 1. Eliminar todos los registros existentes para esta maquinaria
            ToleranceThresholds.objects.filter(id_machinery=id_machinery).delete()
            OBDFaultMachinery.objects.filter(id_machinery=id_machinery).delete()
            EventTypeMachinery.objects.filter(id_machinery=id_machinery).delete()

            # 2. Crear tolerance_thresholds
            for threshold_data in validated_data.get('tolerance_thresholds', []):
                threshold = ToleranceThresholds.objects.create(
                    id_machinery=id_machinery,
                    id_parameter_id=threshold_data['id_parameter'],
                    minimum_threshold=threshold_data.get('minimum_threshold'),
                    maximum_threshold=threshold_data.get('maximum_threshold'),
                    id_maintenance_id=threshold_data.get('id_maintenance'),
                    alert_enabled=threshold_data.get('alert_enabled')
                )
                updated_records['tolerance_thresholds'].append(threshold)

            # 3. Crear obd_fault_machinery
            for obd_data in validated_data.get('obd_fault_machinery', []):
                obd_fault = OBDFaultMachinery.objects.create(
                    id_obd_fault_id=obd_data['id_obd_fault'],
                    id_machinery=id_machinery,
                    alert_enabled=obd_data['alert_enabled'],
                    id_maintenance_id=obd_data.get('id_maintenance')
                )
                updated_records['obd_fault_machinery'].append(obd_fault)

            # 4. Crear event_type_machinery
            for event_data in validated_data.get('event_type_machinery', []):
                event_type = EventTypeMachinery.objects.create(
                    id_event_type_id=event_data['id_event_type'],
                    id_machinery=id_machinery,
                    id_maintenance_id=event_data.get('id_maintenance'),
                    threshold=event_data.get('threshold'),
                    alert_enabled=event_data.get('alert_enabled')
                )
                updated_records['event_type_machinery'].append(event_type)

            return {
                'id_machinery': id_machinery,
                'updated_records': updated_records
            }

        except Exception as e:
            raise ValidationError(f"Error al actualizar los registros: {str(e)}")
