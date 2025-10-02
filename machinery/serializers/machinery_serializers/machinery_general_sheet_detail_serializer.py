from rest_framework import serializers
from machinery.models import Machinery
from parameterization.models.types import Types
from parameterization.models.brands import Brands
from parameterization.models.brand_model import Models
from parameterization.models.statues import Statues


class MachineryDetailSerializer(serializers.ModelSerializer):
    machinery_type = serializers.PrimaryKeyRelatedField(read_only=True)
    machinery_type_name = serializers.SerializerMethodField()
    
    machinery_secondary_type = serializers.PrimaryKeyRelatedField(read_only=True)
    machinery_secondary_type_name = serializers.SerializerMethodField()
    
    machinery_operational_status = serializers.PrimaryKeyRelatedField(read_only=True)
    machinery_operational_status_name = serializers.SerializerMethodField()
    
    id_model = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    model_name = serializers.SerializerMethodField()
    
    brand_id = serializers.IntegerField(source='id_model.id_brand_id', read_only=True)
    brand_name = serializers.SerializerMethodField()
    
    id_device = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    
    def get_machinery_type_name(self, obj):
        return obj.machinery_type.name if obj.machinery_type else None
    
    def get_machinery_secondary_type_name(self, obj):
        return obj.machinery_secondary_type.name if obj.machinery_secondary_type else None
    
    def get_machinery_operational_status_name(self, obj):
        return obj.machinery_operational_status.name if obj.machinery_operational_status else None
    
    def get_model_name(self, obj):
        return obj.id_model.name if obj.id_model else None
    
    def get_brand_name(self, obj):
        return obj.id_model.id_brand.name if (obj.id_model and obj.id_model.id_brand) else None

    class Meta:
        model = Machinery
        fields = [
            'machinery_name',
            'manufacturing_year',
            'serial_number',
            'machinery_type', 'machinery_type_name',
            'brand_id', 'brand_name',
            'id_model', 'model_name',
            'tariff_subheading',
            'machinery_secondary_type', 'machinery_secondary_type_name',
            'id_country',
            'id_department',
            'id_city',
            'image_path',
            'id_device',
            'justification',
            'machinery_operational_status', 'machinery_operational_status_name',
        ]