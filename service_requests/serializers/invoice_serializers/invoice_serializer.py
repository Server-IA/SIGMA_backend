# service_requests/serializers/invoice_serializers/invoice.py

from rest_framework import serializers
from service_requests.models.invoice import Invoice
from service_requests.models.payment_method import PaymentMethod
from parameterization.models import Statues
from django.db import transaction
from .invoice_line_serializer import InvoiceLineSerializer
from service_requests.models.invoice_line import InvoiceLine

# ----------------------------------------------------------------------
# 2. SERIALIZER DE LECTURA DE LISTA
# ----------------------------------------------------------------------
class InvoiceListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.legal_entity_name', read_only=True) 
    # Exponer el id del estado y el nombre legible
    invoice_status_id = serializers.IntegerField(source='status_id', read_only=True)
    invoice_status_name = serializers.CharField(source='status.name', read_only=True)
    service_request_id = serializers.CharField(source='service_request.id_request', read_only=True) # ID de la solicitud

    class Meta:
        model = Invoice
        fields = ('id_invoice', 'reference_code', 'invoice_date', 'amount_to_pay', 'invoice_status_id', 'invoice_status_name', 'customer_name', 'service_request_id')

# ----------------------------------------------------------------------
# 3. SERIALIZER DE LECTURA DE DETALLE
# ----------------------------------------------------------------------
class InvoiceDetailSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.legal_entity_name', read_only=True)
    service_request_id = serializers.CharField(source='service_request.id_request', read_only=True)
    tax_regime_name = serializers.CharField(source='tax_regime.name', read_only=True) 
    status = serializers.SerializerMethodField(read_only=True)
    api_response = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        """Remover campos sensibles/no deseados de la representación final.

        Nota: `api_response` se expone en forma reducida a través de
        `get_api_response` en lugar del JSON completo.
        """
        data = super().to_representation(instance)

        # Remover payload técnico de Factus en el detalle de las líneas
        try:
            lines = data.get('lines', [])
            if isinstance(lines, list):
                for item in lines:
                    if isinstance(item, dict):
                        item.pop('factus_payload', None)
        except Exception:
            # En caso de cualquier problema al manipular las líneas, continuar sin romper respuesta
            pass

        return data

    def get_api_response(self, obj):
        """Devuelve un resumen seguro de la respuesta de Factus (si existe).

        Extrae campos relevantes de `api_response.data.bill` si está presente.
        """
        api = getattr(obj, 'api_response', None) or {}
        bill = {}
        try:
            bill = api.get('data', {}).get('bill', {}) if isinstance(api, dict) else {}
        except Exception:
            bill = {}

        if not bill:
            return None

        keys = ['cufe', 'number', 'public_url', 'qr', 'total', 'tax_amount', 'surcharge_amount', 'discount_amount']
        summary = {}
        for k in keys:
            if k in bill and bill.get(k) is not None:
                summary[k] = bill.get(k)

        return summary or None

    def get_status(self, obj):
        """Devuelve una representación compacta del estado de la factura."""
        st = getattr(obj, 'status', None)
        if not st:
            return None
        
        data = {}
        if hasattr(st, 'id_statues'):
            data['id_statues'] = getattr(st, 'id_statues')
        else:
            data['id_statues'] = getattr(st, 'id', None)
        data['name'] = getattr(st, 'name', '')
        return data

# ----------------------------------------------------------------------
# 4. SERIALIZER DE CREACIÓN/ACTUALIZACIÓN DE BORRADOR 
# ----------------------------------------------------------------------
class InvoiceDraftCreationSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, required=False, allow_null=True)
    invoice_id = serializers.IntegerField(required=False, write_only=True) 
    service_request = serializers.CharField(write_only=True)

    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'El método de pago seleccionado no existe.',
            'incorrect_type': 'Formato inválido para el método de pago.'
        }
    )

    def validate_service_request(self, value):
        """Validate and resolve the incoming service_request identifier.

        Accepts either a PK as digits or an id_request code like 'SOL-2025-004'.
        Returns the resolved ServiceRequest instance or raises ValidationError.
        """
        try:
            from service_requests.models.service_request import ServiceRequest
        except Exception:
            raise serializers.ValidationError('No se pudo resolver la solicitud de servicio proporcionada.')

        if isinstance(value, str) and value.isdigit():
            try:
                return ServiceRequest.objects.get(pk=int(value))
            except ServiceRequest.DoesNotExist:
                raise serializers.ValidationError(f"Service request con id '{value}' no existe.")

        try:
            return ServiceRequest.objects.get(id_request=value)
        except ServiceRequest.DoesNotExist:
            raise serializers.ValidationError(f"Service request '{value}' no existe.")

    class Meta:
        model = Invoice
        fields = ('invoice_id', 'customer', 'observation', 'lines', 'tax_regime', 'service_request', 'payment_method')
        extra_kwargs = {
            'customer': {'required': True},
            'tax_regime': {'required': True},
            'payment_method': {'required': False},
            'lines': {'required': False},
        }

    @transaction.atomic
    def create(self, validated_data):
        from service_requests.utils.invoice_generator_utils import recalculate_invoice_totals
        
        # 1. Extraer data de líneas. NOTA: Los objetos FK ya están resueltos aquí.
        lines_data = validated_data.pop('lines', [])
        invoice = Invoice.objects.create(**validated_data)
        
        # 2. Creamos el serializer de línea *solo* para acceder al método `create`
        line_serializer = InvoiceLineSerializer()
        
        for line_validated_data in lines_data:
            # 3. Usar la data que ya fue validada y resuelta por el serializer padre
            # Le inyectamos la FK de la factura
            line_serializer.create(validated_data={**line_validated_data, 'invoice': invoice}) 
        
        recalculate_invoice_totals(invoice)
        return invoice

    @transaction.atomic
    def update(self, instance, validated_data):
        from service_requests.utils.invoice_generator_utils import recalculate_invoice_totals
        
        lines_data = validated_data.pop('lines', [])
        
        instance.save()

        InvoiceLine.objects.filter(invoice=instance).delete()
        
        line_serializer = InvoiceLineSerializer()
        
        for line_validated_data in lines_data:
            line_serializer.create(validated_data={**line_validated_data, 'invoice': instance})
        
        recalculate_invoice_totals(instance)
        return instance