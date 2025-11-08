from django.utils import timezone
from django.db.models import Max, Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from maintenance.models import MaintenanceRequest, Maintenance
from parameterization.models import Types, Statues
from monitoring.models import Data
from machinery.models import ToleranceThresholds, OBDFaultMachinery, EventTypeMachinery

class MaintenanceRequestFromServiceSerializer(serializers.Serializer):
    """
    Serializer for creating maintenance requests from service request data.
    """
    
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
    
    def get_maintenance_for_parameter(self, machinery_id, parameter_id):
        """Get maintenance for a specific parameter and machinery."""
        try:
            threshold = ToleranceThresholds.objects.get(
                id_machinery_id=machinery_id,
                id_parameter_id=parameter_id,
                alert_enabled=True,
                id_maintenance__isnull=False
            )
            return threshold.id_maintenance
        except ToleranceThresholds.DoesNotExist:
            return None
    
    def get_maintenance_for_obd_fault(self, machinery_id, obd_fault_code):
        """Get maintenance for a specific OBD fault and machinery."""
        try:
            obd_fault_machinery = OBDFaultMachinery.objects.get(
                id_machinery_id=machinery_id,
                id_obd_fault__code=obd_fault_code,
                alert_enabled=True,
                id_maintenance__isnull=False
            )
            return obd_fault_machinery.id_maintenance
        except OBDFaultMachinery.DoesNotExist:
            return None
    
    def get_maintenance_for_event_type(self, machinery_id, event_type_id):
        """Get maintenance for a specific event type and machinery."""
        try:
            event_type_machinery = EventTypeMachinery.objects.get(
                id_machinery_id=machinery_id,
                id_event_type_id=event_type_id,
                alert_enabled=True,
                id_maintenance__isnull=False
            )
            return event_type_machinery.id_maintenance
        except EventTypeMachinery.DoesNotExist:
            return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        service_request = self.context.get('service_request')
        
        # Get all machinery with alerts for this service request
        machinery_with_alerts = Data.objects.filter(
            id_request=service_request,
            alert=True,
            id_parameter_id__in=[3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        ).values_list('id_machinery', flat=True).distinct()
        
        created_requests = []
        
        for machinery_id in machinery_with_alerts:
            # Get all alert data for this machinery and service request
            machinery_data = Data.objects.filter(
                id_request=service_request,
                id_machinery_id=machinery_id,
                alert=True,
                id_parameter_id__in=[3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
            )
            
            # Process parameter alerts (3,6,7,8,9,10,11,12,14,15)
            parameter_alerts = machinery_data.filter(
                id_parameter_id__in=[3, 6, 7, 8, 9, 10, 11, 12, 14, 15]
            ).values_list('id_parameter_id', flat=True).distinct()
            
            # Process OBD fault alerts (13)
            obd_fault_alerts = machinery_data.filter(
                id_parameter_id=13,
                obd_fault__isnull=False
            ).values_list('obd_fault', flat=True).distinct()
            
            # Process event type alerts (16)
            event_type_alerts = machinery_data.filter(
                id_parameter_id=16,
                data__isnull=False
            ).values_list('data', flat=True).distinct()
            
            # Build description parts
            description_parts = []
            
            # Add parameter-related maintenance to description
            for param_id in parameter_alerts:
                maintenance = self.get_maintenance_for_parameter(machinery_id, param_id)
                if maintenance:
                    # Get parameter name from the data
                    param_name = Data.objects.filter(
                        id_machinery_id=machinery_id,
                        id_parameter_id=param_id,
                        alert=True
                    ).values_list('id_parameter__parameter_name', flat=True).first()
                    
                    if param_name:
                        description_parts.append(f"{param_name}: {maintenance.name}")
            
            # Add OBD fault-related maintenance to description
            for obd_fault in obd_fault_alerts:
                maintenance = self.get_maintenance_for_obd_fault(machinery_id, obd_fault)
                if maintenance:
                    # Get OBD fault code and maintenance from obd_faults_machinery
                    from machinery.models.obd_faults import OBD_Faults
                    from machinery.models.obd_fault_machinery import OBDFaultMachinery
                    
                    # First, get the OBD fault ID from the fault code
                    obd_fault_obj = OBD_Faults.objects.filter(
                        code=obd_fault
                    ).first()
                    
                    if not obd_fault_obj:
                        continue
                        
                    # Then find the OBD fault configuration for this machinery and fault ID
                    obd_config = OBDFaultMachinery.objects.filter(
                        id_machinery_id=machinery_id,
                        id_obd_fault_id=obd_fault_obj.id_obd_fault,
                        alert_enabled=True
                    ).select_related('id_obd_fault', 'id_maintenance').first()
                    
                    if obd_config and obd_config.id_obd_fault and obd_config.id_maintenance:
                        # Format as "code: maintenance_name"
                        description_parts.append(f"{obd_config.id_obd_fault.code}: {obd_config.id_maintenance.name}")
            
            # Add event type-related maintenance to description
            for event_type_id in event_type_alerts:
                maintenance = self.get_maintenance_for_event_type(machinery_id, int(float(event_type_id)))
                if maintenance:
                    # Get event type name from event_types table
                    from machinery.models.event_types import EventTypes
                    from machinery.models.event_type_machinery import EventTypeMachinery
                    
                    # Get the event type name (1: Aceleracion, 2: Frenado, 3: Curva)
                    event_mapping = {
                        '1': 'Aceleracion',
                        '2': 'Frenado',
                        '3': 'Curva'
                    }
                    event_name = event_mapping.get(str(int(float(event_type_id))))
                    
                    if event_name:
                        # Find the maintenance for this event type and machinery
                        event_maintenance = EventTypeMachinery.objects.filter(
                            id_machinery_id=machinery_id,
                            id_event_type_id=int(float(event_type_id)),
                            alert_enabled=True
                        ).select_related('id_maintenance').first()
                        
                        if event_maintenance and event_maintenance.id_maintenance:
                            description_parts.append(f"{event_name}: {event_maintenance.id_maintenance.name}")
            
            if not description_parts:
                continue  # Skip if no maintenance items found
                
            # Join description parts with semicolons and spaces
            description = "; ".join(description_parts)
            
            # Get or create maintenance type (id_types_categories=12) - using first one as default
            maintenance_type = Types.objects.filter(
                id_types_categories=12
            ).first()
            
            if not maintenance_type:
                raise ValidationError("No maintenance type found with id_types_categories=12")
            
            # Get or create priority (id_types_categories=13) - using first one as default
            priority = Types.objects.filter(
                id_types_categories=13
            ).first()
            
            if not priority:
                raise ValidationError("No priority type found with id_types_categories=13")
            
            # Get request status (10 = Pending)
            try:
                request_status = Statues.objects.get(pk=10)
            except Statues.DoesNotExist:
                raise ValidationError("Status with id=10 does not exist")
            
            # Create maintenance request
            maintenance_request = MaintenanceRequest.objects.create(
                id_maintenance_request=self.generate_request_id(),
                id_machinery_id=machinery_id,
                maintenance_type=maintenance_type,
                description=description,
                priority=priority,
                request_status=request_status,
                detected_at=timezone.now().date(),
                id_responsible_user=None,  # Set to None as required
                id_response_user_id=getattr(request.user, 'id', None) if request and hasattr(request, 'user') else None
            )
            
            created_requests.append(maintenance_request)
        
        return created_requests
