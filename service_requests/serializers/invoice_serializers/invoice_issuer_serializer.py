from rest_framework import serializers
from service_requests.models.invoice_issuer import InvoiceIssuer


class InvoiceIssuerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceIssuer
        fields = '__all__'
        read_only_fields = ('id_invoice_issuer', 'created_at')
