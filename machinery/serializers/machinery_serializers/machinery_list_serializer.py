from rest_framework import serializers
from machinery.models.machinery import Machinery
from machinery.models.machinery_usage_sheet import MachineryUsageSheet

class MachineryListSerializer(serializers.ModelSerializer):
    id_machinery_secondary_type = serializers.SerializerMethodField()
    machinery_secondary_type_name = serializers.SerializerMethodField()
    id_machinery_operational_status = serializers.SerializerMethodField()
    machinery_operational_status_name = serializers.SerializerMethodField()
    acquisition_date = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()

    class Meta:
        model = Machinery
        fields = [
            'id_machinery',
            'image_path',
            'machinery_name',
            'serial_number',
            'id_machinery_secondary_type',
            'machinery_secondary_type_name',
            'acquisition_date',
            'id_machinery_operational_status',
            'machinery_operational_status_name'
        ]
        extra_kwargs = {
            'image_path': {'allow_null': True, 'required': False}
        }

    def get_id_machinery_secondary_type(self, obj):
        return obj.machinery_secondary_type_id

    def get_machinery_secondary_type_name(self, obj):
        return getattr(obj.machinery_secondary_type, 'name', None) if obj.machinery_secondary_type_id else None

    def get_id_machinery_operational_status(self, obj):
        return obj.machinery_operational_status_id

    def get_machinery_operational_status_name(self, obj):
        return getattr(obj.machinery_operational_status, 'name', None) if obj.machinery_operational_status_id else None
        
    def get_image_path(self, obj):
        if not obj.image_path:
            return None
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image_path)
        return obj.image_path

    def get_acquisition_date(self, obj):
        try:
            usage_sheet = getattr(obj, 'machineryusagesheet_set', None)
            if usage_sheet and hasattr(usage_sheet, 'first') and usage_sheet.exists():
                return usage_sheet.first().acquisition_date
            return None
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting acquisition date: {str(e)}")
            return None
