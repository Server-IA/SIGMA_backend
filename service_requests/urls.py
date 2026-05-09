from .api.invoice_viewset import health_check
from django.urls import path, include
from rest_framework import routers
from service_requests.api.customer_viewset import CustomerViewSet
from service_requests.api.invoice_viewset import InvoiceViewSet
from service_requests.api.invoice_lines_viewset import InvoiceLineViewSet
from service_requests.api.invoice_issuer_viewset import InvoiceIssuerViewSet
from service_requests.api.person_type_viewset import PersonTypeViewSet
from service_requests.api.service_viewset import ServiceViewSet
from service_requests.api.tax_regime_viewset import TaxRegimeViewSet
from service_requests.api.service_request_viewset import ServiceRequestViewSet
from service_requests.api.payment_method_viewset import PaymentMethodViewSet
from service_requests.api.soil_type_viewset import SoilTypeViewSet
from service_requests.api.texture_viewset import TextureViewSet
from service_requests.api.implementation_viewset import ImplementationViewSet
from .api.invoice_viewset import download_invoice_pdf, consult_sigma_economic_events

router = routers.DefaultRouter()

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'person_types', PersonTypeViewSet, basename='person_type')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'tax_regimes', TaxRegimeViewSet, basename='tax_regime')
router.register(r'service_requests', ServiceRequestViewSet, basename='service_request')
router.register(r'payment_methods', PaymentMethodViewSet, basename='payment_method')
router.register(r'soil_types', SoilTypeViewSet, basename='soil_type')
router.register(r'textures', TextureViewSet, basename='texture')
router.register(r'implementations', ImplementationViewSet, basename='implementation')

router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-lines', InvoiceLineViewSet, basename='invoice_line')
router.register(r'invoice-issuers', InvoiceIssuerViewSet, basename='invoice_issuer')


urlpatterns = [
    # Health check - Validación simple de disponibilidad de la API
    path(
        'health',
        health_check,
        name='health-check'
    ),

    path('', include(router.urls)),

    path(
        'invoices/<int:id_invoice>/download_pdf/',
        download_invoice_pdf,
        name='invoice-download-pdf'
    ),

    # Alias para compatibilidad con URL anterior
    path(
        'invoices/<int:id_invoice>/download_fe_document/',
        download_invoice_pdf,
        name='invoice-download-fe-document'
    ),

    # RF-INT-15 - Obtención de eventos económicos de SIGMA por rango
    path(
        'sigma/economic-events/consult/<str:sincePeriod>/<str:untilPeriod>',
        consult_sigma_economic_events,
        name='sigma-economic-events-consult'
    ),
]