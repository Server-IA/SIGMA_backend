from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from ..models.invoice_line import InvoiceLine
from service_requests.serializers.invoice_serializers.invoice_line_serializer import InvoiceLineSerializer

logger = logging.getLogger(__name__)

# Constantes de permisos
PERM_INVOICE_LINES_CRUD = 157


class InvoiceLineViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLine.objects.all()
    serializer_class = InvoiceLineSerializer
    lookup_field = 'id_invoice_line'

    def check_permission(self, request, required_permission_id: int):
        """Verifica permisos del usuario."""
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []
        permisos_usuario = []
        
        for rol in user_roles:
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))
        
        is_authenticated = getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False)
        return is_authenticated and (required_permission_id in permisos_usuario)

    def list(self, request, *args, **kwargs):
        # Verificar autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"status": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso
        if not self.check_permission(request, PERM_INVOICE_LINES_CRUD):
            return Response(
                {"status": False, "message": "No tiene permisos para listar líneas de factura."},
                status=status.HTTP_403_FORBIDDEN
            )

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
