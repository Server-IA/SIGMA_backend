from django.urls import path, include
from rest_framework import routers
from service_requests.api.customer_viewset import CustomerViewSet
from service_requests.api.person_type_viewset import PersonTypeViewSet
from service_requests.api.service_viewset import ServiceViewSet
from service_requests.api.tax_regime_viewset import TaxRegimeViewSet

router = routers.DefaultRouter()

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'person_types', PersonTypeViewSet, basename='person_type')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'tax_regimes', TaxRegimeViewSet, basename='tax_regime')

urlpatterns = [
    path('', include(router.urls))
]