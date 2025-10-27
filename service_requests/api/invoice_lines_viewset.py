from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from ..models.invoice_line import InvoiceLine
from service_requests.serializers.invoice_serializers.invoice_line_serializer import InvoiceLineSerializer

logger = logging.getLogger(__name__)


class InvoiceLineViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLine.objects.all()
    serializer_class = InvoiceLineSerializer
    lookup_field = 'id_invoice_line'

    def list(self, request, *args, **kwargs):
        invoice_id = request.query_params.get('invoice')
        qs = self.queryset
        if invoice_id:
            qs = qs.filter(invoice_id=invoice_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
