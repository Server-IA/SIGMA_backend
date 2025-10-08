from rest_framework import serializers
from maintenance.models import (
    MaintenanceReport, 
    MaintenanceMaintenanceReports, 
    MaintenanceReportSpareParts,
    MaintenanceScheduling
)
from users.models.user import User
from parameterization.models import Brands, Units, Statues, BrandsCategory

class MaintenanceReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear reportes de mantenimiento.
    """
    
    # Campos para mantenimientos realizados
    # Acepta objetos: { id_maintenance, id_technician, maintenance_cost }
    maintenance_items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de objetos con id_maintenance, id_technician y maintenance_cost"
    )
    
    # Campos para repuestos utilizados
    spare_parts = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="Lista de repuestos utilizados con cantidad y costo"
    )
    
    # Usuario responsable (viene del body y se mapea al FK id_responsible_user)
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        required=False,  # No es requerido en el input
        write_only=True
    )
    
    currency_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(),
        required=True,
        help_text="Unidad de moneda para los costos del reporte"
    )
    
    # Lista de IDs de técnicos asignados al reporte
    technicians = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="Lista de IDs de usuarios técnicos asignados al reporte"
    )
    
    def validate_id_maintenance_scheduling(self, value):
        """
        Valida que el mantenimiento programado exista, no tenga reportes previos
        y esté en estado 13 (Programado).
        """
        if not value:
            raise serializers.ValidationError("El mantenimiento programado es obligatorio.")
        
        try:
            # Obtener el mantenimiento programado con su estado
            scheduling = MaintenanceScheduling.objects.select_related(
                'maintenance_scheduling_status'
            ).prefetch_related('maintenance_reports'  # Usando el related_name definido en el modelo
            ).get(pk=value.id_maintenance_scheduling)
            
            # Verificar si ya existe un reporte para este mantenimiento programado
            if scheduling.maintenance_reports.exists():
                raise serializers.ValidationError(
                    "Ya existe un reporte creado para este mantenimiento programado."
                )
                
        except MaintenanceScheduling.DoesNotExist:
            raise serializers.ValidationError("El mantenimiento programado no existe.")
        
        if scheduling.maintenance_scheduling_status.id_statues != 13:
            try:
                expected_status = Statues.objects.get(id_statues=13)
                current_status = Statues.objects.get(id_statues=scheduling.maintenance_scheduling_status.id_statues)
                error_message = (
                    f"Solo se pueden crear reportes para mantenimientos en estado '{expected_status.name}'. "
                    f"El estado actual es '{current_status.name}'"
                )
                raise serializers.ValidationError(error_message)
            except Statues.DoesNotExist:
                raise serializers.ValidationError("Estado de mantenimiento programado no encontrado")
        
        return value
    
    def validate_maintenance_items(self, value):
        """
        Valida que los mantenimientos y técnicos existan, que el costo sea válido
        y que no haya mantenimientos duplicados.
        """
        if not value:
            raise serializers.ValidationError("Debe especificar al menos un mantenimiento realizado.")
        
        maintenance_ids = []
        user_ids = []
        seen_maintenance_ids = set()
        
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Cada item debe ser un objeto con id_maintenance, id_technician y maintenance_cost")
                
            # Validar campos requeridos
            required_fields = ['id_maintenance', 'id_technician', 'maintenance_cost']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Falta '{field}' en un item de maintenance_items")
            
            # Validar que no haya id_maintenance duplicados
            maintenance_id = item['id_maintenance']
            if maintenance_id in seen_maintenance_ids:
                raise serializers.ValidationError(
                    f"El mantenimiento con ID {maintenance_id} está duplicado en la lista de items"
                )
            seen_maintenance_ids.add(maintenance_id)
            
            # Validar costo
            try:
                cost = float(item['maintenance_cost'])
                if cost < 0:
                    raise serializers.ValidationError("'maintenance_cost' debe ser >= 0")
            except (TypeError, ValueError):
                raise serializers.ValidationError("'maintenance_cost' debe ser numérico")
                
            # Validar id_technician
            try:
                technician_id = int(item['id_technician'])
                if technician_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise serializers.ValidationError("El id_technician debe ser un número entero positivo")
                
            maintenance_ids.append(maintenance_id)
            user_ids.append(technician_id)
            
        # Verificar que existan los mantenimientos
        from maintenance.models import Maintenance
        existing_maintenances = set(Maintenance.objects.filter(
            id_maintenance__in=maintenance_ids
        ).values_list('id_maintenance', flat=True))
        
        missing_maintenances = set(maintenance_ids) - existing_maintenances
        if missing_maintenances:
            raise serializers.ValidationError(
                f"Los siguientes mantenimientos no existen: {list(missing_maintenances)}"
            )
            
        # Verificar que existan los técnicos
        existing_users = set(User.objects.filter(
            id_user__in=user_ids
        ).values_list('id_user', flat=True))
        
        missing_users = set(user_ids) - existing_users
        if missing_users:
            raise serializers.ValidationError(
                f"Los siguientes IDs de técnico no existen: {list(missing_users)}"
            )
            
        return value
    
    def validate_spare_parts(self, value):
        """
        Valida que los repuestos tengan datos válidos y filtra campos no deseados.
        """
        if not value:
            return value
        
        validated_spare_parts = []
        
        for spare_part in value:
            # Validar campos requeridos
            required_fields = ['spare_part_brand', 'name', 'quantity_used', 'cost_at_time']
            for field in required_fields:
                if field not in spare_part:
                    raise serializers.ValidationError(
                        f"Cada repuesto debe tener '{field}'"
                    )
            
            try:
                brand = Brands.objects.select_related('id_brands_categories').get(
                    id_brands=spare_part['spare_part_brand']
                )
                if brand.id_brands_categories.id_brands_categories != 2:
                    try:
                        expected_category = BrandsCategory.objects.get(id_brands_categories=2)
                        raise serializers.ValidationError(
                            f"La marca {brand.name} debe pertenecer a la categoría '{expected_category.name}'"
                        )
                    except BrandsCategory.DoesNotExist:
                        raise serializers.ValidationError("Categoría de marca no encontrada")
            except Brands.DoesNotExist:
                raise serializers.ValidationError(
                    f"La marca con ID {spare_part['spare_part_brand']} no existe"
                )
            
            if spare_part['quantity_used'] <= 0:
                raise serializers.ValidationError(
                    "La cantidad utilizada debe ser mayor a 0"
                )
            
            if spare_part['cost_at_time'] <= 0:
                raise serializers.ValidationError(
                    "El costo en el momento debe ser mayor a 0"
                )
            
            # Crear un nuevo diccionario solo con los campos válidos
            validated_part = {
                'spare_part_brand': spare_part['spare_part_brand'],
                'name': spare_part['name'],
                'quantity_used': spare_part['quantity_used'],
                'cost_at_time': spare_part['cost_at_time']
            }
            validated_spare_parts.append(validated_part)
        
        return validated_spare_parts
    
    def validate_currency_unit(self, value):
        """
        Valida que la unidad de moneda pertenezca a la categoría con id 10.
        """
        if value.id_units_categories_id != 10:
            from parameterization.models import UnitsCategory
            try:
                expected_category = UnitsCategory.objects.get(id_units_categories=10)
                raise serializers.ValidationError(
                    f"La unidad de moneda debe pertenecer a la categoría '{expected_category.name}'."
                )
            except UnitsCategory.DoesNotExist:
                raise serializers.ValidationError("Categoría de unidad de moneda no encontrada")
        return value
        
    def validate(self, data):
        """
        Validaciones adicionales del serializer.
        """
        # Obtener el usuario del contexto si está disponible
        user = self.context.get('user')
        if not user and 'request' in self.context:
            user = self.context['request'].user
            
        # Si no hay usuario autenticado y no se proporcionó responsable, lanzar error
        if not user and 'responsible_user' not in data:
            raise serializers.ValidationError({
                'non_field_errors': ['Usuario no autenticado']
            })
            
        # Si no se proporcionó responsable, usar el usuario autenticado
        if 'responsible_user' not in data and user:
            data['responsible_user'] = user
            
        # Validar que el tiempo invertido sea positivo
        if data.get('time_invested_hours', 0) < 0 or data.get('time_invested_hours', 0) >= 100:
            raise serializers.ValidationError({
                'time_invested_hours': 'Las horas deben estar entre 0 y 99'
            })
        
        if data.get('time_invested_minutes', 0) < 0 or data.get('time_invested_minutes', 0) >= 60:
            raise serializers.ValidationError({
                'time_invested_minutes': 'Los minutos deben estar entre 0 y 59'
            })
            
        if data.get('time_invested_seconds', 0) < 0 or data.get('time_invested_seconds', 0) >= 60:
            raise serializers.ValidationError({
                'time_invested_seconds': 'Los segundos deben estar entre 0 y 59'
            })
        
        # Validar que los técnicos en maintenance_items estén en la lista de technicians
        maintenance_items = data.get('maintenance_items', [])
        technicians = set(data.get('technicians', []))
        
        if maintenance_items and not technicians:
            raise serializers.ValidationError({
                'technicians': 'Se requieren técnicos cuando se especifican ítems de mantenimiento'
            })
            
        for i, item in enumerate(maintenance_items):
            technician_id = item.get('id_technician')
            if technician_id is not None and technician_id not in technicians:
                raise serializers.ValidationError({
                    'maintenance_items': {
                        i: {
                            'id_technician': f'El técnico con ID {technician_id} no está en la lista de técnicos asignados'
                        }
                    }
                })
        
        return data
    
    def validate_technicians(self, value):
        """
        Valida que los IDs de los técnicos existan y no estén duplicados.
        """
        if not value:
            return value
            
        # Verificar que no haya IDs duplicados
        if len(value) != len(set(value)):
            from collections import Counter
            duplicates = [k for k, v in Counter(value).items() if v > 1]
            raise serializers.ValidationError(
                f"Hay IDs de técnicos duplicados: {duplicates}. Cada técnico solo puede aparecer una vez."
            )
            
        # Verificar que todos los IDs de usuario existan
        existing_users = set(User.objects.filter(id_user__in=value).values_list('id_user', flat=True))
        invalid_ids = set(value) - existing_users
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"Los siguientes IDs de usuario no existen: {list(invalid_ids)}"
            )
            
        return value
    
    def create(self, validated_data):
        """
        Crea el reporte de mantenimiento con sus relaciones.
        Actualiza el estado del mantenimiento programado a 15 (Completado)
        y el estado de la maquinaria a 4 (Disponible).
        """
        from django.db import transaction
        
        # Extraer datos de relaciones
        maintenance_items = validated_data.pop('maintenance_items', [])
        spare_parts = validated_data.pop('spare_parts', [])
        responsible_user = validated_data.pop('responsible_user')
        technicians = validated_data.pop('technicians', [])
        maintenance_scheduling = validated_data.get('id_maintenance_scheduling')
        
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
        validated_data['currency_unit'] = validated_data.pop('currency_unit')
        report = MaintenanceReport.objects.create(**validated_data)
        
        # Asignar técnicos al reporte
        if technicians:
            report.assigned_users.add(*technicians)
        
        # Crear relaciones con mantenimientos
        for item in maintenance_items:
            MaintenanceMaintenanceReports.objects.create(
                id_maintenance_id=item['id_maintenance'],
                id_maintenance_report=report,
                id_technician_id=item['id_technician'],
                maintenance_cost=float(item['maintenance_cost'])
            )
        
        # Crear repuestos del reporte
        for spare_part_data in spare_parts:
            MaintenanceReportSpareParts.objects.create(
                id_maintenance_report=report,
                spare_part_brand_id=spare_part_data['spare_part_brand'],
                name=spare_part_data['name'],
                quantity_used=spare_part_data['quantity_used'],
                cost_at_time=spare_part_data['cost_at_time']
            )
        
        # Actualizar estado del mantenimiento programado a 15 (Completado)
        # y estado de la maquinaria a 4 (Disponible) de manera atómica
        try:
            with transaction.atomic():
                # Get the maintenance scheduling record
                scheduling = report.id_maintenance_scheduling
                if not scheduling:
                    raise ValueError("No se encontró el mantenimiento programado asociado")
                
                # Get both statuses first to fail fast if they don't exist
                completed_status = Statues.objects.get(id_statues=15)
                available_status = Statues.objects.get(id_statues=4)
                
                # Update maintenance scheduling status to 15 (Completed)
                scheduling.maintenance_scheduling_status = completed_status
                scheduling.save()
                
                # Update related machinery status to 4 (Available)
                if hasattr(scheduling, 'id_machinery') and scheduling.id_machinery is not None:
                    scheduling.id_machinery.machinery_operational_status = available_status
                    scheduling.id_machinery.save()
                
                return report
                
        except Statues.DoesNotExist as e:
            error_msg = f"No se encontró uno de los estados requeridos: {str(e)}"
            raise serializers.ValidationError({"non_field_errors": [error_msg]})
            
        except ValueError as e:
            error_msg = f"Error de validación: {str(e)}"
            raise serializers.ValidationError({"non_field_errors": [error_msg]})
            
        except Exception as e:
            # Cualquier otro error inesperado
            error_msg = f"Error inesperado al actualizar los estados: {str(e)}"
            raise serializers.ValidationError({"non_field_errors": [error_msg]})
        
    class Meta:
        model = MaintenanceReport
        fields = [
            'title',
            'description',
            'id_maintenance_scheduling',
            'time_invested_hours',
            'time_invested_minutes',
            'time_invested_seconds',
            'currency_unit',
            'recommendations',
            'maintenance_items',
            'spare_parts',
            'responsible_user',
            'technicians'
        ]
