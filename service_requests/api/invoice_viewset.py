import logging
from decimal import Decimal
from django.apps import apps
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import AnonymousUser
import pytz
import requests
import base64
import os
import time
import threading
import json

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from users.authentication import JWTAuthentication

from parameterization.models import Statues
from service_requests.models import PaymentMethod
from ..models.invoice import Invoice
from ..models.invoice_line import InvoiceLine
from ..models.service_request import ServiceRequest
from ..serializers.invoice_serializers import (
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceDraftCreationSerializer,
    InvoiceLineSerializer
)
from ..utils.invoice_generator_utils import (
    generate_unique_reference_code,
    recalculate_invoice_totals,
    build_factus_payload
)
from core.services.factus_service import FactusService, FactusServiceError
from core.services.file_upload_service import upload_invoice_files_pair
from core.services.zip_service import ZipService

from core.services.file_upload_service import upload_invoice_pdf

# Auditoría
from audit_sdk import AuditClient
from service_requests.utils.audit_helpers import invoice_snapshot
from service_requests.utils.audit_helpers import get_actor_info  
import logging

logger = logging.getLogger(__name__)
COLOMBIA_TIMEZONE = pytz.timezone("America/Bogota")

PERM_INVOICE_LIST = 156 # request.list_invoices 156
PERM_INVOICE_RETRIEVE = 157 # request.view_invoice_detail 157
PERM_INVOICE_CREATE_EDIT = 158 # request.crud_invoice 158
PERM_INVOICE_LINES_CRUD = 159 # request.crud_invoice_lines 159
PERM_INVOICE_GENERATE = 160 # request.generate_invoice 160
PERM_INVOICE_DOWNLOAD = 161 # request.download_invoice 161

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestión de Facturas Electrónicas."""
    
    # Estados de factura
    BORRADOR = 24
    ENVIADA = 25
    VALIDADA = 26
    RECHAZADA = 27
    
    VALID_STATUS_TRANSITIONS = {
        BORRADOR: [ENVIADA],
        ENVIADA: [VALIDADA, RECHAZADA],
        VALIDADA: [],
        RECHAZADA: [BORRADOR]
    }
    
    queryset = Invoice.objects.all()
    lookup_field = 'id_invoice'
    
    def get_queryset(self):
        """Filtra por customer_id si se proporciona."""
        queryset = self.queryset
        customer_id = self.request.query_params.get('customer_id')
        
        if customer_id:
            try:
                queryset = queryset.filter(customer_id=int(customer_id))
            except ValueError:
                pass
        
        return queryset.order_by('-invoice_date')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        if self.action in ('create_draft', 'update_draft'):
            return InvoiceDraftCreationSerializer
        return InvoiceDetailSerializer
    
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
    
    def _transition_status(self, invoice, new_status_id: int, user=None):
        """Valida y ejecuta transición de estado."""
        current_status_id = invoice.status_id
        
        if new_status_id not in self.VALID_STATUS_TRANSITIONS.get(current_status_id, []):
            current_status = Statues.objects.get(pk=current_status_id).name
            new_status = Statues.objects.get(pk=new_status_id).name
            raise ValueError(f"Transición inválida de {current_status} a {new_status}")
        
        old_status = invoice.status
        invoice.status_id = new_status_id
        
        if new_status_id == self.ENVIADA:
            invoice.sent_at = timezone.now()
            invoice.save(update_fields=['status', 'sent_at'])
        else:
            invoice.save(update_fields=['status'])
        
        actor = self._get_actor_name(user)
        logger.info(f"Factura {invoice.id_invoice} cambió de {old_status} a {invoice.status} por {actor}")
        return True
    
    def _get_actor_name(self, user):
        """Extrae nombre del actor para auditoría."""
        if not user:
            return 'sistema'
        return (
            getattr(user, 'username', None) or
            getattr(user, 'email', None) or
            getattr(user, 'id', None) or
            'usuario'
        )
    
    def list(self, request, *args, **kwargs):
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"status": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not self.check_permission(request, PERM_INVOICE_LIST):
            return Response(
                {"status": False, "message": "No tiene permisos para listar facturas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().list(request)        
    
    def retrieve(self, request, pk=None, *args, **kwargs):
        """GET /invoices/{id}/"""
        if not self.check_permission(request, PERM_INVOICE_RETRIEVE):
            return Response(
                {"success": False, "message": "No tiene permisos para ver el detalle de la factura."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, pk, *args, **kwargs)
    
    def destroy(self, request, pk=None, *args, **kwargs):
        """DELETE /invoices/{id}/"""
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"status": False, "detail": "No tiene permisos para eliminar facturas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice_id = pk or kwargs.get('id_invoice')
        invoice = get_object_or_404(Invoice, id_invoice=invoice_id)
        
        allowed = [self.BORRADOR, self.RECHAZADA]
        if invoice.status_id not in allowed:
            return Response(
                {"status": False, "detail": "Solo se pueden eliminar facturas en estado BORRADOR o RECHAZADA."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reference = invoice.reference_code
        invoice.delete()
        logger.info(f"Factura {invoice_id} ({reference}) eliminada por {self._get_actor_name(request.user)}")
        
        return Response({
            "status": True,
            "reference_code": reference,
            "detail": "Factura eliminada exitosamente."
        }, status=status.HTTP_200_OK)
    
    # Endpoints personalizados

    @action(detail=False, methods=['get'], url_path='tributes-items')
    def tributes_items(self, request):
        """GET /invoices/tributes-items/ - Retorna solo los tributos IVA (id=1) e INC (id=4)."""
        # Permisos: mismo permiso que crear/editar factura
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"success": False, "message": "No tiene permisos para consultar tributos."},
                status=status.HTTP_403_FORBIDDEN
            )

        static_fallback = [
            {"id": 1, "code": "01", "name": "IVA", "description": "Impuesto sobre las Ventas"},
            {"id": 4, "code": "04", "name": "INC", "description": "Impuesto Nacional al Consumo"},
        ]

        try:
            factus = FactusService()
            tributes = factus._get_tributes()  # Lista completa desde Factus
            filtered = [t for t in tributes if int(t.get('id', 0)) in (1, 4)]

            def map_tribute(t):
                tid = int(t.get('id'))
                return {
                    "id": tid,
                    "code": t.get('code') or ("01" if tid == 1 else "04"),
                    "name": t.get('name') or ("IVA" if tid == 1 else "INC"),
                    "description": t.get('description') or (
                        "Impuesto sobre las Ventas" if tid == 1 else "Impuesto Nacional al Consumo"
                    ),
                }

            data = [map_tribute(t) for t in filtered]
            if not data:
                data = static_fallback

            return Response({"success": True, "tributes": data}, status=status.HTTP_200_OK)
        except FactusServiceError as e:
            logger.warning(f"Fallo consultando tributos en Factus, usando fallback: {e}")
            return Response({"success": True, "tributes": static_fallback}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error inesperado en tributes_iva_inc: {e}", exc_info=True)
            return Response({"success": False, "message": "Error interno al consultar tributos."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='debug-measurement-units')
    def debug_measurement_units(self, request):
        """GET /invoices/debug-measurement-units/ - [DEBUG] Lista todas las unidades de medida disponibles en Factus."""
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"success": False, "message": "No tiene permisos."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            factus = FactusService()
            units_data = factus._get_measurement_units()  # Obtiene el catálogo completo
            
            # Extraer solo IDs y nombres para facilitar búsqueda
            units_list = [
                {"id": item.get('id'), "name": item.get('name', 'N/A')}
                for item in units_data
            ]
            
            return Response({
                "success": True,
                "total": len(units_list),
                "environment": factus.BASE_URL,
                "units": units_list
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error obteniendo unidades de medida: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Error consultando Factus: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        static_fallback = [
            {"id": 1, "code": "01", "name": "IVA", "description": "Impuesto sobre las Ventas"},
            {"id": 4, "code": "04", "name": "INC", "description": "Impuesto Nacional al Consumo"},
        ]

        try:
            factus = FactusService()
            tributes = factus._get_tributes()  # Lista completa desde Factus
            filtered = [t for t in tributes if int(t.get('id', 0)) in (1, 4)]

            def map_tribute(t):
                tid = int(t.get('id'))
                return {
                    "id": tid,
                    "code": t.get('code') or ("01" if tid == 1 else "04"),
                    "name": t.get('name') or ("IVA" if tid == 1 else "INC"),
                    "description": t.get('description') or (
                        "Impuesto sobre las Ventas" if tid == 1 else "Impuesto Nacional al Consumo"
                    ),
                }

            data = [map_tribute(t) for t in filtered]
            if not data:
                data = static_fallback

            return Response({"success": True, "tributes": data}, status=status.HTTP_200_OK)
        except FactusServiceError as e:
            logger.warning(f"Fallo consultando tributos en Factus, usando fallback: {e}")
            return Response({"success": True, "tributes": static_fallback}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error inesperado en tributes_iva_inc: {e}", exc_info=True)
            return Response({"success": False, "message": "Error interno al consultar tributos."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='create-draft')
    def create_draft(self, request):
        """POST /invoices/create-draft/ - Crea borrador desde solicitud de servicio."""
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"success": False, "message": "No tiene permisos para crear borradores."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service_request_code = request.data.get('service_request')
        observation = request.data.get('observation', '')
        
        if len(observation) > 250:
            return Response(
                {"success": False, "message": "La observación no debe exceder 250 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        REQUIRED_STATUS_IDS = [20, 21, 22]
        if not service_request_code:
            return Response(
                {"success": False, "message": "El campo 'service_request' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service_request_obj = get_object_or_404(
                ServiceRequest.objects.select_related('request_status', 'customer__tax_regime'),
                id_request=service_request_code
            )
            
            if service_request_obj.request_status_id not in REQUIRED_STATUS_IDS:
                return Response(
                    {"success": False, "message": "Solo es posible crear factura para solicitudes en estado 'Pendiente', 'En proceso' o 'Finalizada'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if Invoice.objects.filter(service_request=service_request_obj).exclude(status_id=27).exists():
                return Response(
                    {"success": False, "message": f"Ya existe una factura en trámite para la solicitud '{service_request_code}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            customer_id = service_request_obj.customer_id
            tax_regime_id = service_request_obj.customer.tax_regime.pk if service_request_obj.customer.tax_regime else None
            
            if not customer_id or not tax_regime_id:
                return Response(
                    {"success": False, "message": "La solicitud no tiene Cliente o Régimen Fiscal asociado."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Http404:
            return Response(
                {"success": False, "message": f"Solicitud de Servicio '{service_request_code}' no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error en create_draft: {e}", exc_info=True)
            return Response(
                {"success": False, "message": "Error interno al procesar la solicitud."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        mutable_data = request.data.copy()
        mutable_data['customer'] = customer_id
        mutable_data['tax_regime'] = tax_regime_id
        
        if not mutable_data.get('payment_method'):
            efectivo = PaymentMethod.objects.filter(code='10').first()
            if efectivo:
                mutable_data['payment_method'] = efectivo.pk
        
        serializer = self.get_serializer(data=mutable_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save(
            reference_code=generate_unique_reference_code(),
            status_id=self.BORRADOR
        )
        
        return Response({
            'id_invoice': invoice.id_invoice,
            'reference_code': invoice.reference_code,
            'created_at': timezone.now().astimezone(COLOMBIA_TIMEZONE).isoformat(),
            'detail': 'Factura creada exitosamente.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put', 'patch'], url_path='update-draft')
    def update_draft(self, request, pk=None, *args, **kwargs):
        """PATCH /invoices/{id}/update-draft/ - Actualiza cabecera."""
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"success": False, "message": "No tiene permisos para actualizar borradores."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice_id = pk or kwargs.get("id_invoice")
        instance = get_object_or_404(Invoice, id_invoice=invoice_id, status_id=self.BORRADOR)
        
        allowed_fields = {"observation", "payment_method"}
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        if not update_data:
            return Response(
                {"success": False, "message": "No se proporcionaron campos válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fields_to_update = []
        for field, value in update_data.items():
            if field == "payment_method":
                # ForeignKey requiere usar payment_method_id para asignar directamente el ID
                if not PaymentMethod.objects.filter(pk=value).exists():
                    return Response(
                        {"success": False, "message": f"PaymentMethod con ID {value} no existe."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                instance.payment_method_id = value
                fields_to_update.append('payment_method')
            else:
                setattr(instance, field, value)
                fields_to_update.append(field)
        
        instance.save(update_fields=fields_to_update)
        
        return Response({
            "success": True,
            "detail": "Borrador actualizado con éxito.",
            "id_invoice": instance.id_invoice
        }, status=status.HTTP_200_OK)
    
    # Gestión de líneas (endpoints de conveniencia)
    
    @action(detail=True, methods=['post'], url_path='lines')
    def add_line(self, request, id_invoice=None):
        """POST /invoices/{id}/lines/ - Agrega línea a factura."""
        if not self.check_permission(request, PERM_INVOICE_LINES_CRUD):
            return Response(
                {"success": False, "message": "No tiene permisos para gestionar líneas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = get_object_or_404(Invoice, id_invoice=id_invoice)
        
        if invoice.status_id != self.BORRADOR:
            return Response(
                {"success": False, "message": "Solo se pueden modificar líneas en facturas BORRADOR."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        line_data = request.data.copy()
        if not line_data.get('units_measurement_id'):
            line_data['units_measurement_id'] = 70
        
        serializer = InvoiceLineSerializer(data=line_data)
        serializer.is_valid(raise_exception=True)
        
        service_item = serializer.validated_data.get('service_item')
        if service_item and InvoiceLine.objects.filter(invoice=invoice, service_item_id=service_item.pk).exists():
            return Response(
                {"success": False, "message": "Este servicio ya existe en la factura."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        line = serializer.save(invoice=invoice)
        
        try:
            recalculate_invoice_totals(invoice)
        except Exception:
            logger.exception("Error recalculando totales tras agregar línea")
        
        line_serialized = InvoiceLineSerializer(line).data
        line_serialized.pop('factus_payload', None)
        
        return Response({
            'success': True,
            'detail': 'Línea agregada con éxito.',
            'line': line_serialized,
            'id_invoice': invoice.id_invoice
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['put', 'patch', 'delete'], url_path='lines/(?P<line_id>[^/.]+)')
    def update_line(self, request, id_invoice=None, line_id=None):
        """PUT/PATCH/DELETE /invoices/{id}/lines/{line_id}/"""
        if not self.check_permission(request, PERM_INVOICE_LINES_CRUD):
            return Response(
                {"success": False, "message": "No tiene permisos para gestionar líneas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = get_object_or_404(Invoice, id_invoice=id_invoice)
        
        if invoice.status_id != self.BORRADOR:
            return Response(
                {"success": False, "message": "Solo se pueden modificar líneas en facturas BORRADOR."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            line = InvoiceLine.objects.get(id_invoice_line=line_id, invoice=invoice)
        except InvoiceLine.DoesNotExist:
            return Response(
                {"success": False, "message": "Línea no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'DELETE':
            line.delete()
            try:
                recalculate_invoice_totals(invoice)
            except Exception:
                logger.exception("Error recalculando totales tras eliminar línea")
            
            return Response({
                'success': True,
                'detail': 'Línea eliminada con éxito.',
                'id_invoice': invoice.id_invoice
            }, status=status.HTTP_200_OK)
        
        # PUT/PATCH con validación centralizada en el serializer
        allowed = {'quantity', 'units_measurement_id', 'percentage_taxes_per_line', 'discount_percentage', 'tribute_id'}
        update_data = {k: v for k, v in request.data.items() if k in allowed}

        if not update_data:
            return Response(
                {"success": False, "message": "No se proporcionaron campos válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvoiceLineSerializer(instance=line, data=update_data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        line = serializer.save()
        
        try:
            recalculate_invoice_totals(invoice)
        except Exception:
            logger.exception("Error recalculando totales tras actualizar línea")
        
        line_serialized = InvoiceLineSerializer(line).data
        line_serialized.pop('factus_payload', None)
        
        return Response({
            'success': True,
            'detail': 'Línea actualizada con éxito.',
            'line': line_serialized,
            'id_invoice': invoice.id_invoice
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='final-charges')
    def final_charges(self, request, id_invoice=None):
        """POST /invoices/{id}/final-charges/ - Aplica recargos globales."""
        if not self.check_permission(request, PERM_INVOICE_CREATE_EDIT):
            return Response(
                {"success": False, "message": "No tiene permisos para aplicar cargos finales."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = get_object_or_404(Invoice, id_invoice=id_invoice)
        
        if invoice.status_id != self.BORRADOR:
            return Response(
                {"success": False, "message": "Solo permito para facturas sin validación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not invoice.lines.exists():
            return Response(
                {"success": False, "message": "La factura no tiene líneas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payload_list = request.data.get('allowance_charges') or []
        if not isinstance(payload_list, (list, tuple)):
            return Response(
                {"success": False, "message": "allowance_charges debe ser una lista."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recalculate_invoice_totals(invoice)
        base_imponible = Decimal(invoice.total_without_taxes or 0)
        processed = []
        allowance_total = Decimal('0.00')
        
        for idx, item in enumerate(payload_list):
            reason = item.get('reason')
            amount_raw = item.get('amount')
            
            if not reason or not isinstance(reason, str):
                return Response(
                    {"success": False, "message": f"Elemento #{idx+1}: 'reason' requerido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                amount = Decimal(str(amount_raw))
            except:
                return Response(
                    {"success": False, "message": f"Elemento #{idx+1}: 'amount' debe ser numérico."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if amount <= 0 or amount > base_imponible:
                return Response(
                    {"success": False, "message": f"Elemento #{idx+1}: amount inválido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            allowance_total += amount
            processed.append({
                "concept_type": "03",
                "is_surcharge": True,
                "reason": reason,
                "base_amount": f"{base_imponible:.2f}",
                "amount": f"{amount:.2f}"
            })
        
        amount_before = Decimal(invoice.total_without_taxes or 0) + Decimal(invoice.total_taxes or 0) - Decimal(invoice.total_withholding_taxes or 0)
        invoice.amount_to_pay = (amount_before + allowance_total).quantize(Decimal('0.01'))
        
        api_resp = invoice.api_response or {}
        api_resp['allowance_charges'] = processed
        api_resp['allowance_total'] = f"{allowance_total:.2f}"
        invoice.api_response = api_resp
        invoice.save(update_fields=['amount_to_pay', 'api_response'])
        
        if invoice.service_request_id:
            ServiceRequest.objects.filter(pk=invoice.service_request_id).update(amount_to_pay=float(invoice.amount_to_pay))
        
        return Response({
            "success": True,
            "detail": "Cargos aplicados correctamente.",
            "allowance_charges": processed,
            "allowance_total": f"{allowance_total:.2f}",
            "amount_to_pay": f"{invoice.amount_to_pay:.2f}"
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def generate_fe(self, request, id_invoice=None):
        """POST /invoices/{id}/generate_fe/ - Genera factura electrónica."""
        if not self.check_permission(request, PERM_INVOICE_GENERATE):
            return Response(
                {"success": False, "message": "No tiene permisos para generar facturas FE."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = get_object_or_404(Invoice, id_invoice=id_invoice, status_id=self.BORRADOR)
        
        if not invoice.service_request:
            return Response(
                {'detail': 'Debe asociarse a una Solicitud de Servicio.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                recalculate_invoice_totals(invoice)
                
                # LIMPIEZA PREVENTIVA (GLOBAL CUENTA): eliminar última factura status=0 del cliente API
                try:
                    factus_service = FactusService()
                    acc_cleanup = factus_service.cleanup_last_pending_for_account()
                    if acc_cleanup.get('found'):
                        if acc_cleanup.get('deleted'):
                            logger.info(f"[GENERATE_FE] Limpiada factura status=0 previa: ref={acc_cleanup.get('reference_code')} id={acc_cleanup.get('bill_id')}")
                        else:
                            logger.warning(f"[GENERATE_FE] Pendiente no eliminada: {acc_cleanup.get('message')}")
                    
                    # LIMPIEZA ESPECÍFICA POR reference_code (por si acaso)
                    cleanup_result = factus_service.check_and_cleanup_rejected_invoice(invoice.reference_code)
                    
                    if cleanup_result.get('had_rejected'):
                        if cleanup_result.get('deleted'):
                            logger.info(f"[GENERATE_FE] Factura rechazada previa eliminada: {invoice.reference_code}")
                            logger.info(f"[GENERATE_FE] Errores previos: {cleanup_result.get('errors')}")
                        else:
                            logger.warning(f"[GENERATE_FE] No se pudo eliminar factura rechazada: {cleanup_result.get('message')}")
                    else:
                        logger.info(f"[GENERATE_FE] No hay facturas rechazadas previas, procediendo con generación")
                        
                except Exception as e:
                    # No bloquear el flujo si la limpieza falla por cualquier motivo (incluye atributos faltantes)
                    logger.error(f"[GENERATE_FE] Error en limpieza preventiva: {e}", exc_info=True)
                    # No bloquear el flujo si la limpieza falla, continuar con la generación
                
                invoice_payload = build_factus_payload(invoice, request=request)
                factus_response = factus_service.generate_invoice(invoice_payload)
                
                logger.info(f"Respuesta Factus para factura {invoice.id_invoice}: {factus_response}")
                
                bill_data = factus_response.get('data', {}).get('bill', {})
                
                if not bill_data.get('cufe') and not bill_data.get('number'):
                    logger.error(f"Respuesta Factus incompleta: {factus_response}")
                    return Response(
                        {'detail': 'Error en respuesta de Factus: sin CUFE ni número.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                invoice.cufe = bill_data.get('cufe')
                invoice.invoice_number = bill_data.get('number')
                invoice.api_response = factus_response
                
                # Sincronizar amount_to_pay con el total de Factus (incluye allowance_charges)
                factus_total = bill_data.get('total')
                if factus_total:
                    try:
                        invoice.amount_to_pay = Decimal(str(factus_total))
                        logger.info(f"amount_to_pay sincronizado con Factus: {invoice.amount_to_pay}")
                        
                        # Actualizar también el ServiceRequest asociado
                        if invoice.service_request_id:
                            ServiceRequest.objects.filter(pk=invoice.service_request_id).update(
                                amount_to_pay=float(invoice.amount_to_pay)
                            )
                            logger.info(f"ServiceRequest {invoice.service_request_id} actualizado con amount_to_pay: {invoice.amount_to_pay}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"No se pudo convertir total de Factus a Decimal: {factus_total}, error: {e}")
                
                if invoice.cufe and invoice.invoice_number:
                    if invoice.status_id == self.BORRADOR:
                        self._transition_status(invoice, self.ENVIADA, request.user)
                    self._transition_status(invoice, self.VALIDADA, request.user)
                else:
                    self._transition_status(invoice, self.ENVIADA, request.user)
                
                invoice.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(invoice.id_invoice),
                        after=invoice_snapshot(invoice),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=PERM_INVOICE_GENERATE,
                        module="requests",
                        submodule="invoice_generate_fe",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en generate_fe: %s", e)

                # Descargar y subir archivos + enviar email automáticamente
                self._handle_invoice_files(invoice, request)
                
                return Response({
                    'detail': 'Factura generada y enviada con éxito.',
                    'id_invoice': invoice.id_invoice,
                    'invoice_pdf_url': invoice.invoice_pdf_url,
                    'invoice_xml_url': invoice.invoice_xml_url
                }, status=status.HTTP_201_CREATED)
                
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except FactusServiceError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error generando factura {id_invoice}: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno del servidor.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_invoice_files(self, invoice, request=None):
        """Descarga archivos de Factus y sube a Firebase."""
        time.sleep(2)
        
        if not invoice.invoice_number and not invoice.cufe:
            logger.error(f"Factura {invoice.id_invoice} sin número ni CUFE")
            return
        
        try:
            key = invoice.invoice_number or invoice.cufe
            
            if invoice.invoice_number:
                pdf_data, _ = FactusService().get_invoice_pdf_by_number(invoice.invoice_number)
                try:
                    xml_data, _ = FactusService().get_invoice_xml_by_number(invoice.invoice_number)
                except FactusServiceError:
                    logger.warning(f"XML no disponible para factura {invoice.invoice_number}")
                    xml_data = None
            else:
                pdf_data, _ = FactusService().get_invoice_pdf(invoice.cufe)
                xml_data = None
            
            if not pdf_data:
                raise ValueError("PDF vacío")
            
            if xml_data:
                pdf_url, xml_url = upload_invoice_files_pair(
                    pdf_data=pdf_data,
                    xml_data=xml_data,
                    invoice_number=key,
                    reference_code=invoice.reference_code
                )
                invoice.invoice_pdf_url = pdf_url
                invoice.invoice_xml_url = xml_url
                invoice.save(update_fields=['invoice_pdf_url', 'invoice_xml_url'])
            else:
                pdf_url = upload_invoice_pdf(
                    pdf_data=pdf_data,
                    invoice_number=key,
                    reference_code=invoice.reference_code
                )
                invoice.invoice_pdf_url = pdf_url
                invoice.save(update_fields=['invoice_pdf_url'])
            
            logger.info(f"Archivos subidos para factura {invoice.id_invoice}")
            
            # Enviar email automáticamente después de subir archivos
            if request and invoice.status_id == self.VALIDADA:
                auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION')
                if not auth_header and hasattr(request, 'headers'):
                    auth_header = request.headers.get('Authorization')
                
                logger.info(f"[AUTO-SEND] Iniciando envío automático de email para factura {invoice.invoice_number}")
                self._send_email_async(invoice, auth_header)
            
        except Exception as e:
            logger.error(f"Error procesando archivos de factura {invoice.id_invoice}: {e}", exc_info=True)
    
    def _send_email_async(self, invoice, auth_header=None):
        """Envía el correo electrónico de forma asíncrona en un thread separado."""
        def send_email_task():
            try:
                logger.info(f"[AUTO-SEND] Thread iniciado para factura {invoice.invoice_number}")
                
                # Validar que la factura tenga cliente y email
                if not invoice.customer:
                    logger.warning(f"[AUTO-SEND] Factura {invoice.invoice_number} sin cliente asociado")
                    return
                
                if not invoice.customer.email:
                    logger.warning(f"[AUTO-SEND] Cliente de factura {invoice.invoice_number} sin email")
                    return
                
                # Validar que existan PDF y XML
                if not invoice.invoice_pdf_url or not invoice.invoice_xml_url:
                    logger.warning(f"[AUTO-SEND] Factura {invoice.invoice_number} sin archivos completos")
                    return
                
                # Crear ZIP
                logger.info(f"[AUTO-SEND] Creando ZIP para factura {invoice.invoice_number}")
                zip_bytes, zip_filename = ZipService.create_invoice_zip_in_memory(
                    pdf_url=invoice.invoice_pdf_url,
                    xml_url=invoice.invoice_xml_url,
                    invoice_number=invoice.invoice_number,
                    reference_code=invoice.reference_code
                )
                
                customer = invoice.customer
                client_name = f"{customer.name or ''} {customer.first_last_name or ''}".strip()
                if not client_name:
                    client_name = "Cliente"
                
                total_formatted = f"${invoice.amount_to_pay:,.0f} COP".replace(",", ".")
                invoice_date = invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else "N/A"
                
                auth_service_url = os.getenv('AUTH_SERVICE_URL')
                if not auth_service_url:
                    logger.error("[AUTO-SEND] AUTH_SERVICE_URL no configurado")
                    return
                
                zip_base64 = base64.b64encode(zip_bytes).decode('utf-8')
                url = f"{auth_service_url.rstrip('/')}/users/users/send-invoice-zip/"
                
                payload = {
                    "email": customer.email,
                    "client_name": client_name,
                    "invoice_number": invoice.invoice_number,
                    "invoice_date": invoice_date,
                    "total_amount": total_formatted,
                    "zip_base64": zip_base64,
                    "zip_filename": zip_filename,
                    "cufe": invoice.cufe if hasattr(invoice, 'cufe') else None
                }
                
                headers = {'Content-Type': 'application/json'}
                if auth_header:
                    headers['Authorization'] = auth_header
                    logger.info(f"[AUTO-SEND] Token propagado: {auth_header[:20]}...")
                
                logger.info(f"[AUTO-SEND] Enviando email a {customer.email}")
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                
                logger.info(f"[AUTO-SEND] Status: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"[AUTO-SEND] ✓ Email enviado exitosamente a {customer.email}")
                else:
                    logger.error(f"[AUTO-SEND] ✗ Error enviando email: {response.text[:200]}")
                    
            except Exception as e:
                logger.error(f"[AUTO-SEND] ✗ Excepción en envío automático: {e}", exc_info=True)
        
        # Crear y ejecutar thread daemon
        email_thread = threading.Thread(target=send_email_task, daemon=True)
        email_thread.start()
        logger.info(f"[AUTO-SEND] Thread lanzado para factura {invoice.invoice_number}")
    
    @action(detail=True, methods=['post'], url_path='send-by-email')
    def send_by_email(self, request, id_invoice=None):
        invoice = get_object_or_404(Invoice, id_invoice=id_invoice)
        
        # 1. Validar estado 
        if invoice.status_id != self.VALIDADA:
            return Response({
                'success': False,
                'message': 'Solo se pueden enviar por email facturas en estado VALIDADA.',
                'errors': {'status': ['La factura debe estar validada para ser enviada.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validar cliente y email
        if not invoice.customer:
            return Response({
                'success': False,
                'message': 'La factura no tiene un cliente asociado.',
                'errors': {'customer': ['Se requiere un cliente para enviar la factura.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not invoice.customer.email:
            return Response({
                'success': False,
                'message': 'El cliente no tiene correo electrónico registrado.',
                'errors': {'email': ['El cliente debe tener un email válido.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Validar existencia de PDF y XML en Firebase
        if not invoice.invoice_pdf_url:
            return Response({
                'success': False,
                'message': 'La factura no tiene PDF disponible.',
                'errors': {'pdf': ['No se encontró el archivo PDF de la factura.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not invoice.invoice_xml_url:
            return Response({
                'success': False,
                'message': 'La factura no tiene XML disponible.',
                'errors': {'xml': ['No se encontró el archivo XML de la factura.']}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info(f"[SEND EMAIL] Creando ZIP temporal para factura {invoice.invoice_number}")
            
            zip_bytes, zip_filename = ZipService.create_invoice_zip_in_memory(
                pdf_url=invoice.invoice_pdf_url,
                xml_url=invoice.invoice_xml_url,
                invoice_number=invoice.invoice_number,
                reference_code=invoice.reference_code
            )
            
            zip_size_mb = ZipService.get_zip_size_mb(zip_bytes)
            logger.info(f"[SEND EMAIL] ZIP creado: {zip_filename} ({zip_size_mb} MB)")
            
            customer = invoice.customer
            
            client_name = f"{customer.name or ''} {customer.first_last_name or ''}".strip()
            if not client_name:
                client_name = "Cliente"
            
            total_formatted = f"${invoice.amount_to_pay:,.0f} COP".replace(",", ".")
            
            invoice_date = invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else "N/A"
            
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            logger.info(f"[SEND EMAIL] AUTH_SERVICE_URL desde .env: '{auth_service_url}'")
            
            if not auth_service_url:
                logger.error("[SEND EMAIL] AUTH_SERVICE_URL no configurado")
                return Response({
                    'success': False,
                    'message': 'Servicio de email no disponible.',
                    'errors': {'config': ['Configuración del servicio de email no encontrada.']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            logger.info("[SEND EMAIL] Codificando ZIP a base64...")
            zip_base64 = base64.b64encode(zip_bytes).decode('utf-8')
            logger.info(f"[SEND EMAIL] ZIP base64 generado - Longitud: {len(zip_base64)} caracteres")
            
            url = f"{auth_service_url.rstrip('/')}/users/users/send-invoice-zip/"
            logger.info(f"[SEND EMAIL] URL COMPLETA construida: '{url}'")
            
            payload = {
                "email": customer.email,
                "client_name": client_name,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice_date,
                "total_amount": total_formatted,
                "zip_base64": zip_base64,
                "zip_filename": zip_filename,
                "cufe": invoice.cufe if hasattr(invoice, 'cufe') else None
            }
            
            headers = {'Content-Type': 'application/json'}
            
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION')
            if not auth_header and hasattr(request, 'headers'):
                auth_header = request.headers.get('Authorization')
            
            if auth_header:
                headers['Authorization'] = auth_header
                logger.info(f"[SEND EMAIL] Token de autorización propagado: {auth_header[:20]}...")
            else:
                logger.warning("[SEND EMAIL] No se encontró token de autorización para propagar")
            
            logger.info(f"[SEND EMAIL] Headers preparados: {list(headers.keys())}")
            
            logger.info(f"[SEND EMAIL] === INICIANDO PETICIÓN HTTP ===")
            logger.info(f"[SEND EMAIL] Método: POST")
            logger.info(f"[SEND EMAIL] URL: {url}")
            logger.info(f"[SEND EMAIL] Factura: {invoice.invoice_number}")
            logger.info(f"[SEND EMAIL] Destinatario: {customer.email}")
            logger.info(f"[SEND EMAIL] Payload keys: {list(payload.keys())}")
            logger.info(f"[SEND EMAIL] ZIP filename: {zip_filename}")
            logger.info(f"[SEND EMAIL] === ENVIANDO... ===")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=60
            )
            
            logger.info(f"[SEND EMAIL] === RESPUESTA RECIBIDA ===")
            logger.info(f"[SEND EMAIL] Status Code: {response.status_code}")
            logger.info(f"[SEND EMAIL] Headers de respuesta: {dict(response.headers)}")
            logger.info(f"[SEND EMAIL] Cuerpo de respuesta: {response.text[:500]}")
            logger.info(f"[SEND EMAIL] === FIN RESPUESTA ===")
            
            # --- 8. Procesar respuesta ---
            if response.status_code == 200:
                logger.info(f"[SEND EMAIL] ✓ Factura enviada exitosamente a {customer.email}")
                
                return Response({
                    'success': True,
                    'message': f'Factura enviada exitosamente a {customer.email}',
                    'data': {
                        'zip_size_mb': zip_size_mb,
                        'email': customer.email,
                        'invoice_number': invoice.invoice_number,
                        'zip_filename': zip_filename
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"[SEND EMAIL] Error del servicio de email: {response.status_code}")
                logger.error(f"[SEND EMAIL] Respuesta: {response.text}")
                
                return Response({
                    'success': False,
                    'message': 'Error al enviar el correo electrónico',
                    'errors': {
                        'email_service': [f'Código de error: {response.status_code}', response.text[:200]]
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"[SEND EMAIL] Error inesperado: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error interno al procesar el envío',
                'errors': {'detail': [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["GET"])
def download_invoice_pdf(request, id_invoice):
    """GET /invoices/{id}/download_pdf/ - Descarga PDF de factura."""    
    jwt_auth = JWTAuthentication()
    try:
        user_data = jwt_auth.authenticate(request)
        if user_data:
            user, payload = user_data
            request.user = user
            request.auth = payload
    except Exception as e:
        return HttpResponse(
            '{"status": false, "detail": "Usuario no autenticado"}',
            content_type='application/json',
            status=401
        )
    
    if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
        return HttpResponse(
            '{"status": false, "detail": "Usuario no autenticado"}',
            content_type='application/json',
            status=401
        )
    
    payload = getattr(request, "auth", None) or {}
    user_roles = payload.get("rol") or payload.get("roles") or []
    permisos_usuario = []
    
    for rol in user_roles:
        perms = rol.get("permisos") or rol.get("permissions") or []
        for perm in perms:
            if isinstance(perm, dict) and "id" in perm:
                permisos_usuario.append(perm.get("id"))
    
    if PERM_INVOICE_DOWNLOAD not in permisos_usuario:
        return HttpResponse(
            '{"status": false, "detail": "No tiene permisos para descargar facturas."}',
            content_type='application/json',
            status=403
        )
    
    try:
        invoice = Invoice.objects.get(id_invoice=id_invoice)
    except Invoice.DoesNotExist:
        return HttpResponse(
            '{"status": false, "detail": "Factura no encontrada."}',
            content_type='application/json',
            status=404
        )
    
    if invoice.status_id not in [25, 26]:
        return HttpResponse(
            '{"status": false, "detail": "Factura no lista para descarga."}',
            content_type='application/json',
            status=400
        )
    
    try:
        filename = f"factura_{invoice.reference_code}.pdf"
        
        if invoice.invoice_pdf_url:
            logger.info(f"Descargando PDF desde Firebase: {invoice.invoice_pdf_url}")
            resp = requests.get(invoice.invoice_pdf_url, timeout=30)
            resp.raise_for_status()
            pdf_data = resp.content
        elif invoice.cufe:
            logger.info(f"Descargando PDF desde Factus: {invoice.cufe}")
            pdf_data, filename = FactusService().get_invoice_pdf(invoice.cufe)
        else:
            return HttpResponse(
                '{"status": false, "detail": "No hay PDF disponible."}',
                content_type='application/json',
                status=404
            )
        
        if not pdf_data:
            raise ValueError("PDF vacío")
        
        # Auditoría
        try:
            actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

            AuditClient(request).create(
                object_id=str(invoice.id_invoice),
                after=invoice_snapshot(invoice),
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                permission_id=PERM_INVOICE_DOWNLOAD,
                module="requests",
                submodule="download_invoice_pdf",
            )
            logger.info(f"Auditoría registrada para descarga de factura {invoice.id_invoice}")
        except Exception as e:
            logger.warning("El servicio de auditoría ha fallado en download_invoice_pdf: %s", e)
        
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_data)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
        
    except requests.RequestException as e:
        logger.error(f"Error descarga Firebase: {e}", exc_info=True)
        return HttpResponse(
            '{"status": false, "detail": "Error al descargar desde almacenamiento."}',
            content_type='application/json',
            status=502
        )
    except Exception as e:
        logger.error(f"Error descarga PDF {id_invoice}: {e}", exc_info=True)
        return HttpResponse(
            '{"status": false, "detail": "Error interno."}',
            content_type='application/json',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
def consult_sigma_economic_events(request, sincePeriod, untilPeriod):
    """
    GET /sigma/economic-events/consult/{sincePeriod}/{untilPeriod}/

    Endpoint protegido por JWT para obtener eventos económicos de SIGMA
    y construir un lote AAEF con facturas y pagos/transacciones.

    Ejemplo:
    /sigma/economic-events/consult/2026-03-01/2026-03-31/
    """

    def json_response(data, http_status=200):
        return HttpResponse(
            json.dumps(data, ensure_ascii=False, default=str),
            content_type="application/json",
            status=http_status
        )

    def get_nested_value(source, path, default=None):
        current = source or {}

        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and isinstance(key, int):
                if 0 <= key < len(current):
                    current = current[key]
                else:
                    return default
            else:
                return default

            if current is None:
                return default

        return current

    def to_decimal(value, default="0.00"):
        try:
            if value is None or value == "":
                return Decimal(default)
            return Decimal(str(value))
        except Exception:
            return Decimal(default)

    def format_decimal(value):
        try:
            return str(to_decimal(value).quantize(Decimal("0.01")))
        except Exception:
            return "0.00"

    def get_customer_display_name(customer):
        if not customer:
            return ""

        legal_name = getattr(customer, "legal_entity_name", None)
        if legal_name:
            return legal_name

        name_parts = [
            getattr(customer, "name", None),
            getattr(customer, "first_last_name", None),
            getattr(customer, "second_last_name", None),
        ]

        return " ".join([str(x).strip() for x in name_parts if x]).strip()

    def get_customer_document_number(customer):
        if not customer:
            return ""

        return (
            getattr(customer, "document_number", None)
            or getattr(customer, "identification_number", None)
            or getattr(customer, "nit", None)
            or ""
        )

    def get_customer_document_type(customer):
        if not customer:
            return ""

        type_document = getattr(customer, "type_document", None)
        if type_document:
            return (
                getattr(type_document, "code", None)
                or getattr(type_document, "name", None)
                or str(type_document)
            )

        type_document_id = getattr(customer, "type_document_id_id", None)
        if type_document_id:
            return str(type_document_id)

        return ""

    def get_payment_method_code(payment_method_id):
        mapping = {
            "10": "CASH",
            "20": "CHECK",
            "47": "TRANSFER",
            "48": "CARD",
            "49": "CARD",
        }

        if payment_method_id is None:
            return "PENDING"

        return mapping.get(str(payment_method_id).strip(), "PENDING")

    def get_invoice_status_aaef(invoice):
        if getattr(invoice, "status_id", None) == 26:
            return "PAID"

        if getattr(invoice, "status_id", None) == 24:
            return "EASER"

        return "PENDING"

    def get_service_accounting_account(model_line):
        """
        Obtiene la cuenta contable del concepto facturado desde:

        InvoiceLine.service_item -> Service.accounting_account
        """
        if not model_line:
            return ""

        service_item = getattr(model_line, "service_item", None)

        if not service_item:
            return ""

        accounting_account = getattr(service_item, "accounting_account", None)

        if accounting_account is None:
            return ""

        return str(accounting_account).strip()

    def get_invoice_lines_aaef(invoice):
        result = []

        api_response = getattr(invoice, "api_response", None) or {}
        api_items = get_nested_value(api_response, ["data", "items"], []) or []

        try:
            model_lines = list(invoice.lines.all())
        except Exception:
            model_lines = []

        max_len = max(len(model_lines), len(api_items))

        for index in range(max_len):
            model_line = model_lines[index] if index < len(model_lines) else None
            api_item = api_items[index] if index < len(api_items) else {}

            code = ""
            name = "Concepto facturado"
            quantity = 1
            unit_price = None

            # RF-INT-15:
            # Lines.AccountingAccount[0]
            # Sale de services.accounting_account del concepto consultado.
            accounting_account = get_service_accounting_account(model_line)

            if model_line:
                code = getattr(model_line, "code_reference", None) or ""
                name = getattr(model_line, "service_name", None) or name
                quantity = getattr(model_line, "quantity", None) or quantity
                unit_price = (
                    getattr(model_line, "price_unit", None)
                    or getattr(model_line, "unit_price", None)
                )

            code = code or api_item.get("code_reference") or api_item.get("code") or ""
            name = api_item.get("name") or api_item.get("description") or name
            description = api_item.get("note") or api_item.get("description") or name
            quantity = api_item.get("quantity") or quantity

            if unit_price is None:
                unit_price = api_item.get("price") or api_item.get("unit_price") or 0

            line_value = (
                api_item.get("total")
                or api_item.get("value")
                or to_decimal(quantity) * to_decimal(unit_price)
            )

            tax_type = get_nested_value(api_item, ["tribute", "code"], None)
            tax_rate = api_item.get("tax_rate")
            tax_amount = api_item.get("tax_amount")

            taxes = []

            if tax_type or tax_rate or tax_amount:
                taxes.append({
                    "TaxType": tax_type or "01",
                    "Rate": format_decimal(tax_rate or 0),
                    "Amount": format_decimal(tax_amount or 0)
                })

            result.append({
                "Code": str(code),
                "Name": str(name),
                "Description": str(description),
                "LineType": str(name),

                "AccountingAccount": [
                    accounting_account
                ],

                "Quantity": format_decimal(quantity),
                "UnitPrice": format_decimal(unit_price),
                "Value": format_decimal(line_value),
                "Taxes": taxes
            })

        return result

    def build_invoice_aaef(invoice):
        api_response = getattr(invoice, "api_response", None) or {}
        bill = get_nested_value(api_response, ["data", "bill"], {}) or {}

        customer = getattr(invoice, "customer", None)

        reference_code = getattr(invoice, "reference_code", None) or ""
        invoice_number = getattr(invoice, "invoice_number", None) or ""

        validated_at = (
            bill.get("validated")
            or bill.get("validated_at")
            or getattr(invoice, "sent_at", None)
            or getattr(invoice, "invoice_date", None)
        )

        issue_date = (
            bill.get("created_at")
            or getattr(invoice, "invoice_date", None)
        )

        subtotal = (
            bill.get("taxable_amount")
            or getattr(invoice, "total_without_taxes", None)
            or 0
        )

        total_vat = (
            bill.get("tax_amount")
            or getattr(invoice, "total_taxes", None)
            or 0
        )

        total_discounts = bill.get("discount_amount") or 0

        total_payment = (
            getattr(invoice, "amount_to_pay", None)
            or bill.get("total")
            or 0
        )

        return {
            "Header": {                
                "DocumentId": reference_code,
                "Prefix": "SIGMA-FACT",
                "Serial": invoice_number or reference_code,
                "Type": {
                    "Code": get_nested_value(
                        api_response,
                        ["data", "bill", "document", "code"],
                        "INVOICE"
                    ),
                    "Name": "Factura de Venta"
                },
                "IssueDate": issue_date,
                "DueDate": validated_at,
                "Status": get_invoice_status_aaef(invoice),
                "UpdatedAt": validated_at
            },
            "ThirdParty": {
                "DocumentType": get_customer_document_type(customer),
                "DocumentNumber": get_customer_document_number(customer),
                "NIT": None,
                "Name": get_customer_display_name(customer),
                "Email": getattr(customer, "email", None) if customer else "",
                "Address": getattr(customer, "address", None) if customer else ""
            },
            "Totals": {
                "Subtotal": format_decimal(subtotal),
                "TotalVAT": format_decimal(total_vat),
                "TotalWithholdings": format_decimal(
                    getattr(invoice, "total_withholding_taxes", 0) or 0
                ),
                "TotalDiscounts": format_decimal(total_discounts),
                "TotalPayment": format_decimal(total_payment),
                "OutstandingBalance": format_decimal(
                    getattr(invoice, "amount_to_pay", 0) or 0
                )
            },
            "Lines": get_invoice_lines_aaef(invoice)
        }

    def build_transaction_aaef(invoice):
        api_response = getattr(invoice, "api_response", None) or {}
        bill = get_nested_value(api_response, ["data", "bill"], {}) or {}

        customer = getattr(invoice, "customer", None)
        service_request = getattr(invoice, "service_request", None)

        reference_code = getattr(invoice, "reference_code", None) or ""

        validated_at = (
            bill.get("validated")
            or bill.get("validated_at")
            or getattr(invoice, "sent_at", None)
            or getattr(invoice, "invoice_date", None)
        )

        if validated_at:
            validated_date = str(validated_at)[0:10]
        else:
            validated_date = timezone.now().date().isoformat()

        payment_method_id = None

        if service_request:
            payment_method_id = getattr(service_request, "payment_method_id", None)

        if payment_method_id is None:
            payment_method = getattr(invoice, "payment_method", None)
            payment_method_id = (
                getattr(payment_method, "code", None)
                or getattr(invoice, "payment_method_id", None)
            )

        return {             
            "DocumentId": f"PAY-{reference_code}-{validated_date}",
            "Date": validated_at,
            "RelatedInvoiceId": reference_code,
            "ThirdParty": {
                "DocumentType": get_customer_document_type(customer),
                "DocumentNumber": get_customer_document_number(customer),
                "Name": get_customer_display_name(customer)
            },
            "Amount": format_decimal(getattr(invoice, "amount_to_pay", 0) or 0),
            "Currency": "COP",
            "Status": "COMPLETED",
            "Notes": f"Pago asociado a factura {reference_code}",
            "UpdatedAt": (
                getattr(service_request, "confirmation_datetime", None)
                if service_request
                else validated_at
            ),
            "Type": {
                "Code": "PAY",
                "Name": "Pago de Factura",
            },
            "PaymentMethod": {
                "Code": get_payment_method_code(payment_method_id)
            }
        }

    # 1. Autenticación JWT.
    # No se valida permiso específico por solicitud funcional.
    jwt_auth = JWTAuthentication()

    try:
        user_data = jwt_auth.authenticate(request)

        if user_data:
            user, payload = user_data
            request.user = user
            request.auth = payload

    except Exception as e:
        logger.warning("[SIGMA_EVENTS] Usuario no autenticado: %s", e)

        return json_response({
            "success": False,
            "message": "Usuario no autenticado."
        }, 401)

    if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
        return json_response({
            "success": False,
            "message": "Usuario no autenticado."
        }, 401)

    # 2. Tomar fechas desde la URL.
    since_period = sincePeriod
    until_period = untilPeriod

    if not since_period or not until_period:
        return json_response({
            "success": False,
            "message": "Los parámetros sincePeriod y untilPeriod son obligatorios."
        }, 400)

    # 3. Validar formato básico de fechas.
    try:
        from datetime import datetime

        since_date = datetime.strptime(str(since_period), "%Y-%m-%d").date()
        until_date = datetime.strptime(str(until_period), "%Y-%m-%d").date()
    except Exception:
        return json_response({
            "success": False,
            "message": "Los parámetros sincePeriod y untilPeriod deben tener formato YYYY-MM-DD."
        }, 400)

    if since_date > until_date:
        return json_response({
            "success": False,
            "message": "sincePeriod no puede ser mayor que untilPeriod."
        }, 400)

    try:
        # 4. Consultar facturas validadas en el rango.
        # Se usa invoice_date como filtro operativo inicial.
        invoices_queryset = (
            Invoice.objects
            .select_related("customer", "payment_method", "service_request")
            .prefetch_related("lines__service_item")
            .filter(
                status_id=26,
                invoice_date__gte=since_date,
                invoice_date__lte=until_date
            )
            .order_by("invoice_date", "id_invoice")
        )

        invoices = list(invoices_queryset)

        # 5. Construir invoices y transactions AAEF.
        aaef_invoices = []
        aaef_transactions = []

        for invoice in invoices:
            aaef_invoices.append(build_invoice_aaef(invoice))

            service_request = getattr(invoice, "service_request", None)
            payment_status_id = (
                getattr(service_request, "payment_status_id", None)
                if service_request
                else None
            )

            # Según criterios de aceptación RF-INT-15:
            # payment_status_id = 18 => COMPLETED.
            # payment_status_id = 16 o 17 => excluido.
            if str(payment_status_id) == "18":
                aaef_transactions.append(build_transaction_aaef(invoice))

        # 6. Calcular summary.
        total_invoices = len(aaef_invoices)
        total_transactions = len(aaef_transactions)
        total_documents = total_invoices + total_transactions

        total_gross_amount = Decimal("0.00")
        total_taxes = Decimal("0.00")
        total_net = Decimal("0.00")

        for invoice in invoices:
            api_response = getattr(invoice, "api_response", None) or {}
            bill = get_nested_value(api_response, ["data", "bill"], {}) or {}

            gross_value = (
                bill.get("gross_value")
                or bill.get("total")
                or getattr(invoice, "amount_to_pay", 0)
                or 0
            )

            tax_amount = (
                bill.get("tax_amount")
                or getattr(invoice, "total_taxes", 0)
                or 0
            )

            amount_to_pay = getattr(invoice, "amount_to_pay", 0) or 0

            total_gross_amount += to_decimal(gross_value)
            total_taxes += to_decimal(tax_amount)
            total_net += to_decimal(amount_to_pay)

        # Se suman también las transacciones como eventos económicos independientes.
        for trx in aaef_transactions:
            total_gross_amount += to_decimal(trx.get("Amount"))
            total_net += to_decimal(trx.get("Amount"))

        now_utc = timezone.now().astimezone(pytz.UTC)

        exchange_id = "AF-{year}-{month:02d}-{seq:05d}".format(
            year=now_utc.year,
            month=now_utc.month,
            seq=int(time.time()) % 100000
        )

        aaef_payload = {
            "metadata": {
                "ExchangeId": exchange_id,
                "GeneratedAt": now_utc.isoformat().replace("+00:00", "Z"),
                "StandardVersion": "1.0",
                "RequestedPeriod": {
                    "From": since_period,
                    "To": until_period
                },
                "SourceSystem": {
                    "SystemId": "sigma-prod-01",
                    "SystemName": "Sigma",
                    "SystemNIT": "900123456",
                    "Environment": os.getenv("DJANGO_ENV", "production")
                },
                "GeneratedBy": "sigma-integration-service"
            },
            "summary": {
                "TotalDocuments": total_documents,
                "TotalInvoices": total_invoices,
                "TotalTransactions": total_transactions,
                "TotalGrossAmount": format_decimal(total_gross_amount),
                "TotalTaxes": format_decimal(total_taxes),
                "TotalNet": format_decimal(total_net),
                "Currency": "COP"
            },
            "invoices": aaef_invoices,
            "transactions": aaef_transactions
        }

        return json_response(
            aaef_payload,
            200
        )

    except Exception as e:
        logger.error("[SIGMA_EVENTS] Error construyendo lote AAEF: %s", e, exc_info=True)

        return json_response({
            "success": False,
            "message": "Error interno al consultar eventos económicos de SIGMA.",
            "detail": str(e)
        }, 500)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    GET /health/

    Endpoint simple para validar que la API está funcionando.
    No requiere autenticación.
    """
    return HttpResponse(
        json.dumps({
            "status": "ok",
            "message": "API funcionando correctamente"
        }, ensure_ascii=False),
        content_type="application/json",
        status=200
    )    