from rest_framework import serializers
from monitoring.models.data import Data
from service_requests.models.request_machinery_user import RequestMachineryUser
from machinery.models.machinery import Machinery
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.obd_faults import OBD_Faults

class DataSerializer(serializers.Serializer):
    machinery_name = serializers.CharField()
    serial_number = serializers.CharField()
    id_user = serializers.IntegerField()
    id_device = serializers.IntegerField()
    imei = serializers.CharField()
    parameters = serializers.ListField(child=serializers.DictField())

def get_machinery_data(request_id):
    # Get all machinery assigned to this request with their users
    request_machinery = RequestMachineryUser.objects.filter(request_id=request_id).select_related(
        'machinery',
        'user',
        'machinery__id_device'
    )
    
    result = []
    
    for rm in request_machinery:
        machinery = rm.machinery
        if not machinery.id_device:
            continue
            
        # Get all data points for this device in this request
        data_points = Data.objects.filter(
            id_device=machinery.id_device,
            id_request=request_id
        ).select_related('id_parameter')
        
        # Organize data by parameter
        parameters_data = {}
        for data in data_points:
            param_id = data.id_parameter.id_parameter
            if param_id not in parameters_data:
                parameters_data[param_id] = {
                    'parameter_id': param_id,
                    'parameter_name': data.id_parameter.parameter_name,
                    'data_points': []
                }
            
            # Get OBD fault name if exists
            obd_fault_name = None
            if data.obd_fault:
                try:
                    fault = OBD_Faults.objects.get(code=data.obd_fault)
                    obd_fault_name = fault.description
                except OBD_Faults.DoesNotExist:
                    obd_fault_name = None
            
            parameters_data[param_id]['data_points'].append({
                'data': data.data,
                'registered_at': data.registered_at,
                'obd_fault': data.obd_fault,
                'obd_fault_name': obd_fault_name,
                'alert': data.alert
            })
        
        # Convert dict to list
        parameters_list = list(parameters_data.values())
        
        result.append({
            'machinery_name': machinery.machinery_name,
            'serial_number': machinery.serial_number,
            'id_user': rm.user.id,
            'id_device': machinery.id_device.id_device,
            'imei': machinery.id_device.IMEI,
            'parameters': parameters_list
        })
    
    return result
