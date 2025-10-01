from rest_framework import serializers
from maintenance.models import (
    MaintenanceReport, 
    MaintenanceMaintenanceReports, 
    MaintenanceSparePartsMaintenance,
    MaintenanceScheduling
)
from maintenance.models import MaintenanceSpareParts
from users.models.user import User


class MaintenanceReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear reportes de mantenimiento.
    """
    
    # Campos para mantenimientos realizados
    # Ahora acepta objetos: { id_maintenance, maintenance_cost }
    maintenance_items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de objetos con id_maintenance y maintenance_cost"
    )
    
    # Campos para repuestos utilizados
    spare_parts = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de repuestos utilizados con cantidad y costo"
    )
    
    # Usuario responsable (viene del body y se mapea al FK id_responsible_user)
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    
    def validate_id_maintenance_scheduling(self, value):
        """
        Valida que el mantenimiento programado exista y esté en estado 13 (pendiente de reporte).
        """
        if not value:
            raise serializers.ValidationError("El mantenimiento programado es obligatorio.")
        
        try:
            scheduling = MaintenanceScheduling.objects.select_related(
                'maintenance_scheduling_status'
            ).get(pk=value.id_maintenance_scheduling)
        except MaintenanceScheduling.DoesNotExist:
            raise serializers.ValidationError("El mantenimiento programado no existe.")
        
        # Validar que el mantenimiento esté en estado 13 (pendiente de reporte)
        if scheduling.maintenance_scheduling_status.id_statues != 13:
            raise serializers.ValidationError(
                "Solo se pueden crear reportes para mantenimientos en estado 13."
            )
        
        return value
    
    def validate_maintenance_items(self, value):
        """
        Valida que los mantenimientos existan y que el costo sea válido.
        """
        if not value:
            raise serializers.ValidationError("Debe especificar al menos un mantenimiento realizado.")
        ids = []
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Cada item debe ser un objeto con id_maintenance y maintenance_cost")
            if 'id_maintenance' not in item:
                raise serializers.ValidationError("Falta 'id_maintenance' en un item de maintenance_items")
            if 'maintenance_cost' not in item:
                raise serializers.ValidationError("Falta 'maintenance_cost' en un item de maintenance_items")
            try:
                cost = float(item['maintenance_cost'])
                if cost < 0:
                    raise serializers.ValidationError("'maintenance_cost' debe ser >= 0")
            except (TypeError, ValueError):
                raise serializers.ValidationError("'maintenance_cost' debe ser numérico")
            ids.append(item['id_maintenance'])

        from maintenance.models import Maintenance
        existing_maintenances = Maintenance.objects.filter(
            id_maintenance__in=ids
        ).values_list('id_maintenance', flat=True)
        missing_ids = set(ids) - set(existing_maintenances)
        if missing_ids:
            raise serializers.ValidationError(
                f"Los siguientes mantenimientos no existen: {list(missing_ids)}"
            )
        
        return value
    
    def validate_spare_parts(self, value):
        """
        Valida que los repuestos existan y tengan datos válidos.
        """
        if not value:
            return value
        
        for spare_part in value:
            if 'id_maintenance_spare_part' not in spare_part:
                raise serializers.ValidationError(
                    "Cada repuesto debe tener 'id_maintenance_spare_part'"
                )
            
            if 'quantity_used' not in spare_part:
                raise serializers.ValidationError(
                    "Cada repuesto debe tener 'quantity_used'"
                )
            
            if 'cost_at_time' not in spare_part:
                raise serializers.ValidationError(
                    "Cada repuesto debe tener 'cost_at_time'"
                )
            
            # Validar que el repuesto exista
            try:
                MaintenanceSpareParts.objects.get(
                    id_maintenance_spare_parts=spare_part['id_maintenance_spare_part']
                )
            except MaintenanceSpareParts.DoesNotExist:
                raise serializers.ValidationError(
                    f"El repuesto {spare_part['id_maintenance_spare_part']} no existe"
                )
            
            # Validar valores positivos
            if spare_part['quantity_used'] <= 0:
                raise serializers.ValidationError(
                    "La cantidad utilizada debe ser mayor a 0"
                )
            
            if spare_part['cost_at_time'] <= 0:
                raise serializers.ValidationError(
                    "El costo debe ser mayor a 0"
                )
        
        return value
    
    def validate(self, data):
        """
        Validaciones adicionales del serializer.
        """
        # Validar que el tiempo invertido sea positivo
        if data.get('time_invested_hours', 0) < 0:
            raise serializers.ValidationError({
                'time_invested_hours': 'Las horas deben ser mayor o igual a 0'
            })
        
        if data.get('time_invested_minutes', 0) < 0 or data.get('time_invested_minutes', 0) >= 60:
            raise serializers.ValidationError({
                'time_invested_minutes': 'Los minutos deben estar entre 0 y 59'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Crea el reporte de mantenimiento con sus relaciones.
        """
        # Extraer datos de relaciones
        maintenance_items = validated_data.pop('maintenance_items', [])
        spare_parts = validated_data.pop('spare_parts', [])
        responsible_user = validated_data.pop('responsible_user')
        
        # Calcular costo total de repuestos
        spare_parts_total_cost = sum(
            item['quantity_used'] * item['cost_at_time'] 
            for item in spare_parts
        )
        validated_data['spare_parts_total_cost'] = spare_parts_total_cost

        # Calcular costo total de mantenimientos
        maint_total_cost = sum(float(i.get('maintenance_cost', 0)) for i in maintenance_items)
        # Total general
        validated_data['total_cost'] = spare_parts_total_cost + maint_total_cost
        
        # Crear el reporte
        validated_data['id_responsible_user'] = responsible_user
        report = MaintenanceReport.objects.create(**validated_data)
        
        # Crear relaciones con mantenimientos
        for item in maintenance_items:
            MaintenanceMaintenanceReports.objects.create(
                id_maintenance_id=item['id_maintenance'],
                id_maintenance_report=report,
                maintenance_cost=float(item['maintenance_cost'])
            )
        
        # Crear relaciones con repuestos
        for spare_part_data in spare_parts:
            MaintenanceSparePartsMaintenance.objects.create(
                id_maintenance_spare_part_id=spare_part_data['id_maintenance_spare_part'],
                id_maintenance_report=report,
                quantity_used=spare_part_data['quantity_used'],
                cost_at_time=spare_part_data['cost_at_time']
            )
        
        return report

    class Meta:
        model = MaintenanceReport
        fields = [
            'title',
            'description',
            'id_maintenance_scheduling',
            'time_invested_hours',
            'time_invested_minutes',
            'recommendations',
            'maintenance_items',
            'spare_parts',
            'responsible_user'
        ]
