from rest_framework import serializers

from service_requests.models.services import Service


class ServiceListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id_service')
    name = serializers.CharField(source='service_name')
    unit_id = serializers.SerializerMethodField()
    unit_name = serializers.SerializerMethodField()
    status_id = serializers.SerializerMethodField()
    status_name = serializers.SerializerMethodField()
    service_type_id = serializers.SerializerMethodField()
    service_type_name = serializers.SerializerMethodField()
    

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'base_price',
            'unit_id',
            'unit_name',
            'applicable_tax',
            'tax_rate',
            'is_vat_exempt',
            'status_id',
            'status_name',
            'service_type_id',
            'service_type_name',
        ]

    def get_unit_id(self, obj):
        u = getattr(obj, 'price_unit', None)
        return (getattr(u, 'id_units', None) or getattr(u, 'pk', None)) if u else None

    def get_unit_name(self, obj):
        u = getattr(obj, 'price_unit', None)
        return getattr(u, 'name', None) if u else None

    def get_status_id(self, obj):
        s = getattr(obj, 'service_status', None)
        return (getattr(s, 'id_statues', None) or getattr(s, 'pk', None)) if s else None

    def get_status_name(self, obj):
        s = getattr(obj, 'service_status', None)
        return getattr(s, 'name', None) if s else None

    def get_service_type_id(self, obj):
        t = getattr(obj, 'service_type', None)
        return (getattr(t, 'id_types', None) or getattr(t, 'pk', None)) if t else None

    def get_service_type_name(self, obj):
        t = getattr(obj, 'service_type', None)
        return getattr(t, 'name', None) if t else None