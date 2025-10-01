from rest_framework import serializers
from maintenance.models import MaintenanceReport


class MaintenanceReportDetailSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar detalles completos de un reporte de mantenimiento.
    """
    
    # Información de la maquinaria (informativa)
    machinery_serial = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.serial_number', 
        read_only=True
    )
    machinery_name = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.machinery_name', 
        read_only=True
    )
    machinery_image = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.image_path', 
        read_only=True
    )
    machinery_type = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.machinery_type.name', 
        read_only=True
    )
    
    # Información del técnico asignado
    assigned_technician_id = serializers.IntegerField(
        source='id_maintenance_scheduling.assigned_technician.id_user', 
        read_only=True
    )
    
    # Información del usuario responsable
    responsible_user_id = serializers.IntegerField(
        source='id_responsible_user.id_user', 
        read_only=True
    )
    
    # Mantenimientos realizados
    maintenance_items = serializers.SerializerMethodField()
    
    # Repuestos utilizados
    spare_parts_used = serializers.SerializerMethodField()
    
    # Campos calculados
    total_time_minutes = serializers.SerializerMethodField()
    
    def get_total_time_minutes(self, obj):
        """
        Calcula el tiempo total en minutos.
        """
        return (obj.time_invested_hours * 60) + obj.time_invested_minutes
    
    def get_maintenance_items(self, obj):
        """
        Obtiene los mantenimientos realizados en este reporte.
        """
        from maintenance.models import MaintenanceMaintenanceReports
        from maintenance.serializers.maintenance_serializer import MaintenanceSerializer
        
        maintenance_relations = MaintenanceMaintenanceReports.objects.filter(
            id_maintenance_report=obj
        ).select_related('id_maintenance')
        
        maintenance_items = []
        for relation in maintenance_relations:
            maintenance_data = MaintenanceSerializer(relation.id_maintenance).data
            maintenance_data['assigned_technician_id'] = obj.id_maintenance_scheduling.assigned_technician.id_user
            maintenance_items.append(maintenance_data)
        
        return maintenance_items
    
    def get_spare_parts_used(self, obj):
        """
        Obtiene los repuestos utilizados en este reporte.
        """
        from maintenance.models import MaintenanceSparePartsMaintenance
        
        spare_parts_relations = MaintenanceSparePartsMaintenance.objects.filter(
            id_maintenance_report=obj
        ).select_related('id_maintenance_spare_part', 'id_maintenance_spare_part__spare_part_brand')
        
        spare_parts_used = []
        for relation in spare_parts_relations:
            spare_part = relation.id_maintenance_spare_part
            spare_parts_used.append({
                'id_maintenance_spare_part': spare_part.id_maintenance_spare_parts,
                'name': spare_part.name,
                'brand_name': spare_part.spare_part_brand.name,
                'quantity_used': relation.quantity_used,
                'unit_cost': relation.cost_at_time,
                'total_cost': relation.quantity_used * relation.cost_at_time
            })
        
        return spare_parts_used

    class Meta:
        model = MaintenanceReport
        fields = [
            'id_maintenance_report',
            'title',
            'description',
            'creation_date',
            'time_invested_hours',
            'time_invested_minutes',
            'total_time_minutes',
            'recommendations',
            'spare_parts_total_cost',
            'total_cost',
            'machinery_serial',
            'machinery_name',
            'machinery_image',
            'machinery_type',
            'assigned_technician_id',
            'responsible_user_id',
            'maintenance_items',
            'spare_parts_used',
            'registration_date',
            'modification_date'
        ]
