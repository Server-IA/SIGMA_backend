from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from ..models.invoice_issuer import InvoiceIssuer
from service_requests.serializers.invoice_serializers.invoice_issuer_serializer import InvoiceIssuerSerializer

logger = logging.getLogger(__name__)


class InvoiceIssuerViewSet(viewsets.ModelViewSet):
    queryset = InvoiceIssuer.objects.all()
    serializer_class = InvoiceIssuerSerializer
    lookup_field = 'id_invoice_issuer'

    def retrieve(self, request, pk=None, *args, **kwargs):
        instance = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
